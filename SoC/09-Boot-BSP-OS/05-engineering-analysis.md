# 启动交接断点推演、A/B 分区抗掉电状态机与热复位数据踩踏深度分析

## 1. 串口日志丢失五大断点精确定界时序图

在 SoC 冷启动链路上，控制台日志（Console Log）是观察系统生命周期的唯一窗口。日志在某一步骤突然消失，标志着特定的软硬件初始化断层：

```mermaid
flowchart TD
    Chain["全链路日志断点排查"] --> B1

    subgraph Breakpoints ["五大日志丢失断点与根因定界"]
        B1["断点 1: BootROM 打印正常, SPL 无任何字符\n• 内部 SRAM 栈设置越界\n• SPL 时钟树未使能 UART 控制器门控 (PCLK/SCLK)"]

        B1 --> B2["断点 2: SPL 正常, U-Boot 在 Relocation 后突然断流\n• U-Boot 重定位基地址超出物理 RAM 顶端\n• 动态重定位表 (.rela.dyn) 未修正全局数据结构体 gd 指针"]

        B2 --> B3["断点 3: U-Boot 打印 Starting kernel ..., 内核 earlycon 无任何输出\n• U-Boot 传参 x0 包含非法 DTB 物理地址\n• bootargs 中 earlycon 参数基地址与 SoC 实际 UART 不匹配"]

        B3 --> B4["断点 4: earlycon 输出正常, 切换正式 TTY 瞬间卡死/乱码\n• DTS 中声明的时钟频率与 earlycon 硬编码频率不一致\n• pinctrl 驱动将 UART 引脚复用重设为了默认 GPIO 输入"]

        B4 --> B5["断点 5: 内核日志打印完毕 (Freeing memory), 无 Shell 提示符\n• RootFS 缺少 /dev/console 字符设备节点\n• /etc/inittab 或 systemd 未在该 ttyS0 实例化 getty 进程"]
    end
```

---

## 2. 设备树 `reg` 地址偏差引发的物理总线行为推演

假设某外设在 SoC 互联中的物理基地址为 `0x01C28000`，若 DTS 中因笔误写为 `0x01C29000`（偏移了 4KB），系统会发生何种行为？

```mermaid
flowchart LR
    Access["CPU 访问错误基地址: 0x01C29000"] --> Bus_Decode{"NoC / AXI 总线解码器匹配"}

    Bus_Decode -->|情况 A: 命中相邻外设寄存器窗口| Wrong_Reg["严重逻辑混乱: 误操作了相邻外设 (如修改了定时器或看门狗)"]
    Bus_Decode -->|情况 B: 命中片上未映射地址空洞 (Unmapped Hole)| DecErr["总线返回 DECERR: CPU 触发 Synchronous External Abort 崩溃"]
    Bus_Decode -->|情况 C: 命中安全受保护区域 (TrustZone Carveout)| SlvErr["TZC 防火墙阻断并返回 SLVERR / 产生安全入侵警报"]
```

- **驱动防范实践**：高质量驱动在 `probe()` 完成 `ioremap` 后的第一件事，**必须读取硬件的版本寄存器（`IP_VERSION`）或魔数 ID（`IP_MAGIC`）并做断言校验**。严禁仅凭 `ioremap` 返回非空即假定硬件正常。

---

## 3. A/B 双分区 OTA 升级防断电状态机推演

嵌入式系统在 OTA 升级过程中遭遇突然拔电，是导致设备“变砖”的高发原因。工业级系统采用基于元数据校验的双分区回滚机制：

```mermaid
stateDiagram-v2
    [*] --> Slot_A_Active: 当前系统在 Slot A 稳定运行

    Slot_A_Active --> Updating_B: OTA 守护进程将新镜像写入非活动的 Slot B

    Updating_B --> Verify_B: 写入完成: 计算并校验 SHA-256 哈希与 RSA 数字签名
    Updating_B --> Slot_A_Active: 写入中途断电 (Slot A 元数据未改变, 重启依然进入 Slot A)

    Verify_B --> Update_Metadata: 签名合法: 将 Slot B 标记为 Active 并重置 Tries_Left = 3 (写带 CRC 的元数据)

    Update_Metadata --> Reboot: 触发系统重启

    Reboot --> Booting_B: Bootloader 读取元数据, 尝试引导 Slot B (Tries_Left 递减为 2)

    Booting_B --> Health_OK: 进入 Slot B 用户态, 业务自检成功: 写入 Successful=1
    Booting_B --> Rollback_A: 启动失败/Watchdog 超时复位 (重试 3 次耗尽)

    Rollback_A --> Slot_A_Active: Bootloader 自动回滚激活 Slot A!
    Health_OK --> Slot_B_Active: 升级彻底完成 (此时方可烧写 Anti-rollback 熔丝)
```

---

## 4. 热复位（Warm Reset）残留 DMA 内存踩踏与防御

- **故障场景**：Linux 发生软件复位（`reboot`）或看门狗热复位。
- **微架构根因**：
  - CPU 核心和部分外设控制器被复位，**但外部 PCIe 网卡或自研高速 DMA 引擎可能未接收到硬件复位信号，仍保持运行态**；
  - 外部网卡继续向先前的 DDR 接收缓冲区执行 DMA 写入；
  - 此时新启动的 U-Boot 或 Linux 内核将该片物理内存重新分配给页表或内核堆栈；
  - **残留的 DMA 写入直接覆盖破坏了新内核的内存数据，导致随机、难以复现的启动崩溃**。
- **防御机制**：
  - 在 BootROM / SPL 早期执行阶段，根据复位原因寄存器（Reset Reason Register）判断是否为 Warm Reset；
  - 如果是热复位，**在使能 MMU 和初始化内存分配器之前，向总线控制器下发全局 Master 隔离命令（Isolation / Gate），强制复位所有片上 DMA 子系统并排空（Drain）互联总线**。
