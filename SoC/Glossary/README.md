# 术语表

| 缩写 | 英文 | 含义 |
| --- | --- | --- |
| ABI | Application Binary Interface | 调用约定、寄存器使用和二进制接口规则 |
| AMBA | Advanced Microcontroller Bus Architecture | ARM 定义的 APB/AHB/AXI 等互联协议族 |
| ASID | Address Space Identifier | 标记进程地址空间的 TLB 标签 |
| CDC | Clock Domain Crossing | 不同时钟域之间的信号或事务跨越 |
| Coherency | Cache Coherency | 多个观察者对同一 Cache Line 副本的协调机制 |
| DMA | Direct Memory Access | 设备或引擎不经 CPU 逐字节参与的内存搬运 |
| DVFS | Dynamic Voltage and Frequency Scaling | 动态调整电压与频率 |
| ECC | Error Correcting Code | 检测和纠正存储位错误的编码 |
| GIC | Generic Interrupt Controller | ARM 通用中断控制器 |
| IOMMU | I/O Memory Management Unit | 为设备执行地址转换与访问隔离 |
| IOVA | I/O Virtual Address | 设备在 IOMMU 一侧使用的地址 |
| IPA | Intermediate Physical Address | 虚拟化 Stage-1 与 Stage-2 之间的地址 |
| ISA | Instruction Set Architecture | 指令、寄存器、异常和内存模型的软硬件契约 |
| ISR | Interrupt Service Routine | 中断服务程序 |
| IPC | Inter-Processor Communication | 处理器核心或异构处理器之间的数据交换、通知与同步机制 |
| AMP | Asymmetric Multiprocessing | 不同处理器运行独立 OS/固件并通过显式协议协作的系统形态 |
| MMIO | Memory-Mapped I/O | 通过地址空间中的 Load/Store 访问设备寄存器 |
| MMU | Memory Management Unit | CPU 虚拟地址转换和权限检查单元 |
| MPU | Memory Protection Unit | 以 Region 提供权限和属性、通常不转换地址的单元 |
| NoC | Network on Chip | 以路由和链路连接片上模块的互联网络 |
| OPP | Operating Performance Point | 合法频率与所需电压的组合 |
| PA | Physical Address | 处理器体系中的物理地址 |
| PHY | Physical Layer | 负责采样、串并转换、训练和电气接口的物理层 |
| PLIC | Platform-Level Interrupt Controller | RISC-V 平台级外部中断控制器 |
| PMU | Power Management Unit / Performance Monitoring Unit | 依语境指电源管理单元或性能监控单元 |
| PoC | Point of Coherency | 参与者对内存内容达成一致的体系结构点 |
| PoU | Point of Unification | 指令和数据访问统一观察内容的点 |
| QoS | Quality of Service | 互联中的带宽、优先级和延迟服务策略 |
| SMP | Symmetric Multiprocessing | 多个处理器共享同一 OS 和内存的一种组织方式 |
| SMMU | System Memory Management Unit | ARM 体系中的系统 IOMMU |
| TCM | Tightly Coupled Memory | 与处理器紧耦合、强调确定延迟的存储 |
| TLB | Translation Lookaside Buffer | 缓存地址转换和权限的结构 |
| VA | Virtual Address | CPU 指令直接使用的虚拟地址 |

Master/Slave 与 Initiator/Target 在不少资料中表达相同端口角色。本知识库优先使用 Initiator/Target，但引用具体协议字段时保留规范原名。

## 计算与虚拟化

| 缩写 | 英文 | 含义 |
| --- | --- | --- |
| EL | Exception Level | ARM AArch64 的特权级 EL0～EL3 |
| SBI | Supervisor Binary Interface | RISC-V S-mode 与 M-mode Runtime 的接口 |
| TF-A/ATF | Trusted Firmware-A | ARM Trusted Firmware，常提供 BL31/PSCI |
| OP-TEE | Open Portable Trusted Execution Environment | 常见 ARM Secure World TEE |
| PSCI | Power State Coordination Interface | OS 与 ARM Platform Firmware 的电源管理接口 |
| PASID | Process Address Space ID | PCIe 事务携带的进程地址空间标识 |
| VFIO | Virtual Function I/O | Linux 用户态安全设备直通框架 |

