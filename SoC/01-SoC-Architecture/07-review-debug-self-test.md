# 架构审阅、调试清单与自测

## 1. 新 SoC 资料收集清单

### 1.1 必要资料

- Datasheet：产品能力、封装、引脚、电气和工作条件。
- TRM：子系统结构、寄存器、启动、时钟和低功耗。
- CPU Architecture Reference Manual。
- Interconnect/NoC、GIC/PLIC、SMMU 等 IP 手册。
- Address Map、Interrupt Map、Clock/Reset ID 表。
- Register Specification。
- DDR 参数和板级原理图。
- Boot Flow、镜像格式和安全启动说明。
- Errata：已知硬件问题及规避方案。
- BSP Source、Device Tree、Bootloader 配置和构建说明。

不同文档版本可能互相冲突，应记录芯片 Revision、文档版本和发布日期，并优先使用与目标芯片匹配的勘误表。

## 2. SoC 顶层架构审阅

### 2.1 计算与存储

计算子系统的审阅结果应是一张资源表，而不是“4 核 ARM”这样的产品描述。每个执行单元要写明 ISA/扩展、核数、特权模型、局部存储、Cache 层级、最大频率和启动责任。Cache 的共享边界尤其重要：L1 通常每核私有，L2 可能每 Cluster 共享，System Cache 又可能被 CPU 和 I/O 共同使用。共享边界决定锁和原子操作的作用范围，也决定哪个层级可能发生容量争用和 False Sharing。

存储资源要写明容量、地址、访问延迟、ECC 和生命周期。BootROM 用于第一阶段可信代码；SRAM 常承担早期栈、低功耗恢复和跨核通信；TCM 追求确定性，通常不等同于普通 Cache；DDR 提供容量，却依赖 Controller、PHY 和训练。DDR 理论峰值可用“每秒传输次数 × 总线字节数 × 通道数”估算。例如单通道 32-bit DDR4-3200 的原始峰值为 `3200 MT/s × 4 B = 12.8 GB/s`。这个值未扣除 Refresh、命令间隙、读写切换和仲裁开销，不能直接当作应用带宽。

一致性信息按 Initiator 列出。CPU Cluster 通常天然参与一致性；GPU、NPU 和 I/O 设备是否参与，则取决于 SoC 把它们接到了哪类互联端口，以及事务属性如何配置。IP 宣称支持 ACE/CHI 并不能证明最终芯片启用了该能力。

### 2.2 互联与地址

这一部分最终要交付三张表：Initiator/Target 可达矩阵、按访问者划分的地址表、互联端口参数表。可达矩阵给出读写和安全权限；地址表揭示 CPU PA、DMA Address 与 Alias；端口表记录协议、数据宽度、Clock、Outstanding、QoS 和一致性属性。

位宽和 Clock 转换点往往是吞吐与死锁风险集中的地方。256-bit 高速 NoC 接入 32-bit APB 时，Bridge 必须拆分事务；异步 Bridge 则要在两个 Clock Domain 之间缓存请求和响应。若下游关闭 Clock，上游可能耗尽 Outstanding 槽位并拖住其他 Master。因此审阅不能止于“协议兼容”，还要确认背压上限、超时和错误隔离。

QoS 不能只记录一个 Priority 数字。还要写清仲裁算法、带宽保证、突发限制和优先级是否可被软件改变。例如显示扫描需要稳定的最小带宽，CPU 则更关心平均延迟；若只设置静态最高优先级，显示 Master 可能在高分辨率场景中长期压制 CPU。无效地址和无响应 Target 应落入 Default Error Target 或 Timeout Monitor，并把 Initiator ID、地址、事务类型保存到错误寄存器。

### 2.3 中断

Interrupt Map 应从设备源头写到 CPU：设备状态位、局部 Mask、聚合器输入、全局 IRQ 编号、触发类型、路由目标和安全分组缺一不可。电平中断在源未清除时保持 Assert，适合不会丢事件的状态通知；边沿中断表示瞬时变化，需要控制器锁存。硬件和 Device Tree 对触发类型理解不一致，会造成一次后不再触发或持续中断。

