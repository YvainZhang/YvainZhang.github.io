# 02 PTX 弱内存模型与 Barrier 汇编分析

GPU 采用高度宽松的弱内存模型（Weak Memory Model）：
- **Acquire-Release 语义**：`ld.acquire` 保证后续所有访存不被重排到该指令之前；`st.release` 保证之前的所有写操作对其他 SM 可见后才提交当前写。
- **Memory Fences**：`membar.gl`（全显存屏障）、`membar.cta`（Block 内部屏障）。
