# 案例实战：从 SoC 上电冷启动到 Linux 用户态 Shell 全景推演

## 1. 冷启动端到端全景时序泳道图

从按下电源键到串口输出 `root@soc-host:~#`，系统跨越 6 大特权级与执行环境：

```mermaid
sequenceDiagram
    participant PMIC as PMIC / 硬件供电
    participant ROM as BootROM (EL3)
    participant SPL as SPL / FSBL (SRAM)
    participant TFA as TF-A BL31 (EL3)
    participant UBoot as U-Boot (EL2)
    participant Kernel as Linux Kernel (EL1)
    participant Init as Systemd / Shell (EL0)

    PMIC->>ROM: 1. 各供电轨稳定, Power-Good 触发释放 CPU 0 复位
    ROM->>SPL: 2. 读取 eFuse 校验 SPL 签名, 搬运至 iSRAM 并跳转
    Note over SPL: 3. 初始化 DDR PLL, 执行 PHY Training (Eye Scan)
    SPL->>TFA: 4. 验签并加载 TF-A 与 U-Boot 到 DDR
    TFA->>UBoot: 5. 初始化 PSCI, ERET 降权交接至 Non-secure EL2
    Note over UBoot: 6. U-Boot 重定位到 RAM 顶端, 扫描存储介质
    UBoot->>Kernel: 7. 加载 Image 与 DTB, 标准 ABI 传参 (x0=DTB_PA) 跳转
    Note over Kernel: 8. head.S 开启 MMU, setup_arch() 解析 DTB, 初始化调度器与驱动
    Kernel->>Init: 9. 挂载根文件系统 (EXT4), 降权派生 EL0 init 进程
    Init-->>Init: 10. 启动 systemd/busybox, 在 /dev/ttyS0 打印 Shell 提示符!
```

---

## 2. 关键各阶段状态机与数据流排查断点

| 执行阶段 | 运行空间与特权级 | 核心硬件依赖 | 典型挂死断点与定位方法 |
| :--- | :--- | :--- | :--- |
| **Phase 1: BootROM** | 片上只读 ROM (EL3) | 24MHz 晶振, PMIC 供电, eFuse | 串口完全无输出。读取 AON Scratch 寄存器中的错误码，测量晶振是否起振 |
| **Phase 2: SPL** | 片内 SRAM (Secure EL1) | 内部 SRAM, 存储控制器 (eMMC/SPI) | 打印 SPL 标志后挂死。检查 DDR Training 是否在特定 Byte Lane 失败 |
| **Phase 3: TF-A** | DDR 预留内存 (EL3) | DDR 物理内存可用, GIC 安全配置 | 切换安全世界时崩溃。排查 `SCR_EL3` 安全位与 PSCI 栈空间 |
| **Phase 4: U-Boot** | DDR 顶端区域 (EL2) | 全总线可用, 存储与网络外设 | 重定位后断流。排查 `.rela.dyn` 动态重定位修复与设备树传递 |
| **Phase 5: Kernel** | DDR 低端区域 (EL1) | MMU 页表, GIC PPI/SPI, Arch Timer | 停在 `Starting kernel ...` 或 `Calibrating delay`。开启 `earlycon` |
| **Phase 6: Shell** | 用户态进程空间 (EL0) | 根文件系统块设备, TTY 控制台 | `Attempted to kill init!`。检查 RootFS 架构匹配与动态链接库 |
