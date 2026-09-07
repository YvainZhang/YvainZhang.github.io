# Lab 02: 基于 TVM 思想的自定义 NPU Tiling 调度器

## 实验目标

根据硬件物理约束（片上 Scratchpad SRAM 容量上限、Double Buffering 双缓冲要求），编写启发式循环切块搜索算法，计算最佳 $(T_m, T_n, T_k)$ 矩阵切分参数，保证 DMA 搬运与阵列计算的完美重叠。
