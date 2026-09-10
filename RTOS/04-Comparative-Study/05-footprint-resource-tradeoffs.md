# 资源占用与测量

## 1. 内存资源占用（Footprint）的现实意义

在千万级出货量的消费电子或成本极度敏感的传感器节点中，MCU 的 Flash 和 RAM 规格直接决定单颗芯片的 BOM 成本（例如：从 128KB Flash / 32KB RAM 跨越到 512KB Flash / 128KB RAM，每片成本可能增加 0.5 ~ 1.5 美元）。

因此，评估 RTOS 的**资源开销底线与增长弹性**，是技术选型的决定性考量之一。

## 2. 按相同功能测量资源占用

目前没有随文提供可复现的两套目标固件、配置和 map 文件，因此不列出系统间的 KB 排名。对比时至少固定处理器、编译器、优化选项、任务数、栈大小和启用的驱动/协议栈。

| 配置 | 测量内容 |
| :--- | :--- |
| 仅内核 | 调度器、Tick、空闲任务与应用任务存储 |
| 基础外设 | 在同一基线加入 UART/GPIO/I2C，记录增量 |
| 网络或 BLE | 明确控制器、Host、缓冲池及连接数，分别记录 Flash/RAM |
| 用户态隔离 | 记录对象元数据、特权栈和 MPU 对齐额外开销 |

## 3. RAM 消费深挖：控制块与栈的解剖

Flash 差距是「付一次」，RAM 差距才是「每线程都付」。两类内核的每线程成本构成（字段分组为典型示例值，教育用途，64 位无关；以 32 位架构实际 sizeof 为准）：

| RAM 消费项 | FreeRTOS（TCB_t + 栈） | Zephyr（struct k_thread + 栈） | 说明 |
| :--- | :--- | :--- | :--- |
| **核心控制字段** | 栈顶指针、状态/事件链表节点、优先级与基址优先级、TCB 链表节点 | 栈顶指针、调度器节点（dumb/multiq/rbtree 三选一，尺寸不同）、优先级/时序字段 | 两者同为数十字节量级 |
| **内核对象关联** | 互斥持有计数 `uxMutexesHeld`、通知值/状态（任务通知内嵌 TCB） | 对象核心节点、syscall 授权位图（userspace 开启时） | Zephyr userspace 附加项随配置增长 |
| **FPU 上下文** | ARM_CM4F 按需保存到任务栈，必须预留该 RAM | 保存位置依架构而异，核对线程结构和栈 | FPU 帧按需驻留各任务栈 |
| **名称/调试字段** | `pcTaskName`（configMAX_TASK_NAME_LEN） | `thread_name`（可选配置） | 裁剪点：缩短或关闭 |

!!! note
    **任务栈通常是 RAM 预算的重要部分**：每线程 128B~4KB 的栈 × 线程数，远超控制块总和。FreeRTOS 的 `configMINIMAL_STACK_SIZE` 与 Zephyr 的 `CONFIG_MAIN_STACK_SIZE`/`K_THREAD_STACK_SIZEOF` 才是 RAM 预算的主战场。栈尺寸必须以「High-Water Mark 实测 + 最坏嵌套路径复核」双保险确定，而非拍脑袋常数。


对象成本应从实际构建取值：FreeRTOS 的队列/信号量复用 `Queue_t`，软件定时器每个实例有自己的控制块，命令队列与服务任务由实例共享。Zephyr 的 `k_msgq`、`k_sem`、`k_timer` 等分别计量。栈、堆和缓冲池若已在 `.bss` 或 `.noinit` 中预留，不应重复加总。

--- | :--- | :--- |
| 队列/消息队列（不含缓冲体） | `Queue_t` 约 76~80B + 存储区 | `k_msgq` 约 40~60B + 环形缓冲 |
| 二值/计数信号量 | 复用 Queue_t（约 76B） | `k_sem` 约 16~24B |
| 互斥锁 | 复用 Queue_t（含持有者字段） | `k_mutex` 约 32~48B（含 owner/继承字段） |
| 软件定时器 | 复用队列命令 + TCB（守护任务） | `k_timer` 约 40~60B（链入系统超时链） |
| 工作队列作业 | 不适用（无内建） | `k_work` 约 24~40B |

---

## 4. 瘦身手段矩阵

| 瘦身杠杆 | FreeRTOS | Zephyr |
| :--- | :--- | :--- |
| **编译选项** | `-Os` + `-ffunction-sections` + `--gc-sections`（newlib-nano/picolibc 换 C 库） | 同左 + `CONFIG_SIZE_OPTIMIZATIONS=y` |
| **配置裁剪** | 关 `configUSE_TRACE_FACILITY`/`configUSE_MUTEXES`/统计与断言；慎关 `configASSERT`（调试期保留） | Kconfig 依赖闭包自动排除未用驱动；再关 `CONFIG_SHELL`/`CONFIG_LOG`/`CONFIG_USERSPACE`/`CONFIG_SMP` |
| **栈与堆** | `heap_1` 只配不还省去碎片管理；堆尺寸贴合静态分配需求 | `CONFIG_MAIN_STACK_SIZE`、各 `K_THREAD_STACK_DEFINE` 实测收敛；无动态堆（可选） |
| **printf 家族** | 换微型格式化（如极简 `snprintf` 实现），printf 家族常占数 KB | `CONFIG_CBPRINTF_COMPLETE=n`（缩减版 cbprintf，去除宽字符/长长整型等）、`CONFIG_LOG_MODE_MINIMAL` |
| **驱动排除** | 不链接厂商 HAL 未用外设源文件（依赖源级组织） | 设备树 `status="disabled"` + Kconfig 依赖闭包：未引用驱动**零链接成本** |
| **多点收益对比** | 起点已极低，杠杆有限但每个都直接 | 基线较高，但 Kconfig+DT 的组合裁剪是系统性优势——「没配置就等于不存在」 |

**测量工具链（一次一条）**：
* `arm-none-eabi-size -A firmware.elf`：按段罗列 text/rodata/data/bss，结合 map 文件统计 data/bss/noinit 与其他预留区，避免重复计入栈堆。
* `arm-none-eabi-nm --size-sort -S firmware.elf | tail -30`：揪出最大的 30 个符号，直击「谁吃掉了 Flash」。
* `puncover`：生成交互式网页报告，逐函数尺寸 + 调用树 + 栈深估算。
* `bloaty -d compileunits,symbols old.elf -- new.elf`：两个版本间的体积 diff，回归监控利器。
* Zephyr 专属：构建尾端自动打印 `Memory region Usage Size`（含 `ROM`/`RAM` 列），可直接接 CI 阈值检查。

---

## 5. 选型时的资源判断

资源较紧时先构建最小可用配置，再逐项加入功能。FreeRTOS 的调度内核范围较小，Zephyr 集成的驱动和子系统更多；最终差异取决于产品实际使用的功能。以链接产物和运行期栈/缓冲峰值决定是否满足目标芯片预算。
