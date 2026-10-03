# 02 张量与矩阵计算核心

本章以 **2D 脉动阵列（Systolic Array）**为例，介绍处理单元与数据复用模式，再看向量处理引擎（VPU）和特殊函数单元（SFU）如何处理阵列不擅长的运算。

## 章节导航

1. [2D 脉动阵列数据通路与 PE 微架构](01-systolic-array-datapath.md)
2. [WS、OS 与 IS 三大数据复用模式深度对比](02-data-reuse-stationary-modes.md)
3. [向量计算引擎 VPU 微架构 (LayerNorm/Softmax)](03-vpu-vector-engine.md)
4. [特殊函数单元 SFU 与硬件查找表 (LUT)](04-sfu-activation-lut.md)
5. [计算核心工程问题排查与规避](05-compute-core-guide.md)
