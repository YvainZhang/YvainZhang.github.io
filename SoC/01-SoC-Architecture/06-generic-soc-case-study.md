# 通用教学 SoC 端到端案例

本案例虚构一颗 `Atlas-A1` SoC，用于练习综合阅读。所有地址、编号和参数仅服务于教学。

## 1. 需求背景

`Atlas-A1` 面向边缘网关，要求运行 64 位 Linux，同时由实时核处理控制任务。它需要千兆 Ethernet、PCIe、USB、eMMC、低速外设和 4 GiB DDR，支持安全启动与基础低功耗。

## 2. 顶层结构

```text
                         +----------------------+
                         | Application Cluster  |
                         | 4×64-bit CPU + L2    |
                         +----------+-----------+
                                    | Coherent
                         +----------v-----------+
                         |    Coherent NoC      |
        +----------------+----+-----------+-----+----------------+
        |                     |           |                      |
+-------v-------+   +---------v---+  +----v-------+      +-------v------+
| System Cache |   | PCIe/USB/ETH|  | AXI-to-APB |      | SMMU/Firewall|
+-------+-------+   | DMA Masters |  +----+-------+      +--------------+
        |           +-------------+       |
+-------v-------+                    UART/SPI/I2C/GPIO
| DDR Controller|
+-------+-------+
        |
+-------v-------+       +----------------+     +-----------------+
| DDR PHY/4 GiB|       | RT Subsystem   |     | Always-on/PMU   |
+---------------+       | 2×RT Core+SRAM |     | RTC/WDT/BootCtl |
                        +----------------+     +-----------------+
```

为简化图形，BootROM、eMMC、GIC、Debug 和安全模块未全部画出。

## 3. 关键配置

### 3.1 计算与一致性

- 4 个应用 CPU 共享 L2，参与 Coherent NoC。
- 2 个实时核拥有 512 KiB TCM，通过非一致 AXI 端口访问 DDR。
- Ethernet DMA 支持 I/O Coherency；中央 DMA 不支持一致性。
- PCIe 和 USB 位于 SMMU 后。

“支持 I/O Coherency”仍需确认具体端口、事务属性、页表 Shareability 和系统配置是否正确，不能只凭 IP 数据手册判断整芯片行为。

### 3.2 教学地址表

| 区域 | Base | Size | 说明 |
| --- | ---: | ---: | --- |
| BootROM | `0x0000_0000` | 256 KiB | 复位取指 |
| AON SRAM | `0x0010_0000` | 256 KiB | 早期栈和恢复代码 |
| RT TCM Alias | `0x0100_0000` | 1 MiB | 应用核访问实时核 TCM 的窗口 |
| System Control | `0x1000_0000` | 1 MiB | CRU/PMU/Pinmux/BootCtl |
| APB Peripheral | `0x1100_0000` | 16 MiB | UART/SPI/I2C/GPIO/Timer |
| GIC | `0x1200_0000` | 4 MiB | 中断控制器 |
| High-speed I/O | `0x2000_0000` | 256 MiB | USB/Ethernet/PCIe 控制寄存器 |
| PCIe Aperture | `0x3000_0000` | 256 MiB | PCIe 出站 MMIO |
| DDR Low | `0x4000_0000` | 2 GiB | DDR 的低 2 GiB |
| DDR High | `0x1_0000_0000` | 2 GiB | DDR 的高 2 GiB |

### 3.3 Clock Tree

```text
24 MHz Crystal
├── AON Clock（分频得到 32 kHz/24 MHz 域）
├── CPU PLL → CPU Mux/Divider → Application Cluster
├── SYS PLL → NoC/APB/Peripheral Divider
└── DDR PLL → DDR Controller/PHY
```

Ethernet PHY 使用独立 125 MHz Reference Clock；UART Core Clock 来自 SYS PLL 分频。

### 3.4 Power Domain

- `PD_AON`：不可由软件关闭。
- `PD_CPU`：支持核级 Clock Gate 和 Cluster Retention。
- `PD_DDR`：正常运行期间保持，深度睡眠可进入 Self-refresh。
- `PD_HSIO`：PCIe/USB/Ethernet 共享，内部还有 PHY 子域。
- `PD_PERI`：低速外设。
- `PD_RT`：实时域，可在应用核复位时保持运行。

## 4. 冷启动推演

### 4.1 POR 到 BootROM

