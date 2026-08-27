# SoC 的定义、组成与分类

## 1. 什么是 SoC

SoC（System on Chip，片上系统）是在一颗芯片中集成计算、存储、通信、控制和专用加速能力的完整系统。它通常不仅包含 CPU，还包含片上存储、外部存储控制器、总线或 NoC、外设控制器、中断控制器、时钟/复位/电源管理、安全模块以及调试基础设施。

“System”是理解 SoC 的关键：单独看每个 IP 都可能工作正常，但系统是否正确，还取决于地址是否可达、时钟是否有效、复位是否释放、电源域是否开启、访问权限是否允许、内存属性是否一致以及软件初始化顺序是否正确。

## 2. SoC 与相近概念

| 概念 | 典型含义 | 主要特征 |
| --- | --- | --- |
| CPU | 中央处理器核或处理器集群 | 执行通用指令，本身未必构成完整系统 |
| MPU | Microprocessor Unit | 通常需要外部 DRAM 和较完整 OS，常带 MMU |
| MCU | Microcontroller Unit | CPU、Flash、SRAM、定时器和外设高度集成，强调实时和低功耗 |
| SoC | System on Chip | 面向特定系统集成多类计算、存储、I/O 和管理模块 |
| ASIC | 专用集成电路 | 按特定需求固化实现；SoC 通常属于复杂 ASIC |
| FPGA | 可编程逻辑器件 | 逻辑可重配置，也可能包含硬核 CPU 并形成可编程 SoC |
| SiP | System in Package | 多颗裸片或器件封装在同一封装内，不等同于单片 SoC |
| Chiplet | 小芯粒 | 把大型系统拆成多个 Die，通过 Die-to-Die 接口互联 |

边界并不绝对。例如高端 MCU 也可能带 Cache、MPU、外部 DDR 控制器；应用处理器则常被直接称为 SoC。

## 3. 七类基本组成

### 3.1 计算子系统

- 通用 CPU：运行 Bootloader、OS、驱动和应用。
- 实时 CPU/MCU：承担低延迟控制、系统管理或安全任务。
- GPU：图形渲染及通用并行计算。
- NPU/AI Accelerator：矩阵、卷积和张量运算。
- DSP：音频、通信和信号处理。
- 视频/图像单元：ISP、Codec、Display Controller。

阅读架构资料时，需要记录每类处理器的指令集、核数、Cache、是否参与硬件一致性、可访问的地址范围以及启动责任。

### 3.2 存储子系统

- BootROM：固化第一阶段启动代码。
- OTP/eFuse：保存生命周期、安全配置、芯片校准值或密钥材料。
- SRAM：低延迟片上存储，可能作为启动 RAM、共享 RAM 或 TCM。
- Cache：减少处理器访问下一级存储的平均延迟。
- DDR Controller：调度来自片上主设备的内存请求。
- DDR PHY：处理训练、采样、电气时序和外部 DDR 信号。
- Flash/eMMC/UFS Controller：连接非易失启动及大容量存储。

### 3.3 互联子系统

- APB/AHB/AXI 等 AMBA 总线。
- Crossbar 或分层 Bus Matrix。
- NoC Router、Network Interface 和链路。
- 协议桥、位宽转换器、时钟域跨越单元。
- 地址译码、仲裁、QoS、访问过滤及超时监控。

互联不只是“连线”。它决定哪些主设备能访问哪些目标、访问顺序如何保证、拥塞如何传播、错误怎样返回，以及多个设备争用 DDR 时谁优先。

### 3.4 I/O 子系统

- 低速控制类：GPIO、UART、SPI、I2C、PWM、ADC。
- 存储类：SD/eMMC、NAND、NOR、UFS。
- 高速通信类：USB、PCIe、Ethernet、CAN、MIPI。
- 控制器通常负责协议逻辑，PHY 负责模拟/高速电气接口。

一个外设可用通常至少依赖 Pinmux、Clock、Reset、Power、MMIO、IRQ 和 DMA 中的若干项。

### 3.5 系统控制子系统

- Interrupt Controller：汇聚、屏蔽、路由和仲裁中断。
- Timer/Watchdog：计时、调度、超时恢复。
- Clock Controller：选择时钟源、分频、门控。
- Reset Controller：生成、同步和分发复位。
- Power Management Unit：控制电源域、隔离、保持和唤醒。
- System Controller：芯片模式、Boot Strap、引脚复用、生命周期状态。

### 3.6 安全与可靠性子系统

