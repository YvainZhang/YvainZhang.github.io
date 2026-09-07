# 04 特殊函数单元 SFU 与硬件查找表 (LUT)

## 1. 非线性激活函数硬件实现

- **查找表 (Look-Up Table, LUT)**：
  - 针对 Sigmoid、Tanh、GELU、Exp 函数，在片上配置由小容量双端口 SRAM 构成的硬件 LUT。
  - **分段线性插值（Piecewise Linear Approximation, PLA）**：硬件取出区间端点值 $y_0, y_1$ 及斜率 $k$，单周期计算 $y = y_0 + k \times (x - x_0)$。
- **高精度多项式逼近**：使用 3 阶/5 阶泰勒/切比雪夫多项式硬件计算流水线，保证浮点计算精度与 PyTorch CPU 误差 $< 10^{-4}$。