## 存储与一致性

| 缩写 | 英文 | 含义 |
| --- | --- | --- |
| MESI/MOESI | Cache coherence states | Cache Line 的稳定权限状态模型 |
| DDR | Double Data Rate SDRAM | 双沿传输的外部动态内存 |
| PRP | Physical Region Page | NVMe 描述数据页的指针形式 |
| SGL | Scatter-Gather List | 描述非连续内存段的列表 |
| UFS | Universal Flash Storage | 基于 M-PHY/UniPro 的嵌入式存储接口 |
| NVMe | Non-Volatile Memory Express | 基于 Queue 的 PCIe 非易失存储协议 |

## 互联

| 缩写 | 英文 | 含义 |
| --- | --- | --- |
| APB | Advanced Peripheral Bus | 面向低速寄存器访问的 AMBA 总线 |
| AHB | Advanced High-performance Bus | 地址数据流水的 AMBA 总线 |
| AXI | Advanced eXtensible Interface | 五通道、支持 Burst/Outstanding 的 AMBA 总线 |
| AXI-Stream | AXI Streaming Interface | 无地址、VALID/READY 的流式接口 |
| ACE | AXI Coherency Extensions | 在 AXI 上扩展一致性通道 |
| CHI | Coherent Hub Interface | ARM 可扩展一致性互联协议 |
| ITS | Interrupt Translation Service | GIC 中把设备 Event/MSI 翻译成 LPI 的单元 |
| LPI | Locality-specific Peripheral Interrupt | GICv3 面向大量消息中断的中断类型 |
| Mailbox | Hardware Mailbox | 在处理器或电源域之间传递事件和少量数据的硬件通知单元 |
| Doorbell | Doorbell Register | 通过寄存器写通知对端检查共享队列的机制 |
| SGI | Software Generated Interrupt | ARM GIC 体系中由软件触发的目标核核间中断 |
| IMSIC | Incoming MSI Controller | RISC-V AIA 体系中接收和路由消息中断/IPI 的控制器 |
| Vring | VirtIO Ring | VirtIO 使用的共享描述符环形队列 |
| RPMsg | Remote Processor Messaging | 基于 VirtIO/Vring 的异构处理器消息总线 |
| remoteproc | Remote Processor Framework | Linux 中负责辅核固件装载、启动、停止和崩溃恢复的框架 |
| OpenAMP | Open Asymmetric Multi-Processing | 面向异构多核系统的跨平台开源通信与生命周期框架 |
| UCIe | Universal Chiplet Interconnect Express | 开放式 Chiplet 芯粒间高带宽低延迟互联标准 |

## 时钟、电源与接口

| 缩写 | 英文 | 含义 |
| --- | --- | --- |
| PLL | Phase-Locked Loop | 从参考时钟产生目标频率和相位的锁相环 |
| PMIC | Power Management Integrated Circuit | 提供和排序芯片电源 Rail 的电源管理芯片 |
| CCF | Common Clock Framework | Linux 时钟 Provider/Consumer 框架 |
| SerDes | Serializer/Deserializer | 高速串并转换与物理链路单元 |
| MIPI CSI/DSI | Camera/Display Serial Interface | MIPI 摄像头输入与显示输出接口 |
| LTSSM | Link Training and Status State Machine | PCIe 链路训练和状态机 |
| MSI/MSI-X | Message Signaled Interrupt | 设备通过内存写产生的消息中断 |

## 调试与性能

| 缩写 | 英文 | 含义 |
| --- | --- | --- |
| DAP | Debug Access Port | CoreSight 外部调试访问入口 |
| ETM | Embedded Trace Macrocell | 处理器指令流 Trace Source |
| ETF/ETR | Trace FIFO / Trace Router | 片上缓冲或写 DDR 的 Trace Sink |
| CTI/CTM | Cross Trigger Interface/Matrix | 调试组件间跨触发网络 |
| TMAM | Top-down Microarchitecture Analysis Method | 按 Pipeline Slot 分类瓶颈的方法 |
| HITM | Hit Modified | 请求命中其他核 Modified Cache Line 的事件 |
