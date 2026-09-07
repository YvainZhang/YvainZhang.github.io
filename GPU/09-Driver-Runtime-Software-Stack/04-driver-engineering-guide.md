# 04 驱动与运行时工程问题排查与规避

## 1. 驱动与系统软件常见问题排查

| 故障现象 | 根因诊断 | 排查手段 |
| :--- | :--- | :--- |
| **Kernel Freeze / Dmesg 打印 GPU Hang** | SM 内死循环或硬件总线死锁，导致 Fence 超时 | 查看 `dmesg` 中 DRM 触发的 GPU Soft-Reset 记录 |
| **Out of Memory (OOM) 误报** | 显存碎片严重，虚拟地址空间存在大量不连续小空隙 | 开启 CUDA 虚拟内存分配 API（`cuMemAddressRange_t`）进行内存池化复用 |
| **JIT 编译时延过长导致首帧卡顿** | 运行时首次加载 PTX 动态编译为 SASS 开销巨大 | 离线编译时通过 `-gencode` 预先生成目标微架构的原生 SASS 机器码 |
