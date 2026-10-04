# Linux 系统实践

从 fd、buffer 和事件处理中的具体问题出发，沿着用户态、网络与驱动边界，整理 Linux 的机制、时序和工程取舍。

## 从问题进入

| 问题 | 机制 | 实践与设计 |
| --- | --- | --- |
| 保存的 fd 或 buffer 还能继续使用吗？ | [fd 与对象寿命](mechanisms/03-fd-lifetime.md)、[队列与所有权](mechanisms/07-concurrency-ownership.md) | [异步 SDK 运行时](runtime/01-async-sdk.md) |
| 有数据却等不到下一次事件，为什么？ | [事件、就绪与时间](mechanisms/06-events-time.md) | [停止时的排队请求](cases/01-stop-drain.md) |
| ping 已通，报文经过了哪条路径？ | [网络与 TAP](mechanisms/09-network-tap.md) | [环境与复现](guide/environment.md) |
| 设备已经解绑，旧 fd 为什么还能读？ | [内核设备与退出](mechanisms/10-kernel-lifetime.md) | [启动与硬件边界](hardware/01-boot-hardware.md) |
| 在途额度扩大四倍，代价是什么？ | [内存、调度与性能](mechanisms/08-memory-performance.md) | [额度性能案例](cases/02-inflight-budget.md) |
| exec 以后，子进程为什么拿不到通道？ | [构建与 ELF](mechanisms/02-build-elf.md)、[fd 引用](mechanisms/03-fd-lifetime.md) | [描述符继承案例](cases/04-exec-fd.md) |

## 按依赖阅读

先读 [C 对象与 ABI](mechanisms/01-c-abi.md)、[构建与 ELF](mechanisms/02-build-elf.md)，再看 fd、IO、进程和事件。已有系统编程经验，可以从当前问题进入，沿章节链接补前置知识。

异步 SDK 串起复制、接受、完成、超时和停止；TAP 用于观察网络路径与背压；QEMU 软件设备用于观察内核引用与解绑。各章给出源码位置、实验命令和结果边界。[环境准备](guide/environment.md)说明容器、工具链与专用 VM 的使用方法。

## 从机制走到平台设计

接口保证、资源预算、交付和演进在 [平台架构实践](https://xidianedu.cc/tech/platform/) 中展开。RTOS 的任务、队列、通知和实际运行步骤有独立入口：[RTOS 系统知识库](https://xidianedu.cc/tech/rtos/) 与 [FreeRTOS 异步 SDK 实践](https://xidianedu.cc/tech/rtos/Practice/)。

[公开源码与许可](https://xidianedu.cc/tech/platform/reference/source/) · [验证范围与记录](https://xidianedu.cc/tech/platform/reference/verification/) · [博客技术总览](https://xidianedu.cc/tech/)
