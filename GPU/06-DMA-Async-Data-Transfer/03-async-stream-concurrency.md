# 03 异步 Stream 并发与 CUDA Graph 硬件执行

## 1. 多 Stream 硬件队列与依赖管理

- **Stream 硬件本质**：对应 GPU Command Processor 内部的一个独立硬件指令队列。
- **Event 同步机制**：通过硬件标记寄存器（Syncpoint / Fence）实现不同 Stream 之间的细粒度依赖同步（`cudaStreamWaitEvent`）。

---

## 2. CUDA Graph 硬件执行优化

在传统迭代下发中，每次小算子 Launch 都有 ~5-10 $\mu s$ 的 CPU 驱动下发开销（CPU Launch Bound）：
- **CUDA Graph 机制**：将整个模型的计算图在驱动层提前烘焙（Instantiate）为一张静态依赖图。
- **硬件执行**：一次性将整张图的执行描述符压入硬件队列，由 GPU 硬件调度器自主按拓扑顺序触发执行，消除一切 CPU 介入时延。
