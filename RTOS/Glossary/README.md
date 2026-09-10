# RTOS 核心术语与缩写速查

按主题分组；同一条目内给出英文全称与一句话工程释义。跨模块复用的术语以首次出现的领域为准。

## 1. 实时与调度理论

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **RTOS** | Real-Time Operating System | **实时操作系统**：以确定性（时限控制）为核心设计的嵌入式操作系统。 |
| **RMS** | Rate-Monotonic Scheduling | **单调速率调度**：周期越短优先级越高的静态最优调度算法。 |
| **DM** | Deadline Monotonic | **截止期单调调度**：相对截止期越短优先级越高的静态算法；当 $D_i \le T_i$ 时比 RMS 更优。 |
| **EDF** | Earliest Deadline First | **最早截止时间优先**：截止时限最近的任务优先执行的动态调度理论。 |
| **WCET** | Worst-Case Execution Time | **最坏情况执行时间**：某段任务或代码在最严苛硬件与并发下的运行上限。 |
| **RTA** | Response Time Analysis | **响应时间分析**：用递归方程 $R_i = C_i + B_i + \sum \lceil R_i/T_j \rceil C_j$ 逐任务验证时限的精确方法。 |
| **TCB** | Task Control Block | **任务控制块**：内核维护任务状态、栈顶指针、优先级的核心数据结构。 |
| **PIP** | Priority Inheritance Protocol | **优先级继承协议**：低优先级占有锁被高优先级阻塞时临时升至高优先级，防御反转。 |
| **PCP** | Priority Ceiling Protocol | **优先级天花板协议**：资源被占用时直接升至预设天花板优先级，杜绝死锁。 |
| **WCIL** | Worst-Case Interrupt Latency | **最坏情况中断延迟**：给定屏蔽窗口与抢占干扰下推导出的中断响应时间上界。 |
| **Jitter** | Timing Jitter | **时钟抖动**：周期性事件实际发生时刻的离散度，实时性的核心观测指标。 |

## 2. ARM Cortex-M 体系与中断

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **PSP / MSP** | Process / Main Stack Pointer | **进程 / 主堆栈指针**：ARM Cortex-M 硬件双堆栈解耦机制。 |
| **PendSV** | Pended Service Call | **可悬挂系统调用**：用于推迟执行上下文切换以防破坏中断现场的最低优先级异常。 |
| **SysTick** | System Tick Timer | **系统滴答定时器**：处理器内核自带的递减定时器，用于提供系统时钟节拍。 |
| **NVIC** | Nested Vectored Interrupt Controller | **嵌套向量中断控制器**：Cortex-M 内的中断优先级仲裁、屏蔽与嵌套管理单元。 |
| **BASEPRI** | Base Priority Mask | **基础优先级屏蔽寄存器**：非零时屏蔽优先级数值大于或等于阈值的可配置异常；FreeRTOS 用它实现「可调用的中断才被关」的选择性临界区。 |
| **PRIMASK** | Primary Interrupt Mask | **一级中断屏蔽寄存器**：`cpsid i` 置位后屏蔽全部可屏蔽中断，粗暴但一刀切。 |
| **FAULTMASK** | Fault Exception Mask | **异常屏蔽寄存器**：连 HardFault 都可屏蔽的最高级别中断掩码，仅在极短窗口内使用。 |
| **EXC_RETURN** | Exception Return Value | **异常返回值**：LR 在异常时载入的魔数（如 `0xFFFFFFFD`），低位编码返回模式、栈选择及帧类型（FPU 帧由 bit 4 标识）。 |
| **FPCA / Lazy Stacking** | FP Context Active / Lazy State Preservation | **浮点上下文激活位 / 惰性压栈**：CONTROL.FPCA 标记任务用过 FPU；FPCCR 的惰性机制把 s0–s15 的硬件压栈推迟到 ISR 真正执行浮点指令之时。 |
| **Tail-Chaining** | — | **尾链**：Cortex-M 让下一异常直接复用出栈-入栈序列的硬件优化，省去回到线程模式再进异常的往返周期。 |
| **Late Arrival** | — | **晚到（高优先级抢占压栈）**：压栈期间更高优先级中断到达时，硬件复用正在保存的现场、优先执行晚到者的机制。 |
| **CLZ** | Count Leading Zeros | **计算前导零指令**：用于单周期内极速定位最高就绪任务优先级的硬件指令。 |
| **DMB / DSB / ISB** | Data Memory / Data Synchronization / Instruction Synchronization Barrier | **三类内存/指令屏障**：DMB 保证访问序、DSB 保证完成序、ISB 保证流水线重取指；核间通信与 MPU 重配置的必用工具。 |
| **CFSR / MMFAR** | Configurable Fault Status Register / MemManage Fault Address Register | **故障状态/地址寄存器**：解码 HardFault 真因（MPU 违例、总线错、压栈失败）与非法访问地址的第一现场。 |
| **WFI** | Wait For Interrupt | **等待中断指令**：内核进入低功耗停钟状态，中断或事件将其唤醒；idle 任务节流的最后手段。 |

