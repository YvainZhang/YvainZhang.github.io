# NPU 知识体系：从硬件预算到模型交付

NPU 是一类加速器，不代表统一 ISA。脉动阵列、VLIW、静态内存规划都是具体设计选择，不是名称自带的强制属性。阅读时区分通用数学、教学模型、公开实现和指定产品行为。

## 从 Wi-Fi/嵌入式经验迁移

DMA 描述符、IOMMU、buffer 所有权、Firmware 状态机和 reset 经验可直接迁移；新增难点在于张量布局、量化语义、编译器合法变换与资源预算共同决定正确性。相比“队列有包就发送”，NPU 任务还需要对输入 shape、layout、scale 和计算依赖达成完整契约。

## 能力覆盖与可验收标准

| 能力 | 入口 | 掌握标准 |
| --- | --- | --- |
| 计算映射 | [阵列与复用](../02-Tensor-Matrix-Compute-Core/README.md) | 区分有效运算、padding、流水填充和硬件 busy |
| SRAM 规划 | [双缓冲](../03-Scratchpad-OnChip-Buffer/02-ping-pong-double-buffering.md) | 算输入、累加器、输出、工作区及 bank 约束 |
| 数值契约 | [量化](../04-Data-Quantization-Mixed-Precision/README.md) | 手算 zero-point、溢出界和重缩放，解释舍入差异 |
| 数据搬运 | [Tensor DMA](../05-NPU-DMA-Dataflow-Engine/README.md) | 从 shape/layout 推导字节 stride 和尾块 mask |
| 调度恢复 | [任务同步](../07-Command-Processor-Task-Scheduler/README.md) | 指出每个 buffer 的最后使用者及异常退出依赖 |
| 编译部署 | [编译器](../09-AI-Compiler-Software-Stack/README.md) | 区分图等价、目标合法性、fallback 与性能 |
| 跨层验证 | [量化 GEMM 案例](../Case-Studies/04-quantized-gemm-contract.md) | 定位浮点、整数、切块、实卡的首次偏差 |
| 实验预算 | [Tiling 实验](../Labs/lab02-tvm-custom-npu-tiling/README.md) | 可复现容量和尾块结果，不冒充真实时延预测 |

## 十二个递进追问

1. **TOPS 高为什么模型慢？** 先匹配精度/稀疏口径，再检查形状利用率、访存、非矩阵算子和 fallback。
2. **Stationary 是什么保持不动？** 指定层级与循环次序，说明减少哪种流量、增加哪种容量需求。
3. **SRAM 装得下就能跑吗？** 总量之外还有活跃区间、分 bank 容量、端口、对齐和 descriptor 限制。
4. **双缓冲是否必然两倍快？** 用启动、稳态 `max(load,compute)` 和排空解释，并计共享回写资源。
5. **为什么量化零点影响 padding？** 整数零不一定代表实数零；无效 K 项必须为零贡献。
6. **为何累加器比输入宽？** 给出 K 与输入幅度的上界，说明 bias 和重缩放所在位置。
7. **融合为什么会变慢？** 中间写回减少，但 live range、SRAM 和寄存器压力上升，可能导致 spill 或更小 Tile。
8. **最大 Tile 是否最优？** 容量复用、尾块浪费、启动开销相互竞争，启发式得分不能代替目标实测。
9. **量化误差与编译错误如何区分？** 先建立相同语义的整数参考，再检查切块模型与目标输出。
10. **导出 ONNX 是否完成部署？** 尚需目标编译、算子覆盖、layout、runtime ABI 与实卡验证。
11. **CPU fallback 为什么危险？** 正确性可能保持，但隐式搬运/同步使端到端时延陡增，应检查分区报告。
12. **Prefill 与 Decode 为什么不同？** 用 batch、序列长度、权重复用和 KV cache 流量推导，不能只背“一个算力一个带宽”。

## 三条完整复习路线

驱动路线：Host/Device 契约 → DMA 地址与布局 → 事件依赖 → buffer 生命周期 → 超时与复位。交付一份包含错误分支的任务时间线。

编译器路线：浮点算子 → 量化语义 → 形状/layout → Tile 候选 → 活跃区间和 SRAM → 指令/描述符 → 对拍。交付一个尾块不整齐的 GEMM 映射记录。

架构路线：工作负载分布 → 精度与阵列形状 → SRAM/DDR/NoC 预算 → 利用率损失 → 功耗和业务时延。交付明确假设的模型，不填虚构产品测量值。

## 数据与证据要求

区分三类材料：手算/脚本模型、软件模拟、目标硬件实测。模拟通过不意味着 RTL 或芯片通过；模型包能导出不意味着厂商 runtime 能加载。性能报告必须附目标型号、编译器/runtime/驱动版本、输入 profile、精度门限、fallback 列表和原始记录。

参考 [ONNX 量化算子](https://onnx.ai/onnx/operators/onnx__QuantizeLinear.html) 固定数值语义，以 [MLIR Linalg](https://mlir.llvm.org/docs/Dialects/Linalg/) 理解结构化变换，用 [NVDLA 公开单元文档](https://nvdla.org/hw/v1/ias/unit_description.html) 对照一类实际架构。它们分别回答不同层的问题，不是同一套完整芯片规范。

对照 [GPU 专题](/tech/gpu/) 时，应比较具体执行模型和软件能力，避免“GPU 全动态、NPU 全静态”这样的绝对结论。
