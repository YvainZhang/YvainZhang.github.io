# Lab 01: CUDA GEMM 算子极致调优

## 实验目标

本实验通过由浅入深的四个阶段，实现并优化高性能单精度通用矩阵乘（SGEMM, $C = A 	imes B$）：
1. **阶段 1 (Naive)**：直接使用全局内存读取，验证基本算法正确性与显存带宽瓶颈。
2. **阶段 2 (Shared Memory Tiling)**：引入二维分块，将数据缓存在片上 SRAM，大幅降低全局显存访问量。
3. **阶段 3 (Bank Conflict Elimination)**：分析 32-Bank 映射公式，通过添加 1 列 Padding 消除 Bank 冲突。
4. **阶段 4 (Double Buffering & Vectorized Load)**：使用 `float4` 向量化读取与寄存器双缓冲隐藏访存时延。

---

## 目录结构与源文件

- [`Makefile`](Makefile)：NVCC 编译配置文件。
- [`gemm_kernels.cuh`](gemm_kernels.cuh)：包含 V1 到 V3 的 CUDA 算子实现。
- [`main.cu`](main.cu)：基准评测驱动程序。

---

## 编译与运行

```bash
cd Labs/lab01-cuda-gemm-tuning
make
./gemm_bench
```
