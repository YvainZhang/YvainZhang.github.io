# 量化 GEMM：数值契约、SRAM、DMA 与结果验证

## 明确范围

使用教学型 NPU：INT8 输入和权重、INT32 累加、显式 SRAM，DMA 与矩阵引擎可独立执行。它不是所有 NPU 的统一 ISA，也不是厂商可加载模型格式。取 `M=130,N=70,K=129`，刻意保留三个方向的尾块。

## 1. 固定量化语义

仿射量化为 `real = scale*(q-zero_point)`。每个张量记录 dtype、scale、zero-point、量化轴、rounding 和饱和范围。本例逐张量 scale，INT8 范围 `[-128,127]`；对称 `[-127,127]` 是另一种显式约定，不能静默混用。

```text
acc[m,n] = sum_k ((Aq[m,k]-za) * (Bq[k,n]-zb))
Yq[m,n] = saturate(round(acc[m,n] * sa*sb/sy) + zy)
```

[ONNX QuantizeLinear](https://onnx.ai/onnx/operators/onnx__QuantizeLinear.html) 定义舍入与饱和，[QLinearMatMul](https://onnx.ai/onnx/operators/onnx__QLinearMatMul.html) 提供矩阵乘法量化契约。导入时还需记录 opset，确认后端支持的粒度与形状；能读取 ONNX 不等于完整执行该图。

bias 应对齐到累加器尺度；逐输出通道量化会改变每列重缩放参数。硬件以整数 multiplier/shift 近似比例时，需独立量化这层误差，不能将所有 mismatch 都归为 INT8 正常误差。

## 2. Padding 必须代表实数零

非对称量化的实数零对应 zero-point，而非整数 0。K=129 补齐到 256 时，无效 A/B 按各自 zero-point 填充或使用等价 mask，否则补出的项会污染有效输出。

M/N 额外输出要 mask 掉。逻辑 N=70 不代表物理行跨度是 70 B，布局可能补到 128 B；logical shape、physical shape、stride 和对齐要分别记录。

## 3. 切块与容量预算

取 `Tm=Tn=64,Tk=128`，双份输入、单份累加器，另保留 16 KiB 给输出、scale、描述符和对齐：

```text
S_input = 2*(64*128 + 128*64) = 32768 B
S_acc   = 4*64*64             = 16384 B
S_total = 32768+16384+16384   = 65536 B = 64 KiB
```

预留量是模型参数，不是普遍足够的常数。SRAM 总量刚好装得下，也未证明 bank 分区、指令区与并发任务允许该布局。

分块数 `ceil(130/64)=3`、`ceil(70/64)=2`、`ceil(129/128)=2`，共 12 次 Tile 乘加。若每块按完整尺寸执行，有效 MAC 为 1,173,900，物理槽位 6,291,456，形状有效比例约 18.66%。它不是 PE busy 或 MFU；硬件可跳过尾部时分母要重新定义。

最大 Tile 不必最快：尾块浪费可能使小 Tile 更有利；小 Tile 又增加启动、描述符与同步开销，必须进一步实测。

## 4. 跨 K 保留累加器

同一输出 Tile 在第一 K 块清零 INT32 accumulator，后续继续累加，最后才做 bias、激活、重缩放和回写。每个 K 块都先压回 INT8 会改变舍入语义。

若 accumulator 放不下，要明确 INT32 partial sum 的 spill/reload，并将流量计入成本模型。不能将其藏在“融合”标签里。

溢出也要检查：仿射 INT8 去零点值的最坏幅度可到 255，乘积上界 65025。以 `K*65025+|bias_int|` 的保守界检查 INT32。本例 K=129 不构成该界下的溢出，但不能推广到任意 K。

## 5. DMA 与同步

行主序 A 地址为 `base_A+(m*lda+k)*elem_bytes`，B 为 `base_B+(k*ldb+n)*elem_bytes`。描述符区分行长、行数和字节 stride，不能把元素跨度写入按字节计数的字段。

依赖为输入完成 → 本 K 块计算 → 后续 K 累加 → 后处理 → 输出写回完成。双缓冲槽必须在最后一次读取后才覆盖，见 [双缓冲状态与时间预算](../03-Scratchpad-OnChip-Buffer/02-ping-pong-double-buffering.md)。

## 6. 四级验证定位首次偏差

| 层级 | 比较对象 | 定位范围 |
| --- | --- | --- |
| 浮点参考 | 模型输出和业务指标 | 模型、预处理 |
| 整数量化参考 | 相同 scale/rounding 的数学结果 | 校准、饱和与量化误差 |
| 切块模型 | 对完整整数 GEMM | padding、layout、K 累加和尾块 |
| 后端/实卡 | 对切块参考 | lowering、DMA、事件和硬件算术 |

保存首次偏差张量与坐标。误差小不等于业务质量过关，还需任务数据集与门限。随机权重量化导出 JSON/bin 只能验证教学格式，不能证明真实部署。

## 7. 部署前追问

- 是否有 CPU fallback？新增多少布局转换和边界搬运？
- 动态 shape 是否在编译 profile 内？超范围是拒绝、重编译还是 fallback？
- 产物是否记录架构、编译器版本、布局、量化参数与输入契约？
- 冷启动、加载、稳态执行和后处理是否分别测量？
- 速度比较前是否通过相同形状、精度和布局的正确性测试？

[Tiling 预算实验](../Labs/lab02-tvm-custom-npu-tiling/README.md) 可在 CPU 验证容量与尾块，不连接 TVM 后端，也不预测真实时延。编译器层可参考 [MLIR Linalg](https://mlir.llvm.org/docs/Dialects/Linalg/)，将数学等价、合法调度与目标指令选择分开验证。
