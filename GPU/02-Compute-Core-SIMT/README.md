# 02 计算核心与 SIMT 执行模型

本模块深入剖析现代 GPU 最核心的执行引擎——**SM (Streaming Multiprocessor) / CU (Compute Unit)** 的微架构实现与 SIMT（Single Instruction, Multiple Threads）硬件调度机制。

## 章节导航

1. [SIMT 执行模型与线程映射](01-simt-execution-model.md)
2. [Warp 硬件调度器与 Scoreboard 依赖控制](02-warp-scheduler-scoreboard.md)
3. [寄存器堆物理组织与 Register Spill](03-register-file-allocation.md)
4. [ALU、FPU 与 Tensor Core 微架构](04-alu-fpu-tensor-core.md)
5. [分支分化 (Divergence) 与重聚机制](05-branch-divergence-reconvergence.md)
6. [计算核心工程问题排查与规避](06-core-engineering-guide.md)