共享中断要求每个驱动读取自己的状态并只处理属于自己的事件；MSI/MSI-X 则由设备发起一次特殊内存写，问题可能位于设备配置、地址窗口、IOMMU 或中断控制器的消息接收单元，而不是物理中断线。

深度休眠时，普通中断控制器可能掉电。能够唤醒系统的源必须同时连接 Always-on Wakeup Controller，后者锁存原因并请求 PMU 上电。恢复代码先保存 Wake Status，再恢复主中断控制器，避免清状态的顺序把真正唤醒原因抹掉。安全中断应由硬件分组和路由限制到允许的异常级，普通世界不能仅通过改写目标 CPU 就取得安全事件。

### 2.4 Clock/Reset/Power

这里应产出一张依赖图和两条可执行时序：正常上电时序、带错误回退的下电时序。依赖图列出 Bus/Core/Reference/PHY Clock，各路 Reset，父子 Power Domain、Isolation 和 Retention。共享 Gate 或共享 Reset 要特别标记，因为一个驱动关闭“自己的”资源可能同时影响另一个仍在工作的模块。

每个状态转换都要有完成条件和超时。例如请求域上电后轮询 Power Good，启动 PLL 后等待 Lock，解除 Reset 后读取模块 Ready。若只有固定毫秒延时，电压、温度和芯片批次变化后就可能暴露竞态。失败回退还要避免在有 Outstanding 事务时直接关电。

Runtime PM 的前提是驱动知道怎样保存状态、停止 DMA、配置唤醒并恢复资源；DVFS 则要有合法 OPP 和 Regulator/Clock 的顺序约束。硬件若不能读取实际 Clock Gate、Reset 和 Power Acknowledge，软件日志中的“已使能”只能说明发出了命令，无法证明模块端状态已经改变。

### 2.5 安全与调试

安全审阅从不可变的信任根开始。要明确第一条被硬件信任的公钥哈希或密钥位于 ROM、OTP 还是安全元件，BootROM 验证哪个镜像，后续每一阶段又验证谁。只验证第一阶段而允许它无条件加载未签名 Kernel，并没有形成覆盖到运行环境的完整信任链。Anti-rollback 还需要单调版本存储和断电安全的更新协议。

Firewall 和 SMMU 的复位策略以默认拒绝为宜，再由可信固件开放必要窗口。策略表要包含 Initiator/Stream ID、地址、方向和安全属性。JTAG 权限则与芯片生命周期绑定：研发态可能完全开放，量产态要求 Challenge-response 认证，报废态永久关闭。切换生命周期通常不可逆，相关 Fuse 写入必须有双重确认和掉电保护。

错误处理要兼顾安全和可诊断性。ECC Syndrome、NoC Error 和安全违规应进入受保护的 Sticky 寄存器或日志 SRAM，并记录地址、Initiator 和时间；普通世界可以得到“访问失败”，但不应借错误日志读取安全地址布局或密钥相关信息。

## 3. BSP Bring-up 最小步骤

建议按依赖关系逐步扩大系统，不要一开始就同时启用全部模块：

1. 确认电源、晶振和 POR。
2. JTAG 连接并读取 CPU ID、PC 和 Reset Cause。
3. 在片上 SRAM 执行最小程序。
4. 配置一个稳定串口，验证 Clock/Reset/Pinmux/MMIO。
5. 初始化 Timer 和中断控制器。
6. 初始化 DDR，完成不同地址、数据模式和压力测试。
7. 启用 Cache/MMU，验证内存属性和异常处理。
8. 启动多核，验证核间中断与共享内存。
9. 逐个启用 DMA 和外设，先低速后高速。
10. 最后验证 DVFS、Runtime PM、Suspend/Resume 和安全状态。

每一步都保存“已知正常”的固件、配置、日志和测试结果，以便后续回退对比。

## 4. 通用故障定位模板

### 4.1 明确定义现象

不要只记录“启动失败”。应记录：

- 最后一个可靠日志或 Trace 点。
- 芯片 Revision、板卡版本和软件 Commit。
- 冷启动/热启动、温度、电压、频率。
- 复现概率和最短复现步骤。
- 是否与调试器连接、日志级别或延时相关。

