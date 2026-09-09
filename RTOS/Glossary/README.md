# RTOS 核心术语与缩写速查

| 缩写 / 术语 | 英文全称 | 中文全称与工程释义 |
| :--- | :--- | :--- |
| **RTOS** | Real-Time Operating System | **实时操作系统**：以确定性（时限控制）为核心设计的嵌入式操作系统。 |
| **TCB** | Task Control Block | **任务控制块**：内核维护任务状态、栈顶指针、优先级的核心数据结构。 |
| **RMS** | Rate-Monotonic Scheduling | **单调速率调度**：周期越短优先级越高的静态最优调度算法。 |
| **EDF** | Earliest Deadline First | **最早截止时间优先**：截止时限最近的任务优先执行的动态调度理论。 |
| **WCET** | Worst-Case Execution Time | **最坏情况执行时间**：某段任务或代码在最严苛硬件与并发下的运行上限。 |
| **PSP / MSP** | Process / Main Stack Pointer | **进程 / 主堆栈指针**：ARM Cortex-M 硬件双堆栈解耦机制。 |
| **PendSV** | Pended Service Call | **可悬挂系统调用**：用于推迟执行上下文切换以防破坏中断现场的最低优先级异常。 |
| **SysTick** | System Tick Timer | **系统滴答定时器**：处理器内核自带的递减定时器，用于提供系统时钟节拍。 |
| **CLZ** | Count Leading Zeros | **计算前导零指令**：用于单周期内极速定位最高就绪任务优先级的硬件指令。 |
| **PIP** | Priority Inheritance Protocol | **优先级继承协议**：低优先级占有锁被高优先级阻塞时临时升至高优先级，防御反转。 |
| **PCP** | Priority Ceiling Protocol | **优先级天花板协议**：资源被占用时直接升至预设天花板优先级，杜绝死锁。 |
| **DTS / DTB** | DeviceTree Source / Blob | **设备树源码 / 二进制文件**：用于将硬件外设信息与操作系统驱动完全解耦的标准。 |
| **Kconfig** | Kernel Configuration | **内核配置系统**：起源于 Linux 内核、声明式管理宏开关与依赖的静态配置树。 |
| **West** | Zephyr Meta-tool | **Zephyr 专属元工具**：负责代码拉取、多仓库同步、编译构建与固件烧录。 |
| **Vtable** | Virtual Method Table | **虚函数表**：C 语言中通过包含函数指针的结构体实现驱动面向对象多态的标准范式。 |
| **MPU** | Memory Protection Unit | **内存保护单元**：微控制器硬件支持的轻量级内存区域访问权限过滤硬件。 |
| **AMP** | Asymmetric Multiprocessing | **非对称多处理**：多个不同架构核心分别运行独立操作系统，通过共享内存协同。 |
| **RPMsg** | Remote Processor Messaging | **远端处理器消息框架**：基于 VirtIO 环形缓冲区的跨异构核心标准化通信协议。 |
| **TF-M** | Trusted Firmware-M | **ARM 安全固件参考实现**：基于 ARMv8-M TrustZone 的嵌入式可信执行环境。 |
