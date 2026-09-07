# 01 硬件算力利用率 (MFU / HFU) 理论模型与推导

## 1. MFU (Model FLOPs Utilization) 公式定义

$$\text{MFU} = \frac{\text{模型理论所需浮点运算量 (FLOPs/step)}}{\text{硬件标称峰值算力 (Peak FLOPS)} \times \text{实际单步耗时 (Seconds)}}$$

- **原厂工程基准**：
  - 高性能 LLM 训练在 NPU 上 MFU 达到 **50% ~ 65%** 即可判定为极高水平。
  - 大尺寸 GEMM 算子 MFU 达到 **85% ~ 92%**。