### 4.2 确定故障边界

用最小测试区分：

- 单板问题还是所有板一致。
- 软件版本问题还是硬件配置问题。
- CPU 访问问题还是 DMA 访问问题。
- 数据通路问题还是中断通知问题。
- 冷启动问题还是状态恢复问题。
- 特定频点问题还是所有频点问题。

### 4.3 收集证据

- CPU 异常寄存器和调用栈。
- MMU/Page Table 与 Fault Address。
- Clock/Reset/Power 状态。
- 设备 Control/Status/IRQ/DMA/FIFO/Error 寄存器。
- SMMU/Firewall/NoC/DDR 错误记录。
- 中断控制器 Pending/Active 状态。
- 总线 Trace、逻辑分析仪和示波器数据。

### 4.4 建立假设并单变量验证

例如怀疑 Clock 频率错误，可以读取实际 Parent/Divider、输出测试 Clock 或用外部仪器测量，而不是一次性修改 Clock、Reset 和驱动配置。每个实验只改变一个主要变量，并记录预期与实际结果。

## 5. 常见现象速查

### 5.1 CPU 在取指早期挂死

检查 Reset Vector、Boot Remap、镜像入口、CPU 执行状态、SRAM/DDR 是否就绪、异常向量和安全状态。

### 5.2 MMIO 一访问就异常

检查 VA→PA 映射、地址 Base/Size、Memory Attribute、Firewall 权限、Power、Bus Clock 和 Reset。读取 CPU Fault Status 以区分翻译错误和外部 Abort。

### 5.3 外设寄存器可读但状态不变化

检查功能 Clock、模块 Enable、PHY/Pinmux、输入信号、状态机 Reset 和配置更新握手。

### 5.4 DMA 没有写入目标内存

检查 Descriptor、DMA 地址、地址宽度、SMMU Fault、Firewall、Ownership、Burst/Alignment、设备 Error 和 NoC 计数器。

### 5.5 DDR 压力下随机错误

检查训练裕量、频点/电压/温度、Timing、Refresh、ODT/Drive Strength、板级信号完整性、ECC Syndrome 和特定地址/数据模式。

### 5.6 系统低负载正常，高负载卡顿

检查 NoC/DDR 拥塞、QoS、Cache/TLB Miss、中断风暴、锁竞争、Thermal Throttling、DVFS 和队列背压。

## 6. 动手练习

### 练习 1：画一颗真实 SoC 的四张图

选取手边平台，分别画：顶层功能图、数据互联图、控制依赖图、启动安全图。每张图限制在一页内，迫使自己提炼关键关系。

验收标准：图中能指出 CPU 到 DDR、CPU 到 UART、Ethernet DMA 到 DDR、设备到 CPU 中断的完整路径。

### 练习 2：解析 MMIO 地址

给定 UART Base `0x1100_0000`、Status Offset `0x18`，计算寄存器地址并说明从 CPU 到 UART 的各级译码、所需内存属性以及可能返回的错误。

答案要点：地址为 `0x1100_0018`；路径包含 MMU 映射、系统互联、APB Bridge 和 UART；使用 Device 属性；错误可能来自翻译、权限、译码、目标响应或超时。

### 练习 3：计算地址窗口

给定区间 `0x4000_0000`～`0xBFFF_FFFF`，计算容量。

```text
0xBFFF_FFFF - 0x4000_0000 + 1 = 0x8000_0000 = 2 GiB
```

### 练习 4：设计上电状态机

为 PCIe Controller/PHY 写出 Power、Isolation、Clock、Reset、Reference Clock、PLL Lock、Link Training 的状态转换和每一步超时处理。

一种可落地的状态机如下：

```text
OFF
 → POWER_REQUEST：请求数字域和 PHY 域上电
 → POWER_GOOD：等待两个域的 Acknowledge，超时则撤销请求
 → REFCLK_ON：打开板级/片上 Reference Clock，等待稳定
 → CLOCK_ON：打开 APB、AXI、Core Clock
 → DEISOLATE：先解除数字域隔离，再按手册处理 PHY 隔离
 → RESET_RELEASE：依次释放 APB、Controller、PHY Reset
 → PLL_LOCK：等待 PHY PLL Lock，失败则复位 PHY 并有限次数重试
 → PHY_READY：加载校准参数，等待 Calibration Done
 → LINK_TRAINING：使能 LTSSM，等待进入 L0
 → ACTIVE
```

