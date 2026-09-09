# RTOS 架构总览

RTOS 通过任务调度、中断处理和同步机制协调并发执行。分析实时性时，需要关注中断响应、调度延迟、临界区长度和任务的截止时间。

```mermaid
graph TD
    subgraph Fundamentals["01 RTOS 通用核心机制"]
        F1["硬/软实时 & 调度理论"] --> F2["TCB & 硬件现场压栈"]
        F2 --> F3["SysTick & 临界区保护"]
        F3 --> F4["IPC / 信号量 / 优先级继承"]
        F4 --> F5["内存堆分配 & MPU 隔离"]
    end

    subgraph DeepDive["FreeRTOS 与 Zephyr"]
        direction LR
        subgraph FreeRTOS["02 FreeRTOS (调度核)"]
            FR1["极简微内核 / 源码拓扑"]
            FR2["pxReadyTasksLists 位图调度"]
            FR3["PendSV 汇编切换"]
            FR4["Queue / 互斥量底层"]
            FR5["heap_1 ~ heap_5 内存模型"]
            FR6["ISR 安全与工程陷阱"]
        end
        subgraph Zephyr["03 Zephyr (全栈生态 OS)"]
            Z1["微内核演进与类 Linux 哲学"]
            Z2["DeviceTree & Kconfig 体系"]
            Z3["红黑树/多链表多算法调度"]
            Z4["统一驱动模型 DEVICE_DT_DEFINE"]
            Z5["Userspace / MPU / 系统调用"]
            Z6["OpenAMP / BLE / 低功耗"]
        end
    end

    subgraph Decision["04 系统对比与选型"]
        C1["设计哲学与架构范式"]
        C2["调度延迟与实时抖动实测"]
        C3["硬件抽象与驱动迁移"]
        C4["内存保护与安全认证"]
        C5["Flash/RAM Footprint 极值"]
        C6["选型决策树与场景矩阵"]
    end

    Fundamentals --> DeepDive
    DeepDive --> Decision
```

---

## 推荐学习路线

### 路线一：内核工程师（底层原理与汇编级现场）
> 专注处理器微架构交互、中断延迟压制与上下文切换细节。
>
> 1. [实时性与调度理论](../01-RTOS-Fundamentals/01-realtime-principles-scheduling.md) →
> 2. [任务生命周期与上下文切换](../01-RTOS-Fundamentals/02-task-lifecycle-tcb-context-switch.md) →
> 3. [PendSV 汇编现场切换](../02-FreeRTOS-Deep-Dive/03-context-switch-pendsv-assembly.md) →
> 4. [中断体系与临界区保护](../01-RTOS-Fundamentals/03-interrupt-systick-critical-section.md) →
> 5. [任务栈溢出与内存破坏分析](../Case-Studies/02-stack-overflow-isr-corruption-debug.md)

### 路线二：嵌入式软件架构师（系统选型与驱动生态）
> 权衡系统复杂度、开发成本、可移植性与软硬件解耦。
>
> 1. [FreeRTOS 架构哲学与源码拓扑](../02-FreeRTOS-Deep-Dive/01-freertos-architecture-source-topology.md) →
> 2. [Kconfig 与 DeviceTree 体系](../03-Zephyr-Deep-Dive/02-build-system-kconfig-devicetree.md) →
> 3. [统一设备驱动模型](../03-Zephyr-Deep-Dive/04-unified-driver-model.md) →
> 4. [设计哲学与架构范式对比](../04-Comparative-Study/01-philosophy-architectural-paradigm.md) →
> 5. [场景选型决策树与选型矩阵](../04-Comparative-Study/06-selection-decision-tree.md)

### 路线三：异构与多核开发工程师（SoC 协同与核间通信）
> 掌握核间中断、共享内存与 AMP 架构下的 RTOS 角色。
>
> 1. [子系统生态与多核 AMP](../03-Zephyr-Deep-Dive/07-subsystems-amp-power-management.md) →
> 2. [异构多核 AMP RPMsg 协同](../Case-Studies/03-amp-rpmsg-heterogeneous-multicore.md) →
> 3. [内存模型与保护机制](../01-RTOS-Fundamentals/05-memory-management-safety.md)

### 路线四：RVKernel 内核实验
> 在 QEMU RISC-V 环境中运行和调试 RVKernel。
>
> 1. [RVKernel 实验总览与环境准备](../Labs/README.md) →
> 2. [启动、Trap 现场与 Sv32 页表](../Labs/lab01-rv32-boot-trap-paging.md) →
> 3. [SBI 定时器中断与用户态抢占](../Labs/lab02-rv32-timer-preemption-scheduler.md) →
> 4. [环形缓冲与具名管道 IPC](../Labs/lab03-rv32-bounded-pipe-ipc.md) →
> 5. [1~4 核 SMP 多核启动与 IPI](../Labs/lab04-rv32-smp-multicore-ipi.md)

