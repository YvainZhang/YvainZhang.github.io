# 02 CPU 与处理器架构

本模块从软件可见的指令集出发，进入流水线、特权级、异常和多核系统。重点不是记忆 ARM 或 RISC-V 寄存器名称，而是解释一条指令怎样执行、状态怎样切换，以及并发为何会暴露单核程序中不存在的问题。

## 章节

1. [ISA、寄存器与流水线](01-isa-pipeline.md)
2. [特权级、异常与中断入口](02-privilege-exception.md)
3. [多核、原子操作与内存序](03-smp-memory-order.md)
4. [启动、性能与故障分析](04-cases-debug.md)
5. [工程推演与答案](05-engineering-analysis.md)
6. [ARM/RISC-V 异常向量与上下文保存](06-exception-vector-context.md)
7. [原子指令、Cache 与 TLB 维护](07-atomic-cache-tlb.md)
8. [处理器工程问题与规避](08-processor-engineering-guide.md)