任何一步失败都不能直接跳回 `OFF`。先停止 LTSSM 和新事务，确认 AXI Outstanding 为零，再 Assert Reset、恢复 Isolation、关闭 Clock，最后下电。Link Training 超时还应保存 LTSSM 最后状态和 PHY 错误，而不是只返回通用超时码；停在 Detect、Polling 或 Recovery 对应完全不同的板级和协议原因。

### 练习 5：构造 DMA 故障树

场景：CPU 可以读写 Buffer，DMA Completion 一直不出现。至少从配置流、地址流、数据流、中断流和依赖流提出三个检查点。

参考推演：先读 DMA Enable、Channel State 和当前 Descriptor。Channel 根本没有进入 Running，说明 Start/Doorbell、Clock 或 Reset 有问题；进入 Running 但 Descriptor 地址不前进，检查 Descriptor Base、Alignment、Ownership 和 DMA 对该地址的可达性。SMMU 出现 Fault 时，根据 Fault IOVA 区分页表缺失与权限问题。SMMU 无错而 NoC Read Counter 为零，说明 DMA 没有真正发出请求；NoC 有事务而 DDR 无变化，则查 Firewall、地址路由和目标错误。

若 DMA 已更新内存中的 Completion/Descriptor，而 CPU 没收到通知，读取设备 Raw Interrupt。Raw 位为零表示完成条件或中断生成配置错误；Raw 有效而 GIC/PLIC 不 Pending，检查 Mask、连线和触发类型；控制器 Pending 而 CPU 未进入 ISR，检查 Affinity、Priority 和 CPU Mask。依赖流始终贯穿上述过程：Bus Clock 只保证寄存器可读，DMA Core Clock、Power Domain 和 Reset Scope 才决定搬运引擎能否运行。

## 7. 自测题

### 7.1 基础题

1. 为什么 SoC 不能等同于 CPU？
2. Controller 与 PHY 的职责有什么差异？
3. 同一 IP 为什么可能同时是 Initiator 和 Target？
4. Clock Gate、Reset 和 Power Gate 分别改变什么？
5. 为什么 MMIO 不应按普通 Cacheable RAM 映射？
6. Address Map 和 Register Map 有什么关系？
7. CPU PA 为什么不一定等于 DMA 地址？
8. 为什么寄存器可读不表示模块功能 Clock 正常？
9. Power Domain 下电前为什么必须排空事务？
10. Reset Cause 为什么要在启动早期读取？

### 7.2 推理题

1. UART TX FIFO 计数下降，但引脚没有波形。哪些路径已经基本正常，哪些部分仍需检查？
2. CPU 能访问低 2 GiB DDR，某 32 位 DMA 设备访问高 2 GiB 失败，可能怎样解决？
3. 一个设备 ISR 正常进入，但总读到旧 Descriptor。为什么不能只检查中断控制器？
4. 系统只在 Suspend/Resume 后出现 MMIO Timeout，应优先对比哪些状态？
5. 调高 CPU 频率后网卡吞吐没有变化，如何判断瓶颈位于 CPU、NoC、DDR 还是 MAC？

### 7.3 基础题解析

**1. SoC 为什么不能等同于 CPU？**

CPU 是执行指令的计算单元，SoC 则把 CPU 与存储、互联、外设、时钟、复位、电源、安全和调试组合成系统。CPU 能正确执行一段位于 L1 Cache 中的代码，并不能证明 DDR、DMA 或外设可用。反过来，系统也可能在应用 CPU 关机时由 Always-on MCU 继续运行。因此，CPU 是 SoC 的组成部分，不是 SoC 的同义词。

**2. Controller 与 PHY 的职责有什么差异？**

