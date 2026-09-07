# 06 计算核心工程问题排查与规避

## 1. 核心常见问题与排查表

| 故障/性能现象 | 硬件根因分析 | 原厂推荐规避方案 |
| :--- | :--- | :--- |
| **Warp Stall: Long Scoreboard** | 大量等待全局显存或 L2 读请求返回 | 增加数据预取、提高 Tiling 块大小、提升计算访存比 |
| **Warp Stall: Short Scoreboard** | 寄存器读写局部冲突或 Shared Memory 等待 | 循环展开（Loop Unrolling）、调整指令发射顺序消除 RAW 依赖 |
| **SM Occupancy 低** | 线程块请求的寄存器或 Shared Memory 超过单个 SM 限制 | 使用 `__launch_bounds__` 限制寄存器上限，或减小 Block 大小 |
| **计算结果溢出产生 NaN/Inf** | 低精度（FP8/FP16）在 Tensor Core 累加时未采用 FP32 累加器 | 强制指定 Tensor Core Accumulator 为 FP32 精度 |

---

## 2. 指令级并行度 (ILP) 极致调优代码范式

```cuda
// 优化前：串行依赖 (RAW Hazard 导致 Scoreboard 阻塞)
float a = data[i];
float b = a * 2.0f;
float c = b + 1.0f;

// 优化后：展开双路独立计算，提升流水线发射吞吐 (ILP 优化)
float a0 = data[i];
float a1 = data[i+1];
float b0 = a0 * 2.0f;
float b1 = a1 * 2.0f;
float c0 = b0 + 1.0f;
float c1 = b1 + 1.0f;
```