1. PMU 位于 `PD_AON`，等待主电源和 24 MHz 晶振稳定。
2. Reset Controller 保持 CPU、NoC、DDR 和外设复位。
3. PMU 给 CPU/NoC 上电，打开安全低频 Clock。
4. 解除 CPU Reset，CPU 从 `0x0000_0000` 取指。
5. BootROM 读取 Strap 与 eFuse，确定从 eMMC 启动并启用安全验证。

此阶段栈使用 AON SRAM，DDR 尚不可访问。

### 4.2 BootROM 到 SPL

1. BootROM 打开 eMMC Controller 的 Power、Clock 和 Reset。
2. 配置 Pinmux 和基础传输模式。
3. 从固定启动分区读取 SPL 到 AON SRAM。
4. 验证镜像签名、版本和长度。
5. 跳转 SPL 入口。

### 4.3 SPL 初始化 DDR

1. 让 DDR Controller/PHY 保持 Reset。
2. 配置 DDR PLL 并等待 Lock。
3. 设置 Controller 时序、地址映射和 Refresh 参数。
4. 依次解除 PHY/Controller Reset。
5. 执行 Write Leveling、Read Gate、Read/Write Eye 等训练。
6. 检查训练结果并执行小范围内存测试。
7. 初始化 ECC 状态或 Scrub 所需内存。

训练失败时，应保存频点、电压、温度、具体 Lane/Rank 和失败阶段，而不只输出“DDR init failed”。

### 4.4 加载下一阶段

SPL 将可信固件、Bootloader、设备树和可选安全 OS 加载到 DDR，建立保留区域，随后移交控制。Bootloader 最终加载 Kernel，传递 DTB 地址和启动参数。

## 5. Linux 启动后访问 UART0

已知：

- UART0 Base：`0x1100_0000`。
- IRQ：GIC SPI 40，Level-high。
- Clock：`BUS_UART0` 和 `CORE_UART0`。
- Reset：`RESET_UART0`。
- Power：`PD_PERI`。

驱动 Probe 的概念流程：

1. Device Tree 匹配 `compatible`。
2. 内核将 UART0 PA 映射到 Kernel VA，并使用 Device 类型。
3. Runtime PM 请求 `PD_PERI` 上电。
4. Clock Framework 使能 Bus/Core Clock，并设置所需频率。
5. Reset Framework 解除 Reset。
6. 驱动读取 ID/Version，确认 MMIO 通路。
7. 根据实际 Core Clock 计算 Baud Divider。
8. 配置 FIFO、帧格式和中断。
9. 注册 IRQ Handler 和 TTY Port。

发送一个字符时，CPU 写 TX FIFO。此处没有 UART DMA，数据通路经过 CPU 的 MMIO Store、NoC、APB Bridge 和 UART Register/FIFO，而不是 DDR 数据通路。

## 6. Ethernet RX 推演

### 6.1 初始化

1. `PD_HSIO` 上电，打开 MAC Bus/Core Clock 和 125 MHz PHY Ref Clock。
2. 解除 MAC、DMA、PHY Reset，配置 Pinmux/MDIO。
3. 通过 MDIO 识别外部 PHY 并等待 Link。
4. Linux 分配 RX Descriptor 和 Buffer，获得 DMA 地址。
5. 配置 Ring Base、长度、MAC 地址和 Interrupt Coalescing。
6. 通过 Barrier 保证 Descriptor 对设备可见，再设置 DMA Enable。

### 6.2 收包

1. PHY 解码信号并把帧交给 MAC。
2. MAC 校验帧并把 Payload 推入 RX FIFO。
3. DMA 读取 Descriptor，得到目标 Buffer 地址。
4. DMA 以 Coherent 属性经 NoC 写入 DDR/Cache 一致性域。
5. DMA 更新 Descriptor 的 Length/Status/Ownership。
6. 达到中断合并阈值后，MAC 拉高中断。
7. GIC 将 SPI 路由到指定 CPU。
8. 驱动在 ISR 中屏蔽队列中断并调度轮询。
9. 网络轮询代码消费已完成 Descriptor，交给协议栈并补充 Buffer。

### 6.3 故障一：IRQ 增长但无有效数据包

IRQ 数量增长只能证明某类事件不断到达 CPU，不能证明 RX 数据路径完成。先读取 MAC 的 Raw Status。如果增长的是 Link Change 或 RX Error，问题仍在 PHY、帧校验或过滤；只有 RX Complete 才值得继续检查 Ring。

