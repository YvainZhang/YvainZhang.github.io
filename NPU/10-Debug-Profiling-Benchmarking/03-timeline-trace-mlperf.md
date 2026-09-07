# 03 Timeline 性能 Trace 分析与 MLPerf 基准测试

## 1. Timeline Trace 时间线可视化分析

在性能分析工具（如 Profiler）中观察三条核心时间线轨道的重叠情况：
1. **DMA Timeline 轨道**：Tensor DMA 数据搬运占用区间。
2. **Systolic Timeline 轨道**：脉动阵列乘加计算区间。
3. **VPU Timeline 轨道**：向量单元激活与归一化计算区间。
- **健康标准**：脉动阵列轨道持续处于 100% 满载填满状态，DMA 搬运与 VPU 计算均被完全隐藏在脉动计算阴影之下。
