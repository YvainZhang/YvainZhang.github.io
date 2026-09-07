# 02 HCCL 专用集合通信加速引擎与硬件实现

## 1. 硬件级集合通信加速引擎 (Collective Engine)

- **硬件解耦**：NPU 片上集成独立的集合通信硬件加速器，**执行 AllReduce、AllGather、ReduceScatter 时无需占用脉动阵列算力**。
- **动态拓扑自适应**：在片内使用环形（Ring）算法，跨节点使用分层双二叉树（Hierarchical Tree）算法。
