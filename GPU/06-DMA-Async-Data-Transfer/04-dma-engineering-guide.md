# 04 DMA 搬运工程问题排查与规避

## 1. DMA 常见故障排查表

| 故障现象 | 根因分析 | 规避方案 |
| :--- | :--- | :--- |
| **`cudaMemcpyAsync` 发生隐式同步阻塞** | 传入的 Host 内存指针未通过 `cudaHostAlloc` 锁定为 Page-locked (Pinned) 内存 | 必须使用 Pinned Memory 才能触发硬件真异步 DMA |
| **GPUDirect RDMA 初始化报错** | 内核未加载 `nvidia-peermem` 模块或 IOMMU 阻止了 P2P 事务 | 加载 `nvidia-peermem`，并在 grub 配置中加入 `iommu=pt` |
| **Stream 重叠失效 (串行执行)** | 算子默认使用 Default Stream (Stream 0)，触发全局同步语义 | 显式为每个并发任务创建非阻塞 Stream（`cudaStreamNonBlocking`） |