Controller 实现协议的数字逻辑：命令、队列、包格式、重传、DMA 和软件寄存器接口。PHY 负责位级传输和电气特性：串并转换、采样、均衡、PLL、阻抗和训练。以 DDR 为例，Controller 决定何时发 ACT/READ/WRITE/REFRESH，PHY 决定 DQ/DQS 信号在什么相位发出和采样。Controller 状态正常而链路不通时，Reference Clock、PLL、校准和板级信号仍可能失败。

**3. 同一 IP 为什么可能同时是 Initiator 和 Target？**

“Initiator/Target”描述的是总线端口角色，不是 IP 的永久身份。Ethernet MAC 的寄存器端口接收 CPU 的 MMIO 访问，因此是 Target；内部 DMA 为了读 Descriptor、写 Packet Buffer，会主动向 NoC 发起事务，因此又是 Initiator。两个端口可能拥有不同地址宽度、Clock、Reset 和安全属性，调试时必须区分。

**4. Clock Gate、Reset 和 Power Gate 分别改变什么？**

Clock Gate 停止时钟边沿，主要降低翻转造成的动态功耗，状态通常保留；Reset 把寄存器和状态机送到定义状态，但电源仍然存在；Power Gate 切断供电，显著降低漏电，普通寄存器内容随之丢失。三者不能互相替代。一个掉电域需要 Isolation，一个同步 Reset 需要运行中的 Clock，而单纯 Clock Gate 不会清除失控状态机。

**5. MMIO 为什么不应按普通 Cacheable RAM 映射？**

设备寄存器的读写可能具有副作用：读 FIFO 会弹出数据，写 Doorbell 会启动硬件，W1C 位写 1 会清状态。若把 MMIO 映射为普通 Cacheable Memory，CPU 可能从 Cache 返回旧值、合并多次写、推测读取或改变设备观察到的顺序。Device Memory 属性为这类访问提供架构级约束；C 语言 `volatile` 只约束编译器，不管理 Cache 和 CPU 总线顺序。

**6. Address Map 和 Register Map 有什么关系？**

Address Map 在系统地址空间中为一个 IP 分配窗口，Register Map 定义窗口内部各偏移。例如 UART0 Base 为 `0x1100_0000`，Status Offset 为 `0x18`，最终地址就是 `0x1100_0018`。前者由顶层互联译码，后者由 UART 内部寄存器译码。Base 写错通常访问到错误 IP 或产生 DECERR；Offset 写错则可能触发同一 IP 内的保留寄存器或其他功能。

**7. CPU PA 为什么不一定等于 DMA 地址？**

设备可能通过不同 NoC 入口看到带 Offset 的地址空间，也可能位于 SMMU 后，使用 IOVA 经过页表转换成 PA。设备自身还可能只实现较少地址位。操作系统 DMA API 返回的是设备可用地址，它可能数值上恰好等于 PA，但驱动不能依赖这一巧合，更不能把 CPU Virtual Address 直接写进 Descriptor。

**8. 为什么寄存器可读不表示模块功能 Clock 正常？**

许多 IP 把总线接口和功能状态机放在不同 Clock Domain。Bus Clock 打开后，寄存器 Bank 可以响应读写；Core Clock、Sample Clock 或 PHY Reference Clock 仍可能关闭。此时配置值能正常读回，FIFO 指针、传输状态和外部信号却不会变化。可靠判断要观察功能状态或实际输出，而不是只做寄存器回读。

**9. Power Domain 下电前为什么必须排空事务？**

总线读写是请求与响应组成的事务。若 Target 收到请求后被断电，上游拿不到响应，Outstanding 槽位无法释放；严重时会堵塞共享 Bridge 或 NoC，使无关 Master 一起挂死。写事务还可能只完成了一部分，留下数据或 Descriptor 不一致。因此要先停止新请求，等待 DMA、FIFO 和 NoC Outstanding 归零，再隔离并断电。

**10. Reset Cause 为什么要在启动早期读取？**

Reset Cause 常保存在 Always-on Sticky Register 中，但后续初始化、W1C 操作或另一层 Reset 可能清除它。启动代码若先复位 Watchdog 和 PMU，再读取原因，看到的就可能只剩默认值。正确做法是在尽可能早、栈和日志区刚可用时读取原始值，保存到不会被后续复位覆盖的内存，并在确认记录完成后再清除。

