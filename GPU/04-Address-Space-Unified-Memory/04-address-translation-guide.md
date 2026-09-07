# 04 地址翻译工程问题排查与规避

## 1. 常见 MMU / UVM 故障排查

| 故障现象 | 硬件/驱动根因 | 排查定位方法 |
| :--- | :--- | :--- |
| **CUDA Illegal Address (XID 31)** | GPU 访问未映射或越界虚拟地址 | 启用 `compute-sanitizer --tool memcheck` 定位非法访问行号 |
| **UVM Page Fault Storm（缺页风暴）** | CPU 与 GPU 频繁交替读写同一内存区域触发乒乓迁移 | 使用 `cudaMemAdvise(..., cudaMemAdviseSetReadMostly)` 设置只读提示 |
| **TLB Invalidation Timeout** | 驱动更新页表后广播 TLB Invalidate，部分 SM 处于死锁无法应答 | 抓取 GPU GigaThread 挂死堆栈，执行 GPU 引擎级 Soft Reset |
