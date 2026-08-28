---
layout: post
title: "ARM 处理器启动流程与引导架构"
subtitle: "从 BootROM、SPL/BL2、ATF/BL31 安全固件、U-Boot 到 Linux 内核启动"
date: 2022-01-09
redirect_from:
  - /2022/11/07/arm-boot-process/
  - /2022/07/31/arm-boot-process/
author: Yvain Zhang
header-img: "img/post-bg-unix-linux.jpg"
series: "技术"
tags:
  - 操作系统
  - ARM
  - Bootloader
  - U-Boot
  - 嵌入式
---

在嵌入式 Linux 系统开发中，从按下电源键到进入终端命令行，系统经历多级接力式引导。

当遇到板卡上电无输出、DDR 初始化失败、内核停在 `Starting kernel ...` 等启动故障时，需要理解 **BootROM -> SPL/BL2 -> ATF (BL31) -> U-Boot (BL33) -> Linux Kernel** 的时序与硬件状态切换。

本文梳理现代 ARM（包含 ARMv7-A 与 ARMv8-A 64位架构）处理器的引导流程与底层机制。

---

## 1. 启动时序全景图 (ARMv8-A Trusted Boot)

```mermaid
graph TD
    PowerOn[上电复位 Power-On Reset] --> BL1[BL1: SoC BootROM (片上只读 ROM, EL3)]
    BL1 -->|采样启动引脚, 加载 BL2 至片内 SRAM| BL2[BL2: SPL / 辅助引导 (EL3 或 S-EL1)]
    BL2 -->|初始化 DDR 内存控制器, 加载固件镜像| MemLoad[加载 BL31 / BL32 / BL33 至 DDR]
    BL2 -->|跳转至运行时安全固件| BL31[BL31: TF-A / ATF 运行时固件 (EL3)]
    BL31 -->|配置安全/非安全世界, 切至 Non-Secure EL2/EL1| BL33[BL33: U-Boot Proper (Non-Secure EL2/EL1)]
    BL33 -->|加载 Image + DTB 设备树, 直接跳转| Kernel[Linux Kernel (Non-Secure EL1/EL2)]
    Kernel --> Init[用户空间 PID 1 /sbin/init]
```

---

## 2. 各级引导阶段剖析

### 2.1 BL1: SoC BootROM (片上固化代码)
- **运行环境**：处理器上电后，硬件逻辑将程序计数器（PC）复位到 SoC 内部固化的只读存储区（BootROM）。此时外部 DDR 内存尚未初始化，仅能使用 SoC 片内 **SRAM（几 KB 到几十 KB）** 作为运行栈；
- **核心任务**：
  1. 读取硬件引脚（Boot Mode Pins / eFuse），判定启动介质（eMMC, SD卡, SPI Flash, USB 或串口）；
  2. 验证介质中第一阶段固件的安全签名（Secure Boot 验签）；
  3. 将第二阶段引导程序（BL2 / SPL）加载到片内 SRAM 中并跳转执行。

---

### 2.2 BL2: SPL (Secondary Program Loader)
- **为什么需要 SPL？**
  完整版的 U-Boot 体积通常有数百 KB 到数 MB，超出片内 SRAM 的容量限制，无法一次性加载。
- **核心任务**：
  1. **初始化外部 DDR 内存控制器**：配置 DDR 锁相环（PLL）、时钟频率、时序参数并执行硬件训练（DDR Training）；
  2. DDR 就绪后，BL2 将后续的固件镜像从存储介质加载到 DDR 内存中：
     - **BL31**：ARM Trusted Firmware (TF-A) 运行时固件；
     - **BL32**（可选）：安全操作系统（如 OP-TEE）；
     - **BL33**：非安全引导程序（U-Boot Proper）。
  3. BL2 完成加载后，将执行权移交给 BL31。

---

### 2.3 BL31: ARM Trusted Firmware (TF-A) 与异常等级管理

