# 队列保存工作，通知唤醒 owner

生产者把 buffer 指针传入接口，随后立即归池。若队列只保存这个指针，消费者晚些时候拿到的可能已经是另一笔数据。先明确复制边界，再讨论通知与调度。

实现位于 [公开源码](https://xidianedu.cc/tech/platform/reference/source/) 的 `platform/runtime/freertos/runtime.c`；前置阅读是 [队列实现](../02-FreeRTOS-Deep-Dive/04-queue-internals-semaphore-mutex.md)与 [任务通知](../02-FreeRTOS-Deep-Dive/07-task-notifications-event-groups-timers.md)。

## 从 API 到设备任务

```text
API → mutex / ingress queue → task notification
                                  ↓
                              owner task
                                  ↓
                               C core
                                  ↓
                       commands → device task
                                  ↓
                         replies / data queues
```

owner 单独修改 core。API 复制输入并把 `core_event` 放进固定入口队列；device task 执行命令，经回复和数据队列交回结果。`xTaskNotifyGive` 提示 owner 检查真实队列；`ulTaskNotifyTake` 的计数不能代替排队工作的数量。

## Queue 究竟复制什么

本例静态队列的 item 大小是 `sizeof(struct core_event)`，包含 payload。FreeRTOS 按 item 大小复制，因此调用者的 buffer 不需要随队列元素一起保留。

若 item 换成指针，队列只复制地址。接口还需要明确借用直到完成、转移所有权或另做复制。这个选择同时改变 RAM、复制开销与停止回收。[FreeRTOS 队列 API](https://www.freertos.org/Documentation/02-Kernel/04-API-references/06-Queues/01-xQueueCreate)

## 满队列与调度顺序

owner 优先级为 3，device 为 2。device 连续发送时，owner 可能在中途被唤醒并消费；发送次数超过容量，不保证真正触发满队列。

定向过载注入在短且有界的 80 次非阻塞发送期间暂停调度，再恢复调度，使满时丢弃与计数可重复。这是构造测试条件的方法。实际负载仍需结合生产速率、消费预算、任务优先级和可接受丢弃来安排。

`taskYIELD()` 不保证低优先级 device 立即运行。等待应通过表达具体条件的阻塞或通知实现。owner 每轮限制入口、回复和数据处理量，并检查 deadline；tick 粒度会影响等待与超时观察。

## 观察复制和过载

按 [实验环境](01-environment.md)运行 `make -C platform freertos-test`，核对输入复制、满时行为及数据计数守恒。更改队列 item 或容量后，重新检查存储、所有权和收尾，不能只以编译成功作为依据。

队列还剩工作时，任务停止需要怎样处理？下一章看 [恢复与停止](03-recovery-stop.md)。共同接口定义见 [SDK 契约](https://xidianedu.cc/tech/platform/design/02-sdk-contract/)。
