# 02 硬件图调度器与 Task Queue 任务队列

## 1. 硬件任务调度引擎 (Graph Execution Engine)

- **硬件 Task Queue**：硬件维护环形任务队列，每个 Task 描述符包含算子类型、输入输出 Tensor 物理地址、SRAM 偏移与依赖 Event。
- **自动依赖解析**：当 Task A 的执行完成信号释放关联 Event 时，硬件调度引擎自动激活就绪的 Task B，**实现纯硬件级别的算子链式调度，无需 CPU 系统调用**。
