# Lab 01: 手写 Python 时钟周期级 2D 脉动阵列模拟器

## 实验目标

本实验使用面向对象纯 Python 实现一个支持 **Weight-Stationary (WS)** 的 $4 \times 4$ 周期精确 2D 脉动阵列模拟器：
1. 模拟单个 PE 处理单元的乘累加（MAC）与水平/垂直寄存器传递；
2. 实现操作数水平倾斜（Skewing）注入与部分和垂直流水累加；
3. 与 NumPy 的 `np.dot(A, W)` 矩阵乘进行 Bit-Exact 级结果比对。

## 运行方法

```bash
chmod +x run_sim.sh
./run_sim.sh
```
