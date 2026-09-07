# 04 性能调优原厂工程检查清单

## 1. 算子极限性能达成 8 步法检查清单

- [ ] **Step 1 (算子融合)**：是否已将连续的 Elementwise 算子合并至前置 MatMul 输出阶段？
- [ ] **Step 2 (访存对齐)**：Global Memory 读写是否满足 128-bit 向量化合并（`float4`）？
- [ ] **Step 3 (SRAM 冲突)**：Shared Memory 访问是否存在 Bank Conflict？是否已添加 Padding？
- [ ] **Step 4 (Tensor Core)**：矩阵维度是否对齐到 16 的倍数以完整利用 Tensor Core MMA 硬件？
- [ ] **Step 5 (Double Buffering)**：是否采用异步 Copy（`cp.async`）实现计算与数据搬运的流水线重叠？
- [ ] **Step 6 (寄存器控制)**：每线程寄存器用量是否控制在阈值内，杜绝任何 Register Spill？
- [ ] **Step 7 (Occupancy 权衡)**：SM 活跃 Warp 数量是否足以完全隐藏指令延迟？
- [ ] **Step 8 (Roofline 验证)**：实际测得的 TFLOPS 或带宽是否达到硬件理论峰值的 80% 以上？