### 7.4 推理题解析

**1. UART TX FIFO 计数下降，但引脚没有波形。**

FIFO 计数下降说明 CPU 的 MMIO 配置路径、UART Register Bank、FIFO 以及至少一部分发送状态机正在工作，Bus Clock 和 Core Clock 也大概率存在。故障边界已经移动到 Serializer 之后：检查 TX Output Enable、Pinmux 是否选择 UART 功能、Pad 是否被配置为输入或高阻、对应 I/O Power 是否存在，以及封装引脚和板级连线。示波器应先量 SoC Pad，再量连接器，以区分片内配置与 PCB 问题。若计数下降速度不符合波特率，还应重新核对 Core Clock 和 Divider。

**2. 32 位 DMA 设备访问高 2 GiB DDR 失败。**

4 GiB 以上的地址至少需要 33 位，32 位 DMA 无法直接编码。首选方案是在 SMMU 中给设备分配低于 4 GiB 的 IOVA，再映射到高 PA；没有 SMMU 时，让 DMA API 从低端可达区分配 Buffer。若业务数据必须位于高端内存，可用低端 Bounce Buffer 中转，但会增加一次拷贝和同步成本。直接截断高位会把事务送到错误地址，必须禁止。

**3. ISR 正常进入，但 CPU 总读到旧 Descriptor。**

ISR 只证明设备中断源、控制器和 CPU 异常路径可用。Descriptor 走的是另一条内存数据路径。非一致 DMA 写内存后，CPU Cache 可能仍有旧 Cache Line，需要按 DMA API 转移所有权并 Invalidate；一致 DMA 也要保证设备先写 Descriptor，再发布 Completion，中断处理端则在观察到完成后执行适当的读屏障。还要排除 Descriptor 与其他 CPU 写入共享一个 Cache Line、DMA 地址错误或硬件提前发中断。

**4. Suspend/Resume 后出现 MMIO Timeout。**

先与正常冷启动逐项比较 Power Request/Acknowledge、Isolation、Bus Clock、Reset 和 NoC Bridge 状态。MMIO Timeout 表明请求大概率已发出却没有响应，因此 Bus Clock、下游 Power 或跨域 Bridge 比业务配置更值得先查。若域已上电，确认同步 Reset 所依赖的 Clock 在释放时确实运行；若多个设备共享 Bridge，还要检查 Suspend 前是否遗留 Outstanding 事务。仅恢复驱动寄存器而没有重建 Clock Parent、Pinmux 或 Firewall，也会造成恢复路径与冷启动不同。

**5. 提高 CPU 频率后网卡吞吐没有变化。**

先确定是否已达到链路线速；若 MAC TX/RX Byte Counter 已接近协议有效上限，CPU 再快也不会增加吞吐。未到线速时，看 RX FIFO Overflow、Ring Empty 和 Queue Occupancy：Ring Empty 且某 CPU 满载，可能是驱动/协议栈瓶颈；FIFO Overflow 同时 NoC/DDR 延迟升高，则更像内存路径瓶颈。CPU PMU 给出 Cycle、IPC、Cache Miss，NoC/DDR 计数器给出带宽和等待时间，MAC 统计给出链路错误与 FIFO 丢包。只有这些证据指向软件处理能力不足，提高 CPU 频率才应带来近似可预测的改善。

## 8. 模块完成标准

如果能够独立完成以下任务，可以认为已掌握本模块：

- 把陌生 SoC 框图拆成计算、存储、互联、I/O、控制、安全和调试七类模块。
- 建立 Initiator/Target 可达矩阵和至少一张端到端访问路径图。
- 从 Base、Size 和 Offset 准确计算地址，并说明其内存属性。
- 为一个外设列出 MMIO、IRQ、DMA、Clock、Reset、Power 和 Pinmux 依赖。
- 区分配置流、数据流和中断流，并据此建立故障树。
- 描述一个电源域从上电、恢复、工作到安全下电的完整流程。
