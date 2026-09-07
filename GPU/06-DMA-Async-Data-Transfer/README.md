# 06 异步数据搬运与 DMA 引擎

本模块剖析 GPU 芯片内部的专用硬件搬运引擎——**Copy Engine (DMA Engine)**，以及实现零拷贝跨节点通信的 **GPUDirect RDMA / GPUDirect Storage** 体系。

## 章节导航

1. [Copy Engine (DMA) 硬件微架构](01-copy-engine-dma.md)
2. [GPUDirect RDMA 与 GPUDirect Storage 零拷贝技术](02-gpudirect-rdma-storage.md)
3. [异步 Stream 并发与 CUDA Graph 硬件执行](03-async-stream-concurrency.md)
4. [DMA 搬运工程问题排查与规避](04-dma-engineering-guide.md)