## 3. RISC-V 体系

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **SBI** | Supervisor Binary Interface | **监管者二进制接口**：S 态内核请求 M 态固件（如 OpenSBI）服务（置定时器、发射 IPI）的标准调用层。 |
| **mtime / CLINT** | Machine Timer / Core Local Interruptor | **机器态计时器 / 核本地中断器**：RISC-V 标准时基与软件/定时器中断源，mtimecmp 比较触发时钟中断。 |
| **sstatus / SPP** | Supervisor Status / Supervisor Previous Privilege | **S 态状态寄存器 / 来源特权位**：SPP 记录 trap 发生时身处 U 态还是 S 态，是判定「可否抢占」的依据。 |
| **Sv32** | — | **32 位虚地址分页模式**：两级页表（VPN[1]/VPN[0]），RVKernel Lab 的页表实验基准。 |

## 4. FreeRTOS 内核

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **FromISR 后缀** | — | **中断安全 API 族**：`xQueueSendFromISR` 等在 ISR 内唯一合法的内核调用形式，不阻塞、以 `pxHigherPriorityTaskWoken` 回传唤醒请求。 |
| **High-Water Mark** | Stack High-Water Mark | **栈历史最低水位**：从未触及的栈底剩余量（魔数未被覆写的深度）；衡量栈预算是否充裕。 |
| **Tickless Idle** | — | **无节拍空闲**：空闲时停掉 SysTick、按最近到期事件编程低功耗定时器，醒后补偿节拍数的低功耗机制。 |
| **Idle Task** | — | **空闲任务**：优先级 0 的内核自建任务，负责回收被删任务资源与执行低功耗钩子，永不许阻塞。 |

## 5. Zephyr 体系

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **DTS / DTB** | DeviceTree Source / Blob | **设备树源码 / 二进制文件**：用于将硬件外设信息与操作系统驱动完全解耦的标准。 |
| **Overlay** | DeviceTree Overlay | **设备树覆盖片**：不改板级 dtsi、只追加/改写节点的增量文件（`.overlay`），换板适配的主手段。 |
| **Binding** | Devicetree Binding | **设备树绑定**：YAML 描述某 `compatible` 节点必须/可选携带哪些属性，是 DT 与驱动 API 之间的契约。 |
| **chosen** | /chosen Node | **约定节点**：设备树中声明系统级默认外设（stdout 串口、zephyr,flash 等）的节点。 |
| **gen_defines / devicetree.h** | — | **DT 生成宏**：构建期由 DTS 生成的 `DT_*`/`DT_N_*` 宏族，C 代码借它静态寻址硬件。 |
| **Kconfig** | Kernel Configuration | **内核配置系统**：起源于 Linux 内核、声明式管理宏开关与依赖的静态配置树。 |
| **West** | Zephyr Meta-tool | **Zephyr 专属元工具**：负责代码拉取、多仓库同步、编译构建与固件烧录。 |
| **Sysbuild** | — | **多镜像构建**：Zephyr 统一编排应用+bootloader（MCUboot）+多核镜像的顶层构建系统。 |
| **Init Level** | Initialization Level | **初始化层级**：Zephyr 驱动按 `EARLY→PRE_KERNEL_1/2→POST_KERNEL→APPLICATION→SMP` 顺序挂钩的静态初始化框架。 |
| **Vtable** | Virtual Method Table | **虚函数表**：C 语言中通过包含函数指针的结构体实现驱动面向对象多态的标准范式。 |
| **K_USER** | — | **用户态线程标志**：以非特权态创建线程的选项；一切内核访问须经系统调用与对象授权。 |
| **Memory Domain / Partition** | — | **内存域 / 内存分区**：Zephyr 将若干 MPU 保护分区打包为域，随线程切换整体换装的隔离单位。 |
| **Workqueue** | — | **工作队列**：把延迟/异步作业提交到专用内核线程执行的机制，ISR 卸载长活的标准去处。 |
| **k_poll** | — | **多路等待 API**：单线程同时等待信号量/队列/信号等多类事件的一次性/周期轮询原语。 |
| **Object Core** | Kernel Object Core | **内核对象核心**：Zephyr 新一代统一对象注册/追溯基础设施，userspace 权限校验与调试追溯的底座。 |

