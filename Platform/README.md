# 平台架构实践

从接口责任、资源预算与退出边界出发，记录系统机制如何影响平台设计。一个 buffer 提前归池的问题，最终会落到复制、借用、完成和回收的契约；一个停止遗漏通知的问题，则会落到接受边界与结果义务。

## 架构推演

| 具体矛盾 | 深入分析 | 输出的设计决定 |
| --- | --- | --- |
| 平均能力够，突发仍撑满队列 | [负载包络、容量与 admission](design/09-capacity-admission.md) | 容量 / 时延边界、拒绝与降级 |
| 本地只通知一次，设备却执行两次 | [故障模型与恢复边界](design/10-failure-recovery.md) | 结果未知、幂等身份、重试与恢复负责人 |
| 新增零拷贝，旧接口怎样继续工作 | [兼容性与所有权演进](design/11-contract-evolution.md) | API / ABI / wire 承诺、归还协议与支持矩阵 |

这些章节沿现有 SDK 向产品约束推演，给出候选、代价和撤回条件。算例不作为产品指标；operation 去重、v2 与借用模式尚未实现。

## 独立的系统实践

| 专题 | 阅读主线 | 实验入口 |
| --- | --- | --- |
| [Linux 系统实践](https://xidianedu.cc/tech/linux/) | fd、IO、进程、事件、并发、网络与驱动退出 | [Linux 环境](https://xidianedu.cc/tech/linux/guide/environment/) |
| [RTOS 系统知识库](https://xidianedu.cc/tech/rtos/) | 调度、中断、同步、FreeRTOS 与 Zephyr | [FreeRTOS 工程实践](https://xidianedu.cc/tech/rtos/Practice/) |

两条路线分别展开系统机制与复现步骤。这里讨论它们需要共同回答的接口保证、容量、故障、交付与演进问题。

## 从问题到设计判断

| 问题 | 设计章节 | 具体依据 |
| --- | --- | --- |
| 提交成功以后，数据和结果归谁负责？ | [SDK 需求与契约](design/02-sdk-contract.md) | [Linux 所有权](https://xidianedu.cc/tech/linux/mechanisms/07-concurrency-ownership/)、[FreeRTOS 队列](https://xidianedu.cc/tech/rtos/Practice/02-queue-owner/) |
| 同一业务换一个系统，还应保留哪些保证？ | [运行时边界](design/03-linux-freertos.md) | [跨运行时恢复](cases/03-cross-runtime-recovery.md) |
| 吞吐提升的内存与停止代价是什么？ | [资源预算](design/06-resource-budget.md) | [Linux 额度性能案例](https://xidianedu.cc/tech/linux/cases/02-inflight-budget/) |
| 实验通过以后，交付还差哪些证据？ | [可靠性与交付](design/04-reliability-delivery.md) | [验证范围](reference/verification.md) |
| 哪些负载适合当前平台？ | [芯片与平台选型](design/05-platform-selection.md) | 资源、时延、驱动与生命周期约束 |
| 新需求加入时，怎样控制代价？ | [复杂度与演进](design/07-complexity-evolution.md) | [全生命周期评审](design/08-lifecycle-review.md) |

## 源码和结果

实验采用纯 C core 与分别实现的 runtime，共用一份 [公开源码快照](reference/source.md)。Linux、FreeRTOS、TAP 与 QEMU 各有执行入口，见 [环境索引](guide/environment.md)。

宿主 port 的结果支持功能与契约核对，QEMU 软件设备支持对象寿命观察。真实硬件的中断、DMA、功耗与最坏时延按目标平台测量；历史性能样本和当前源码回归分别记录。

[Wi-Fi 系统知识库](https://xidianedu.cc/tech/wifi/) · [SoC 系统知识库](https://xidianedu.cc/tech/soc/) · [博客技术总览](https://xidianedu.cc/tech/)
