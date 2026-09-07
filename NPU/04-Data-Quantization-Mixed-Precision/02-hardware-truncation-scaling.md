# 02 硬件定点截断、舍入与动态 Scaling 单元

## 1. 硬件舍入模式 (Rounding Modes)

乘加完成后的高精度累加值必须压缩回低比特存储格式：
- **Round-to-Nearest-Even (最近偶数舍入)**：IEEE 754 标准，消除统计偏差。
- **Stochastic Rounding (随机舍入)**：引入片上伪随机数发生器（PRNG），以概率 $P = \frac{x - \lfloor x \rfloor}{\text{LSB}}$ 决定进位，在大模型极低比特训练中有效防止梯度下溢消失。