- Root of Trust、Secure Boot、加解密引擎。
- TrustZone/PMP/Firewall/IOMMU 等隔离机制。
- TRNG、密钥存储、Debug Authentication。
- ECC、Parity、错误记录、故障注入和 RAS。

### 3.7 调试与可观测性子系统

- JTAG/SWD、Debug Port、Cross Trigger。
- 指令/数据 Trace、片上 Trace Buffer。
- Performance Monitor Unit。
- NoC/DDR 带宽计数器和错误监视器。
- Crash 寄存器、Reset Cause、Always-on 日志区。

架构阶段若没有设计可观测性，量产后的偶发问题会非常难定位。

## 4. IP、Subsystem 与顶层 SoC

IP 是可复用的功能模块，例如 UART Controller；Subsystem 是多个 IP 和局部互联形成的功能集合，例如包含 CPU、L2 Cache、GIC 接口和调试单元的 CPU Subsystem；顶层 SoC 负责连接各 Subsystem，并定义全局地址、时钟、复位、电源、安全和中断规则。

典型层级如下：

```text
SoC Top
├── Application Processor Subsystem
│   ├── CPU Cluster
│   ├── Shared Cache
│   └── Local Interrupt/Debug
├── Memory Subsystem
│   ├── DDR Controller
│   └── DDR PHY
├── High-speed I/O Subsystem
│   ├── PCIe Controller
│   ├── USB Controller
│   └── Shared PHY/PLL
├── Peripheral Subsystem
│   ├── APB Bridge
│   ├── UART/SPI/I2C/GPIO
│   └── DMA
└── Always-on Subsystem
    ├── PMU
    ├── RTC/Watchdog
    └── Boot/Reset Controller
```

## 5. 硬件视角与软件视角

硬件工程师关注端口、协议、时序、时钟域、复位域、综合约束和状态机；软件工程师看到的是地址、寄存器、中断号、Clock ID、Reset ID、Power Domain ID 和驱动接口。两者通过以下“软硬件契约”连接：

- Register Specification：寄存器偏移、字段、复位值和访问副作用。
- Address Map：每个目标的地址窗口及安全属性。
- Interrupt Map：中断源、编号、触发类型和路由能力。
- Clock/Reset/Power Binding：依赖关系及启停顺序。
- Memory Map/Boot Contract：镜像位置、入口、保留区和传参方式。
- Coherency Contract：设备是否一致、DMA 地址宽度及 Cache 维护责任。

## 6. 常见 SoC 分类

### 6.1 应用处理器 SoC

强调多核 CPU、GPU/NPU、大容量 DDR、高速 I/O 和 Linux/Android 等复杂 OS，通常具备 MMU、硬件 Cache 一致性及多电源域。

### 6.2 实时控制 SoC

强调确定性、快速中断、TCM、锁步核、功能安全和丰富工业接口，可能运行 RTOS 或裸机程序。

### 6.3 异构 SoC

同时包含应用核、实时核和多个加速器。主要难点是资源所有权、跨核通信、共享内存一致性、启动顺序和故障隔离。

### 6.4 FPGA SoC

硬核处理系统与可编程逻辑互联。设计者还需处理逻辑侧地址窗口、AXI 端口、比特流加载、中断聚合和时钟约束。

## 7. 评价一颗 SoC 的维度

- 功能：计算单元、接口和编解码能力是否满足需求。
- 性能：算力、延迟、内存带宽、互联拥塞和实时性。
- 功耗：静态功耗、动态功耗、DVFS、休眠状态和唤醒成本。
- 面积与成本：Die 面积、封装、外部器件和 PCB 复杂度。
- 安全：启动链、隔离、密钥、调试权限和升级机制。
- 可靠性：ECC、故障恢复、温度范围、寿命和安全等级。
- 软件生态：工具链、BSP、驱动、上游支持和文档质量。
- 可调试性：日志、Trace、计数器和故障寄存器是否充分。

## 8. 初学者常见误区

1. **把 SoC 等同于 CPU。** CPU 只负责执行指令，许多系统问题来自互联、DDR、时钟或外设。
2. **认为地址表只是软件信息。** 地址范围实际上对应互联中的译码和路由规则。
3. **认为寄存器能读写就表示模块正常。** 配置通路可用不代表数据通路、PHY 或 DMA 已工作。
4. **认为关闭 Clock 等同于下电。** Clock Gate、Power Gate 和 Reset 是不同控制维度。
5. **忽略访问发起者。** CPU 能访问某区域，不表示 DMA、GPU 或安全核也能访问。
6. **忽略复位后的默认状态。** 安全墙、Pinmux、Clock Gate 和中断屏蔽往往默认关闭功能。
