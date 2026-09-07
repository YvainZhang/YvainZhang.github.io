# 03 向量计算引擎 VPU 微架构 (LayerNorm/Softmax)

## 1. 为什么单独需要 VPU (Vector Processing Unit)

脉动阵列极其擅长 2D 矩阵乘法，但对 1D 向量操作（如 LayerNorm、Softmax、GELU、RMSNorm、RoPE 旋转位置编码）效率极低：
- **VPU 微架构**：包含高位宽 SIMD 向量执行单元（如 512-bit ~ 2048-bit 向量流水线）、向量寄存器堆（Vector RF）以及跨 Lane 归约加法树（Reduction Tree）。
- **紧耦合协同**：脉动阵列输出的矩阵乘结果可直接通过片上内部流线送入 VPU，无需写回外部显存即可完成 `MatMul -> LayerNorm -> Activation` 链式执行。
