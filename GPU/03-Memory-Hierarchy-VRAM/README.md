# 03 显存系统与存储层次

本模块全方位剖析 GPU 芯片从**片上 SRAM（寄存器堆、Shared Memory、L1 Cache）到片上大容量 L2 Cache，再到片外高带宽显存（HBM3e / GDDR7）**的完整存储金字塔体系。

## 学习目标

- 掌握 HBM3e 3D TSV 堆叠封装与 GDDR7 PAM3 物理层架构。
- 深入剖析统一 L1/Shared Memory SRAM 组织结构与 L2 Cache 切片划分。
- 精确掌握 Shared Memory 32-Bank 冲突消除（Padding 算法）与全局显存访存合并（Coalescing）。
- 理解 GPU Cache 弱一致性模型与下沉至 L2 的硬件原子操作 RMW 电路。
- 掌握现场显存 ECC 故障诊断、Row Remapping 修复与性能调优。

## 章节导航

1. [HBM3e 与 GDDR7 显存物理层架构](01-vram-hbm-gddr.md)
2. [L2 Cache 切片与 Unified Shared Memory / L1](02-l2-l1-shared-memory.md)
3. [Shared Memory 32-Bank 冲突消除与访存合并](03-bank-conflict-coalescing.md)
4. [Cache 一致性协议与硬件原子操作](04-memory-coherency-consistency.md)
5. [存储系统工程问题排查与规避](05-memory-engineering-guide.md)
6. [显存系统故障案例与 Bank 冲突现场排查](06-cases-debug.md)
7. [显存层级容量、时延与 Bank 冲突定量计算](07-engineering-analysis.md)
