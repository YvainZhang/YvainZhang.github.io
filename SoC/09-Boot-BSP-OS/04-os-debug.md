# 操作系统引导全流程、挂死断点排查与 Panic 现场定位完全指南

## 1. Linux 内核早期启动关键里程碑时序图

Linux 从接收 U-Boot 控制权到最终生成第一个用户空间进程（PID 1: `/sbin/init`），经历以下 7 个关键执行阶段：

```mermaid
flowchart TD
    Kernel_Entry["1. 汇编入口: arch/arm64/kernel/head.S\n• 校验 CPU 运行模式 (EL2/EL1)\n• 创建早期临时恒等映射页表 (Identity Mapping)\n• 开启 MMU (SCTLR_EL1.M=1) 与 D-Cache, 跳转 start_kernel()"]

    Kernel_Entry --> Early_Console["2. earlycon 阶段: 直接通过 MMIO 物理地址写串口\n输出首行内核日志: Booting Linux on physical CPU 0x0000000000"]

    Early_Console --> Setup_Arch["3. setup_arch(): 解析 DTB 设备树\n• 初始化 memblock 早期物理内存分配器\n• 建立 early_ioremap() 映射机制"]

    Setup_Arch --> Paging_Init["4. paging_init(): 构建内核正式页表体系\n• 初始化 Buddy System (伙伴系统内存分配器) 与 SLUB\n• 释放早期引导内存 (Freeing unused kernel memory)"]

    Paging_Init --> Trap_IRQ["5. trap_init() & init_IRQ()\n• 设置 VBAR_EL1 异常向量表\n• 初始化 GIC 中断域与时钟定时器 (Arch Timer)"]

    Trap_IRQ --> Rest_Init["6. rest_init(): 孵化 PID 1 (kernel_init) 与 PID 2 (kthreadd)\n• 执行 do_initcalls() 遍历加载所有内置驱动 (Platform Driver Probe)\n• 控制台平滑切换至正式 TTY 驱动"]

    Rest_Init --> Mount_Root["7. 挂载根文件系统 (Mount RootFS) 并执行 /sbin/init\n• 降权进入 EL0 用户态, 移交 Shell 交互控制权"]
```

---

## 2. 启动挂死（Boot Hang）经典四大断点定位决策树

```mermaid
flowchart TD
    Hang_Point["系统启动挂死断点"] --> Branch{"挂死在哪个阶段?"}

    Branch -->|断点 1: 停在 Starting kernel ... 串口无声| Case1["1. 汇编早期挂死 (head.S / MMU 开启前)\n• U-Boot 传参寄存器 x0 包含非法 DTB 地址\n• earlycon 参数配错 (基地址/波特率不匹配)\n• 解决方法: 开启 CONFIG_DEBUG_LL 与 earlyprintk 逐行插桩"]

    Branch -->|断点 2: 停在 Calibrating delay loop ...| Case2["2. 架构定时器 (Arch Timer) 未工作\n• SoC 未向 CPU 提供通用定时器时钟源 (cntfrq_el0 未初始化)\n• GIC PPI 虚拟/物理定时器中断号配置错误\n• 解决方法: 检查 TF-A BL31 中 CNTFRQ_EL0 的时钟频率配置"]

    Branch -->|断点 3: 停在 Waiting for root device ...| Case3["3. 存储驱动未就绪或设备名不匹配\n• eMMC/NVMe 驱动编译成了模块 (.ko) 而未编入内核镜像\n• bootargs 中 root=/dev/mmcblk0p2 路径错误 (应改用 PARTUUID)\n• 解决方法: 在 bootargs 中加入 rootdelay=5 等待总线枚举"]

    Branch -->|断点 4: 触发 Kernel panic: Attempted to kill init!| Case4["4. 用户态环境缺失或 ABI 冲突\n• RootFS 缺少动态链接器 (/lib/ld-linux-aarch64.so.1)\n• 64 位内核尝试运行 32 位 RootFS 但未开启 CONFIG_COMPAT\n• /sbin/init 缺少执行权限 (chmod +x)"]
```

---

## 3. `earlycon` 与正式 TTY 驱动交接时的日志丢失排坑

- **微架构机制**：
  - `earlycon` 是一个极简的无中断轮询驱动，在内核启动前几毫秒通过 bootargs 参数直接操作 MMIO 寄存器（`earlycon=uart8250,mmio32,0x01c28000,115200`）；
  - 当内核执行到 `tty_init()` 并 probe 正式串口驱动（如 `8250_dw.c`）时，内核会注销 `earlycon` 并接管该串口硬件。
- **故障排查**：若配置参数（如引脚波特率分频系数、时钟源）在 DTS 与 earlycon 中不一致，串口在交接瞬间会被重新初始化并输出乱码，导致随后的全部崩溃日志丢失。确保 DTS 中的 `clocks` 属性与 bootargs 中的时钟频率绝对吻合。

---

## 4. RTOS（FreeRTOS / Zephyr）HardFault 故障排查手册

在微控制器与实时操作系统中，系统崩溃通常直接触发 **HardFault / UsageFault / MemManageFault**：

```c
/* FreeRTOS / ARM Cortex-M HardFault 堆栈反解汇编桩函数 */
void HardFault_Handler_C(uint32_t *hardfault_args)
{
    uint32_t r0  = hardfault_args[0];
    uint32_t r1  = hardfault_args[1];
    uint32_t r2  = hardfault_args[2];
    uint32_t r3  = hardfault_args[3];
    uint32_t r12 = hardfault_args[4];
    uint32_t lr  = hardfault_args[5]; /* 函数返回地址 */
    uint32_t pc  = hardfault_args[6]; /* 触发 Fault 的指令 PC */
    uint32_t psr = hardfault_args[7];

    /* 检查 CFSR 综合症寄存器 (Configurable Fault Status Register) */
    uint32_t cfsr = (*((volatile uint32_t *)(0xE000ED28)));

    /* 核心排查:
     * 1. 若 CFSR.STKOF == 1: 任务栈深度耗尽 (Stack Overflow)
     * 2. 若 CFSR.UNALIGNED == 1: 非对齐访问
     * 3. 若 CFSR.NOCP == 1: 在未开启 FPU 协处理器前执行了浮点运算指令
     */
}
```
