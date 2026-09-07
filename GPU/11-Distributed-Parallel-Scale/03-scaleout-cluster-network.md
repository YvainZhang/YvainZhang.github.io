# 03 Scale-Out 集群网络与 RoCEv2 / IB 部署

## 1. InfiniBand vs 无损以太网 RoCEv2

| 维度 | InfiniBand (IB) | RoCEv2 (RDMA over Converged Ethernet) |
| :--- | :--- | :--- |
| **流控机制** | Credit-based 硬件信用流控（天然无丢包） | PFC (基于优先级的流控) + ECN (显式拥塞通知) |
| **算网融合** | 支持 SHARP 网内计算（交换机直接执行 AllReduce） | 主要依赖端到端 GPU 聚合计算 |
| **建设成本** | 专用交换机与网卡，成本极高 | 基于成熟以太网生态，性价比高 |