接着比较硬件 Current Descriptor、软件 Consumer Index 和 Descriptor Ownership。硬件指针没有移动，说明 DMA 未取得有效描述符；硬件指针移动而 Ownership 未回到 CPU，说明事务可能在途中失败。此时查看 SMMU Fault 和 NoC Error：Translation Fault 会给出失败 IOVA，Permission Fault 表明页表存在但权限不符。两者都没有，再直接检查 DDR 目标地址是否出现预期写入。

如果 DDR 内容已经更新，而 CPU 读到的 Descriptor 不变，故障落在一致性属性或软件同步。`Atlas-A1` 的 Ethernet 端口声称支持 I/O Coherency，但仍须验证该端口确实以 Coherent 属性发出事务，页表 Shareability 正确，而且驱动没有绕过 DMA API。Descriptor 已更新、Payload 仍异常时，最后核对 Buffer 长度、对齐、Headroom 和 MAC 是否把 CRC 写入内存。

### 6.4 故障二：大流量时丢包

先根据 MAC 统计区分线侧丢包和内存侧丢包。CRC、Alignment 或 PHY Error 增长，问题发生在链路；RX FIFO Overflow 增长，说明帧已被 MAC 接收，但 DMA 来不及排空 FIFO；Ring Empty 增长，则是软件补充 Buffer 太慢。

若 FIFO Overflow 与 DDR 高负载同步出现，读取 NoC 和 DDR 的端口利用率、平均延迟及 QoS 仲裁结果。带宽未满但延迟很高，可能是短 Burst、随机访问或高优先级 Master 长时间占用；带宽接近上限，则要从内存布局、Burst、队列深度或业务带宽预算解决。若硬件队列正常而 Ring Empty，继续观察中断合并、网络轮询预算、CPU Affinity、Cache Miss 和内存分配位置。

还要把频率记录在故障时间线上。Thermal Controller 可能同时降低 CPU、NoC 和 DDR 频率，使丢包只在升温后出现。单独提高 CPU 频率只有在软件补包或协议栈成为瓶颈时才有效，对受限于 RX FIFO、NoC 或 DDR 的场景没有帮助。

## 7. 实时核共享内存通信

应用核和实时核通过 DDR 中的 1 MiB 共享内存及 Mailbox 中断通信。实时核端口非一致，因此协议必须明确：

- Buffer 和控制结构的地址视图。
- Producer/Consumer 所有权。
- Cache Clean/Invalidate 责任。
- 写数据、更新 Producer Index、触发 Mailbox 的顺序。
- Ring Wrap 和错误恢复。
- 一方复位时如何重新同步 Generation ID。

一个推荐的消息发布顺序是：生产者写 Payload，执行所需 Cache 维护与写屏障，更新 Descriptor/Index，再触发 Mailbox；消费者收到通知后执行读屏障和 Cache 同步，再读取 Descriptor 与 Payload。实际指令和 API 取决于两侧架构及软件环境。

## 8. Suspend/Resume 推演

### 8.1 Suspend

1. 用户任务冻结，设备驱动停止新 I/O。
2. Ethernet/USB/PCIe 保存状态，根据唤醒需求配置 Wake Source。
3. 排空 DMA 和 NoC 事务，关闭非唤醒中断。
4. `PD_HSIO` 隔离并下电。
5. DDR 进入 Self-refresh。
6. CPU 上下文保存至 Retention SRAM，Cluster 下电。
7. AON 域保持 RTC、PMU 和 Wakeup Controller。

### 8.2 Resume

1. Wake Source 触发 AON PMU。
2. 恢复主电压和晶振/PLL。
3. DDR 退出 Self-refresh并确认数据有效。
4. CPU Domain 上电，从 Resume Vector 运行。
5. 恢复 NoC、GIC、Timer 和设备 Power Domain。
6. 驱动恢复 Clock/Reset/寄存器/PHY 状态。
7. 清除 Wake Status，恢复普通中断和任务。

### 8.3 Resume 后 UART 无输出

可能原因包括：UART Core Clock Parent 恢复错误、Divider 未按新频率重算、`PD_PERI` 上电但 Isolation 未解除、Pinmux 上下文丢失，或 UART 的 Reset Scope 与驱动预期不一致。

## 9. 案例结论

同一颗 SoC 中不存在一条万能访问路径：

- CPU 普通内存访问走 Cache/一致性 NoC。
- CPU MMIO 访问经过 Device Mapping 和外设 Bridge。
- Ethernet 数据走设备 DMA 路径。
- 实时核共享内存走非一致路径。
- 中断走独立控制路径，但其状态清除又依赖 MMIO。
- 所有路径都建立在正确的 Clock、Reset、Power 和安全配置之上。
