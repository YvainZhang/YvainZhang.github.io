# FreeRTOS 异步 SDK 实践

把一个提前归池的 buffer 问题放回任务与队列中：接口复制了什么，任务通知唤醒了谁，停止时还剩哪些结果没有交付？本组实践沿着这些问题，连接已有的内核机制分析。

| 起点 | 先理解的机制 | 实践章节 |
| --- | --- | --- |
| 接口返回后，buffer 能复用吗？ | [Queue 复制与互斥量](../02-FreeRTOS-Deep-Dive/04-queue-internals-semaphore-mutex.md) | [队列、通知与 owner](02-queue-owner.md) |
| 通知到达以后，工作为什么仍没处理完？ | [任务通知与事件组](../02-FreeRTOS-Deep-Dive/07-task-notifications-event-groups-timers.md) | [队列状态与调度预算](02-queue-owner.md) |
| 恢复后旧回复到达，如何避免误匹配？ | 请求身份与代际 | [恢复与停止](03-recovery-stop.md) |
| 停止超时后，可以直接释放实例吗？ | [任务生命周期](../01-RTOS-Fundamentals/02-task-lifecycle-tcb-context-switch.md) | [退出责任与剩余工作](03-recovery-stop.md) |

先按 [实验环境](01-environment.md)获取固定版本依赖，再进入队列和停止实验。这里使用 FreeRTOS V11.1.0 POSIX port，运行实际任务、队列与调度器；它支持宿主功能核对，MCU 的 tick、中断、DMA、任务栈和最坏时延仍要在对应 port 与硬件上验证。

这些实践采用纯 C 业务核心和独立 FreeRTOS runtime。共同接口保证与预算见 [平台架构实践](https://xidianedu.cc/tech/platform/)，Linux 的线程、epoll 与驱动实验见 [Linux 系统实践](https://xidianedu.cc/tech/linux/)。

[公开源码与许可](https://xidianedu.cc/tech/platform/reference/source/) · [验证记录](https://xidianedu.cc/tech/platform/reference/verification/)
