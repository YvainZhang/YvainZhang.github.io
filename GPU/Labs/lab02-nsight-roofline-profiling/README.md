# Lab 02: NSight Roofline 实战分析

## 实验目标

使用 NVIDIA Nsight Compute (`ncu`) 对典型 Memory-Bound 算子（VectorAdd）与 Compute-Bound 算子（HeavyMath）进行硬件采样，绘制 Roofline 模型图并分析算术强度与瓶颈定位。

## 实验步骤

```bash
make
chmod +x run_ncu_roofline.sh
./run_ncu_roofline.sh
```
