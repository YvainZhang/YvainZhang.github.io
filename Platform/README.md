# 平台架构实践

Linux 系统机制与 RTOS 对照。

一个 buffer 提前归池的问题，往下追会涉及指针、对象寿命、异步完成和队列；继续追到错误回收与停止，就需要明确接口的所有权和退出责任。这里沿着这类具体问题展开，记录机制如何影响平台设计，以及怎样用实验核对判断。

## 从问题进入

| 当前问题 | 机制解释 | 连接的设计与案例 |
|---|---|---|
| 保存的 fd 或 buffer 还能继续使用吗？ | [fd 与对象寿命](mechanisms/03-fd-lifetime.md)、[队列与所有权](mechanisms/07-concurrency-ownership.md) | [SDK 契约](design/02-sdk-contract.md) |
| 有数据却等不到下一次事件，为什么？ | [事件、就绪与时间](mechanisms/06-events-time.md) | [停止时的排队请求](cases/01-stop-drain.md) |
| ping 已通，报文经过了哪条路径？ | [网络与 TAP](mechanisms/09-network-tap.md) | [环境与复现](guide/environment.md) |
| 设备已经解绑，旧 fd 为什么还能读？ | [内核设备与退出](mechanisms/10-kernel-lifetime.md) | [全生命周期评审](design/08-lifecycle-review.md) |
| 在途额度扩大四倍，代价是什么？ | [内存与性能](mechanisms/08-memory-performance.md) | [额度性能案例](cases/02-inflight-budget.md)、[资源预算](design/06-resource-budget.md) |
| 业务移到 RTOS，哪些保证还应成立？ | [SDK 契约](design/02-sdk-contract.md) | [Linux / FreeRTOS 对照](design/03-linux-freertos.md)、[恢复案例](cases/03-cross-runtime-recovery.md) |

## 按依赖阅读

刚接触 Linux 系统编程，可以从 [C 对象与 ABI](mechanisms/01-c-abi.md)、[构建与 ELF](mechanisms/02-build-elf.md)开始，再读 fd、IO、进程与事件。已有 C 和嵌入式经验，可以从 fd 与生命周期进入，按链接补前置知识。

系统机制章节讲对象和执行时序；平台设计章节讨论接口、预算、平台差异与演进；工程案例将这些机制放回完整问题。各章给出源码位置、操作步骤、预期现象与适用条件。

实验载体包括纯 C 异步核心、Linux 与 FreeRTOS 运行时、TAP 链路程序和专用 QEMU 设备模块。源码下载、依赖版本及许可见 [源码页](reference/source.md)，执行入口见 [环境准备](guide/environment.md)。

## 阅读实验结果

宿主 Linux / FreeRTOS POSIX port 的结果用于核对业务契约；QEMU 软件设备用于观察内核对象和解绑。真实 MCU 的中断、DMA、功耗及最坏时延需要在目标平台测量。历史性能样本与当前源码回归分别记录，见 [验证范围](reference/verification.md)。

## 相邻专题

- [Wi-Fi 系统知识库](https://xidianedu.cc/tech/wifi/)：把所有权、背压与恢复放到驱动、总线和固件的收发路径中。
- [RTOS 系统知识库](https://xidianedu.cc/tech/rtos/)：进一步查看任务、队列、通知、互斥和内核调度机制。
- [SoC 系统知识库](https://xidianedu.cc/tech/soc/)：进一步查看启动、设备树、缓存、DMA 和软硬件边界。
- [返回博客技术总览](https://xidianedu.cc/tech/)。
