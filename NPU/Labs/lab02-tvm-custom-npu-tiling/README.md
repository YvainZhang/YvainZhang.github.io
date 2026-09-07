# Lab 02: CPU 上的 NPU Tiling 容量与尾块预算

## 实验目标

使用 Python 标准库枚举 Tile，核算双份输入、INT32 累加器及工作区，并计算非整齐矩阵的尾块浪费。本实验不调用 TVM/MLIR，不生成 NPU 指令，不证明搬运完美重叠，也不预测真实时延。

## 运行

在仓库根目录执行，无需 NPU 或第三方依赖：

```bash
python3 NPU/Labs/lab02-tvm-custom-npu-tiling/npu_tiling_scheduler.py
python3 -B -m unittest discover -s NPU/Labs/lab02-tvm-custom-npu-tiling -p 'test_*.py' -v
```

## 模型契约

输入默认 INT8（1 B），累加器 INT32（4 B），双缓冲仅覆盖 A/B。输出和其他元数据由 `reserved_bytes` 计费；默认 16 KiB 是教学预留，不是通用常数。

`evaluate_tile()` 返回 SRAM 字节、Tile 调用数、有效/物理 MAC 和 padding 效率。`calculate_npu_tiling()` 在候选集中优先最小化物理 MAC，再减少 Tile 调用，最后减少 SRAM；这是可解释的排序规则，不是测得的最优调度。

对于 `M=130,N=70,K=129`、Tile `(64,64,128)`，应得到：64 KiB SRAM（含预留）、12 次调用、1,173,900 有效 MAC、6,291,456 物理 MAC、约 18.66% padding 效率。改变形状会改变选择，不再忽略 M/N/K。

## 没有覆盖的约束

该模型假设完整 Tile 执行，不支持尾部跳过；不建模 bank 端口、NoC 拥塞、指令开销、DMA 突发、功耗与跨 Tile 输入复用。容量可行不代表目标编译器一定接受，评分最高不代表实卡最快。

下一步把候选交给明确版本的目标后端，导出 layout 与分配报告，通过整数对拍后再计时。完整数值契约见 [量化 GEMM 案例](../../Case-Studies/04-quantized-gemm-contract.md)。
