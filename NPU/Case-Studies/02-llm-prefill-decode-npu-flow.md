# 02 LLM Prefill 与 Decode 在 NPU 硬件上的全流程推演

- **Prefill 阶段（Prompt 处理）**：大 Batch 矩阵计算，属于 **Compute-Bound**。脉动阵列达到 90%+ 满载。
- **Decode 阶段（逐 Token 生成）**：向量-矩阵乘法（GEMV），属于典型 **Memory-Bound**。瓶颈在外部显存带宽，需依赖 KV Cache 显存优化与权重驻留策略。
