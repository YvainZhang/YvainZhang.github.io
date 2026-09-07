# 06 Scratchpad SRAM 物理容量与切块极限推演

## 1. 双缓冲 SRAM 容量与 Tile 尺寸定量计算

设片上 Scratchpad SRAM 总物理容量为 $C_{SRAM} = 2\text{ MB} = 2097152\text{ Bytes}$：
$$\text{Double Buffer 约束}: 2 \times (T_m \times T_k + T_k \times T_n + T_m \times T_n) \times 2\text{ Bytes (FP16)} \le 2097152$$

### 实例切分推导：
- 若取 $T_m = T_n = T_k = T$：
  $$2 \times 3 T^2 \times 2 \le 2097152 \implies 12 T^2 \le 2097152 \implies T \le 418$$
- 取硬件 64 对齐最大切分尺寸：$\mathbf{T_m = T_n = T_k = 384}$；
- 此时单组双缓冲占用 SRAM：$12 \times 384^2 = 1,769,472\text{ Bytes} \approx \mathbf{1.6875\text{ MB}}$（SRAM 空间利用率高达 **84.375%**）。
