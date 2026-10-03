# 03 Timeline 性能 Trace 分析与 MLPerf 基准测试

## 1. Timeline Trace 时间线可视化分析

在性能分析工具（如 Profiler）中观察三条核心时间线轨道的重叠情况：
1. **DMA Timeline 轨道**：Tensor DMA 数据搬运占用区间。
2. **Systolic Timeline 轨道**：脉动阵列乘加计算区间。
3. **VPU Timeline 轨道**：向量单元激活与归一化计算区间。
- **观察重点**：标出阵列空闲区间，检查是否在等待 DMA、VPU 或同步事件。结合该模型的算子组成和设备资源判断重叠空间；持续满载不是所有负载都能达到的统一标准。
