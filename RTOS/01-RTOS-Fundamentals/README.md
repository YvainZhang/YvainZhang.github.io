# 01 RTOS 通用核心机制

无论是经典的 FreeRTOS、RT-Thread、ThreadX、VxWorks，还是现代化的 Zephyr，所有嵌入式实时操作系统的核心目标都高度一致：**提供可预测的执行时序、安全可控的任务并发与确定的中断响应。**

本模块梳理所有 RTOS 底层必须直面的普适性计算机系统基础：

```mermaid
graph LR
    A["硬件定时器 / 中断源"] --> B["SysTick / ISR 现场"]
    B --> C["内核调度器 (Scheduler)"]
    C --> D["任务控制块 (TCB) 状态流转"]
    D --> E["上下文切换 (Context Switch)"]
    E --> F["IPC 管道 / 同步锁"]
    F --> G["MPU / 内存保护安全域"]
```

## 篇章目录

1. [实时性与调度理论](01-realtime-principles-scheduling.md)
   - 硬实时（Hard Real-Time）与软实时（Soft Real-Time）的核心区别
   - 确定性（Determinism）、抖动（Jitter）与执行截止时间（Deadline）
   - 经典周期调度理论：单调速率调度（RMS）与最早截止时间优先（EDF）
   - 优先级抢占式（Preemptive）与协作式（Cooperative）调度模型

2. [任务生命周期与上下文切换](02-task-lifecycle-tcb-context-switch.md)
   - 任务状态机：Running、Ready、Blocked/Waiting、Suspended
   - 任务控制块（TCB）的核心内存布局
   - 硬件压栈与软件补齐压栈流程（Cortex-M 双堆栈指针 MSP/PSP）
   - 上下文切换的原子性保证与现场恢复过程

3. [中断体系与临界区保护](03-interrupt-systick-critical-section.md)
   - SysTick 系统时钟节拍与时间基准推移
   - 中断延迟（Interrupt Latency）三要素：关中断时长、硬件仲裁、现场保护
   - 中断嵌套（Nested Interrupts）与顶半部/底半部（Top/Bottom Half）划分
   - 临界区保护手段：关全局中断、BasePri 遮罩与互斥锁的开销权衡

4. [IPC 通信与同步机制](04-ipc-synchronization-primitives.md)
   - 消息队列（Message Queue）底层实现与零拷贝设计
   - 信号量（Semaphore）与事件组（Event Flags）
   - 互斥锁（Mutex）与致命的“优先级反转”（Priority Inversion）
   - 优先级继承协议（PIP）与优先级天花板协议（PCP）

5. [内存模型与保护机制](05-memory-management-safety.md)
   - 静态编译期分配与动态内存堆分配权衡
   - 外部碎片与内部碎片的数学本质
   - 内存保护单元（MPU）在任务级栈隔离与非法越界防御中的应用
