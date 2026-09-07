# 04 集群通信工程问题排查与规避

## 1. 分布式训练经典故障排查表

| 故障现象 | 根因诊断 | 排查手段 |
| :--- | :--- | :--- |
| **NCCL Watchdog Timeout (训练卡死)** | 某单卡发生 CUDA Error 挂死，未响应 AllReduce 导致全集群等待 | 查看 `NCCL_DEBUG=INFO` 日志，定位最先停顿的 Rank 编号 |
| **RoCE 网络 PFC 死锁 (PFC Deadlock)** | 环路流量触发 PFC 持续向源端发送 Pause 帧，整网拥塞 | 交换机配置 Watchdog 强制重置持续超时的 PFC 队列 |
| **多机通信吞吐仅为单机的 20%** | NCCL 未能正确识别 NUMA 亲和性，网卡与 GPU 跨 Socket 访问 | 设置 `export NCCL_TOPO_DUMP=topo.xml` 校准网卡拓扑绑定 |
