# 05 分支分化 (Divergence) 与重聚机制

## 1. 分支分化 (Branch Divergence) 硬件原理

在 SIMT 模型中，Warp 内 32 个线程共享同一个指令计数器（PC）。当遇到条件分支语句时：

```mermaid
graph TD
    Branch["分支判定: if (threadIdx.x < 16)"]
    Branch -->|Thread 0~15 (True)| PathTrue["执行 True 分支<br/>Active Mask = 0x0000FFFF (16 线程活跃, 16 线程空转)"]
    PathTrue -->|串行执行| PathFalse["执行 False 分支<br/>Active Mask = 0xFFFF0000 (16 线程活跃, 16 线程空转)"]
    PathFalse --> Reconverge["重聚点 (Reconvergence Point)<br/>Active Mask = 0xFFFFFFFF (全量 32 线程恢复并发)"]
```

- **算力开销**：当分支分化发生时，总执行耗时为两条分支耗时之和（$T = T_{true} + T_{false}$），单 Warp 有效算力损失达 50%。

---

## 2. 独立线程调度 (Independent Thread Scheduling, ITS)

现代 GPU 架构（Volta 之后）引入了 ITS 机制：
- 每个线程拥有独立的 **Program Counter (PC) 与 Call Stack**；
- 硬件 SIMT 调度器可以根据指令依赖情况，交织执行不同分支中的子指令，从硬件层面杜绝了线程锁步死锁问题（如 Warp 内互斥锁）。
