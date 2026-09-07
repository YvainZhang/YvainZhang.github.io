# 02 NSight 性能计数器体系与 Warp Stall 根因分析

## 1. NSight Compute 核心硬件采样指标

| 指标 (Metric) | 含义 | 调优健康阈值 |
| :--- | :--- | :--- |
| **`sm__throughput.avg.pct_of_peak_sustained_active`** | SM 计算核心实际算力利用率 | $> 75\%$ |
| **`dram__throughput.avg.pct_of_peak_sustained_active`** | HBM / GDDR 显存物理带宽利用率 | $> 80\%$ |
| **`sm__warps_active.avg.pct_of_peak_sustained_active`** | 理论 SM Warp 活跃度 (Occupancy) | $> 50\%$ |

---

## 2. 常见 Warp Stall 原因分类与排查

- **`Stall Long Scoreboard`**：等待全局显存数据返回。 $\rightarrow$ 增加流水线预取，增加并发线程数隐藏延迟。
- **`Stall Short Scoreboard`**：寄存器 RAW 依赖。 $\rightarrow$ 展开循环增加指令级并行（ILP）。
- **`Stall Barrier`**：Warp 在 `__syncthreads()` 等待同 Block 其他线程。 $\rightarrow$ 减少不必要的同步屏障。