## 6. 多核与核间互联

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **SMP** | Symmetric Multiprocessing | **对称多处理**：多核跑同一 OS 镜像共享调度，Zephyr 以 `CONFIG_SMP` 支持。 |
| **AMP** | Asymmetric Multiprocessing | **非对称多处理**：多个不同架构核心分别运行独立操作系统，通过共享内存协同。 |
| **IPI** | Inter-Processor Interrupt | **核间中断**：一个核向另一个核发出的软件中断；SMP 调度踢核与 AMP 门铃的物理载体。 |
| **OpenAMP** | Open Asymmetric MultiProcessing | **开源 AMP 框架**：跨 OS 的 remoteproc/rpmsg 参考实现，Linux 与 RTOS 从核通信的事实标准。 |
| **RPMsg** | Remote Processor Messaging | **远端处理器消息框架**：基于 VirtIO 环形缓冲区的跨异构核心标准化通信协议。 |
| **vring / virtqueue** | Virtual Ring / Queue | **虚拟环/队列**：VirtIO 描述符表+avail/used 双环结构，RPMsg 消息的实际载体。 |
| **remoteproc** | Remote Processor Framework | **远端处理器框架**：Linux 侧加载从核固件、解析资源表、管理其启停与崩溃恢复的生命周期管理器。 |
| **CARVEOUT / smem** | Carved-out Shared Memory | **保留共享内存区**：设备树 `reserved-memory` 中为双核通信划出的物理连续专用区。 |

## 7. 安全、启动与合规

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **MPU** | Memory Protection Unit | **内存保护单元**：微控制器硬件支持的轻量级内存区域访问权限过滤硬件。 |
| **TF-M** | Trusted Firmware-M | **ARM 安全固件参考实现**：基于 ARMv8-M TrustZone 的嵌入式可信执行环境。 |
| **PSA** | Platform Security Architecture | **平台安全架构**：ARM 主导的物联安全框架；PSA Certified 为其分级认证体系。 |
| **MCUboot** | — | **安全引导加载器**：Apache 2.0 开源 bootloader，签名验签与防回滚的 A/B 升级方案，Zephyr 默认集成。 |
| **TrustZone** | ARM TrustZone | **信任域技术**：ARMv8-M 将总线与外设划分为安全/非安全两世界的硬件隔离机制。 |

## 8. 调试与测量

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **DWT** | Data Watchpoint and Trace | **数据观察点与跟踪单元**：Cortex-M 调试单元；CYCCNT 周期计数与数据断点（写入即断）取证利器。 |
| **RTT** | Real-Time Transfer | **实时传输**：SEGGER 经调试口的后台内存通道，SystemView/日志无停机上传的基础。 |
| **Tracealyzer** | Percepio Tracealyzer | **任务级跟踪分析器**：抓取 FreeRTOS 内核事件流生成时间线/阻塞链可视报告的商业工具。 |
| **addr2line** | — | **地址转行号工具**：把故障栈帧里的 PC/LR 映射回 `文件:行号`，硬故障定位第一步。 |
