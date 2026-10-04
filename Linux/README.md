# Linux 系统实践

从 fd、buffer 和事件处理中的具体问题出发，沿着用户态、网络与驱动边界，整理 Linux 的机制、时序和工程取舍。

## 系统设计进阶

已有系统编程经验，可以从下面四个问题进入。每章以现有实现为起点，展开并发推演、候选方案、成本与验证条件。

| 设计问题 | 进阶章节 | 需要形成的判断 |
| --- | --- | --- |
| 热点 IO 不断到达，控制还能及时处理吗？ | [事件循环调度与背压](advanced/01-reactor-scheduling.md) | 数量 / 时间预算、ready 队列、控制与数据隔离 |
| CPU 不忙，p99 为什么恶化？ | [沿请求路径定位等待](advanced/02-tail-latency.md) | 统计边界、分段时间、调度证据与负载模型 |
| 一个实例过载，为什么其它实例也变慢？ | [资源隔离与压力](advanced/03-resource-isolation.md) | 进程边界、CPU / 内存预算和退出集合 |
| 引用还在，怎样证明驱动已经停止访问？ | [驱动静止与退出证明](advanced/04-driver-quiescence.md) | 撤销许可、同步活动、最后引用与硬件依赖 |

[异步 SDK](runtime/01-async-sdk.md)、[额度基准](cases/02-inflight-budget.md)和[设备寿命](mechanisms/10-kernel-lifetime.md)提供代码与历史实验依据。进阶正文明确区分当前实现、推导算例和待执行对照；性能定位、cgroup 与真实 DMA 的新实验结果尚未产生。

## 机制与工程案例

| 问题 | 机制 | 实践与设计 |
| --- | --- | --- |
| 保存的 fd 或 buffer 还能继续使用吗？ | [fd 与对象寿命](mechanisms/03-fd-lifetime.md)、[队列与所有权](mechanisms/07-concurrency-ownership.md) | [异步 SDK 运行时](runtime/01-async-sdk.md) |
| 有数据却等不到下一次事件，为什么？ | [事件、就绪与时间](mechanisms/06-events-time.md) | [停止时的排队请求](cases/01-stop-drain.md) |
| ping 已通，报文经过了哪条路径？ | [网络与 TAP](mechanisms/09-network-tap.md) | [环境与复现](guide/environment.md) |
| 设备已经解绑，旧 fd 为什么还能读？ | [内核设备与退出](mechanisms/10-kernel-lifetime.md) | [启动与硬件边界](hardware/01-boot-hardware.md) |
| 在途额度扩大四倍，代价是什么？ | [内存、调度与性能](mechanisms/08-memory-performance.md) | [额度性能案例](cases/02-inflight-budget.md) |
| exec 以后，子进程为什么拿不到通道？ | [构建与 ELF](mechanisms/02-build-elf.md)、[fd 引用](mechanisms/03-fd-lifetime.md) | [描述符继承案例](cases/04-exec-fd.md) |

## 按依赖阅读

需要补系统编程基础时，先读 [C 对象与 ABI](mechanisms/01-c-abi.md)、[构建与 ELF](mechanisms/02-build-elf.md)，再看 fd、IO、进程和事件。已有系统编程经验，可以从当前问题进入，沿章节链接补前置知识。

异步 SDK 串起复制、接受、完成、超时和停止；TAP 用于观察网络路径与背压；QEMU 软件设备用于观察内核引用与解绑。各章给出源码位置、实验命令和结果边界。[环境准备](guide/environment.md)说明容器、工具链与专用 VM 的使用方法。

## 从机制走到平台设计

接口保证、资源预算、交付和演进在 [平台架构实践](https://xidianedu.cc/tech/platform/) 中展开。RTOS 的任务、队列、通知和实际运行步骤有独立入口：[RTOS 系统知识库](https://xidianedu.cc/tech/rtos/) 与 [FreeRTOS 异步 SDK 实践](https://xidianedu.cc/tech/rtos/Practice/)。

[公开源码与许可](https://xidianedu.cc/tech/platform/reference/source/) · [验证范围与记录](https://xidianedu.cc/tech/platform/reference/verification/) · [博客技术总览](https://xidianedu.cc/tech/)
