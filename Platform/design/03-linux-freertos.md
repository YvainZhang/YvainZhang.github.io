# Linux 与 FreeRTOS：共用业务契约，分别实现运行机制

同一套异步请求逻辑需要运行在 Linux 和 FreeRTOS 上。容易先想到把 thread、mutex、event 封装成一层统一 API，随后却发现通知、时间和退出的差异仍然泄漏出来。更稳定的边界来自请求语义：什么算接受，何时超时，恢复如何隔离旧回复，停止需要交付哪些结果。

先阅读[SDK 契约](02-sdk-contract.md)和[事件与时间](https://xidianedu.cc/tech/linux/mechanisms/06-events-time/)。本例采用官方 FreeRTOS V11.1.0 的 POSIX port，运行真实任务、队列与调度器；底层仍使用宿主能力。实现与版本见[源码入口](../reference/source.md)。

## 分层以后，各层负责什么

```text
Linux: API → mutex/ingress → eventfd → pthread owner → core → seqpacket/exec
RTOS : API → mutex/queue   → notification → owner task → core → task/queues
共同 : 复制、额度、身份、deadline、admission、终态、恢复和停止
```

core 没有 OS 头文件，以输入事件推进状态，输出发送、通知、重建和关闭动作。runtime 把 OS 机制转成事件，并执行这些动作。backend 再落实设备能力与通信。

| 责任 | Linux runtime | FreeRTOS runtime | 必须一致的结果 |
| --- | --- | --- | --- |
| 单写者 | pthread owner | owner task | core 不被多个执行者同时修改 |
| 输入同步 | mutex、固定入口数组 | mutex、固定 item queue | payload 已复制；满时明确拒绝 |
| 唤醒 | eventfd、epoll | task notification | 通知提示检查真实队列 |
| 时间 | CLOCK_MONOTONIC、timerfd | tick 换算 | 按 deadline 决定终态 |
| 后端 | 独立进程、seqpacket | device task、queues | 完整身份、协议与能力 |
| 退出 | 协作停止、waitpid、join | 停止标志、完成信号、自删 | 所有访问结束后释放实例 |

## 分别核对运行机制

[Linux 异步 SDK](https://xidianedu.cc/tech/linux/runtime/01-async-sdk/)展开入口复制、eventfd / epoll、启动发布与进程收尾。[FreeRTOS 工程实践](https://xidianedu.cc/tech/rtos/Practice/)展开队列 item、任务通知、调度、恢复与任务退出。

两端都把通知当作检查真实工作集合的提示。处理预算限制正常循环的单轮工作量；停止时的最终收尾仍要覆盖全部有界剩余集合。共同语义不要求相同调度顺序，但要求结果义务一致。

## 恢复时序保留共同语义

```text
收到 recover
  → 关闭 admission
  → 终结旧 generation 的请求
  → generation 增加，重建 backend
  → READY 后允许新工作
  → 旧 generation 回复到达时拒绝匹配
```

Linux 重建子进程和 IPC 通道，隔离旧通信。FreeRTOS 的旧排队回复仍可能被取出，由完整身份检查排除。两端都需要处理重建失败：进入 FAILED、保留诊断信息，等待显式决策。本例没有自动无限恢复。

详细故障过程见[跨运行时恢复案例](../cases/03-cross-runtime-recovery.md)。

## 运行同一组语义测试

先按[FreeRTOS 实验环境](https://xidianedu.cc/tech/rtos/Practice/01-environment/)获取并校验依赖，再在无网络的专用工具容器项目根目录执行：

```sh
make -C platform core-test freertos-test
```

依赖脚本校验固定版本。FreeRTOS 测试把同一组 core 向量放入实际任务执行，并覆盖复制、队列满、恢复、多实例与停止。Linux 和 FreeRTOS 可以具有不同的任务交错，比较应落在终态、计数和退出义务上。

## 换成 MCU port 后重新验证什么

POSIX port 的结果支持宿主功能与语义验证。迁移到 MCU 时，重新核对 tick 分辨率、FromISR 路径、中断优先级、临界区、任务栈、heap、DMA/cache 和设备完成。

host 上的 heap_free 与栈水位无法覆盖全部宿主 pthread 开销；延迟分位也不能作为 MCU 最坏执行时间。把 port、板级配置和真实设备的测试纳入[交付清单](04-reliability-delivery.md)，共同 core 的复用才有清楚的验证边界。
