# 03 芯片架构 PPA 权衡矩阵与系统选型

| 维度 | 端侧 Edge NPU | 云端 Cloud NPU |
| :--- | :--- | :--- |
| **主要数据类型** | INT4 / INT8 / FP16 | FP8 / BF16 / FP32 / TF32 |
| **脉动阵列尺寸** | $16 \times 16$ 或 $32 \times 32$ | $128 \times 128$ 或分布式多核平铺 |
| **片上 SRAM 容量** | 512KB ~ 4MB | 64MB ~ 256MB+ |
| **主要工作负载** | 推理（Inference Only） | 预训练（Pre-training）与大规模并发推理 |
