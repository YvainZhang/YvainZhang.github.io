# 跨模块工程案例

本目录结合计算核心、存储、驱动与互联，推演几个任务的执行过程：

1. [FlashAttention 在 SM 内部的硬件执行路径推演](01-flash-attention-hardware-path.md)
2. [PCIe/NVLink P2P 跨卡零拷贝直接内存访问事务流](02-pcie-p2p-direct-transfer.md)
3. [多机多卡 AllReduce 集合通信数据流全链路推演](03-multi-gpu-allreduce-flow.md)
4. [GEMM 从任务提交、数值验证到性能证据](04-gemm-evidence-path.md)