在 64 位 ARMv8-A 体系中，定义了四个特权异常等级（Exception Levels）：

```
+───────────────────────────────────────────────────────────+
| EL0: 用户空间 (User Space Application)                    |
+───────────────────────────────────────────────────────────+
| EL1: 操作系统内核 (Linux Kernel / Guest OS)               |
+───────────────────────────────────────────────────────────+
| EL2: 虚拟机监视器 (Hypervisor / KVM)                      |
+───────────────────────────────────────────────────────────+
| EL3: 安全监视器 (Secure Monitor / BL31 TF-A - 最高特权)   |
+───────────────────────────────────────────────────────────+
```

1. **初始化运行时环境**：BL31 驻留在 EL3，负责处理运行时的安全监控调用（SMC）以及电源管理接口（PSCI，如 CPU 热拔插、休眠唤醒）；
2. **切换至非安全世界**：BL31 配置系统的安全/非安全物理内存分区与外设访问权限后，执行 `ERET` 指令将 CPU 降权切换到 Non-Secure EL2（若支持虚拟化）或 Non-Secure EL1，并跳转到 BL33（U-Boot）入口。

---

### 2.4 BL33: U-Boot Proper
- **运行环境**：运行在 Non-Secure EL2 或 EL1 的 DDR 内存中；
- **核心任务**：
  1. 初始化串口（UART）、网卡、USB、存储控制器等外设；
  2. 解析存储介质的文件系统（FAT/EXT4）；
  3. 根据启动配置（`boot.scr` 或 `extlinux.conf`）将操作系统内核镜像（`Image` / `zImage`）、设备树二进制（`dtb`）和根文件系统（`initramfs`）加载至 DDR 指定物理地址；
  4. 设置启动参数（`bootargs`），直接跳转到内核入口（`booti` 或 `bootm`）。

---

### 2.5 Linux 内核初始化 (`start_kernel`)

内核获取执行权后，从汇编入口 `head.S` 开始执行，开启 MMU，随后进入跨架构的 C 语言入口 `init/main.c: start_kernel()`：

1. `setup_arch()`：解析设备树（Device Tree DTB），探测板级硬件信息；
2. `mm_init()`：初始化页表、伙伴系统与 Slab 分配器；
3. `trap_init()` 与 `init_IRQ()`：配置中断向量表与 GIC 中断控制器；
4. `rest_init()`：
   - 启动内核线程 `kthreadd`（PID 2），管理内核工作线程；
   - 创建首个用户态进程 `init`（PID 1），挂载根文件系统并启动系统服务。

---

## 3. 常见启动故障排查参考

| 故障现象 | 停滞阶段 | 常见排查方向 |
| :--- | :--- | :--- |
| 串口无任何输出，芯片无发热 | BootROM (BL1) | 检查供电时序（PMIC 电源轨）、晶振时钟、Boot Mode 跳线与 eFuse 配置。 |
| 打印前导字符后卡死 | SPL (BL2) | DDR 时序参数不匹配、DDR 训练失败、供电电压不稳定。 |
| U-Boot 提示找不到内核镜像 | U-Boot (BL33) | eMMC 分区损坏、`bootargs` 配置错误、存储控制器驱动异常。 |
| 停在 `Starting kernel ...` 之后无输出 | 内核交接/解压 | 串口波特率或 earlycon 配置不符、内核与 DTB 物理地址冲突、设备树兼容字符串（compatible）不匹配。 |

---

## 4. 总结

ARM 处理器的启动过程遵循分层加载与权限隔离：
- **BootROM (BL1)** 提供最基础的片上自举；
- **SPL (BL2)** 负责在片内 SRAM 阶段点亮 DDR 内存并搬运后续镜像；
- **TF-A (BL31)** 在 EL3 建立安全边界与 PSCI 运行时服务，并将 CPU 转入非安全状态；
- **U-Boot (BL33)** 负责外设驱动与多介质加载，最终引导 **Linux 内核**。
