# 11 多卡集群与分布式并行

本模块剖析千卡/万卡大模型训练集群中的硬件拓扑、通信加速库 **NCCL / RCCL 微架构、3D 混合并行体系与高性能 Scale-Out 网络**。

## 章节导航

1. [NCCL 集合通信与底层拓扑算法](01-nccl-collective-comm.md)
2. [3D 并行 (TP/PP/DP) 硬件映射与通信开销](02-3d-parallelism-megatron.md)
3. [Scale-Out 集群网络与 RoCEv2 / IB 部署](03-scaleout-cluster-network.md)
4. [集群通信工程问题排查与规避](04-distributed-engineering-guide.md)
