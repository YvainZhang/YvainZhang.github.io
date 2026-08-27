# Lab 02：DMA Cache 所有权错误模拟

普通 QEMU `virt` 与 Host Cache 不能稳定复现真实非一致 DMA 的 Dirty Line 覆盖。本实验用两个显式副本模拟 CPU Cache 与 Device-visible Memory，准确展示 Clean/Invalidate 和 Ownership；它验证软件协议，不声称验证物理 Cache 指令。

```bash
cc -O2 -Wall -Wextra coherency_sim.c -o coherency_sim
./coherency_sim
```

程序先演示 CPU 写后未 Clean，设备读到旧数据；再演示设备写后 CPU 未 Invalidate，CPU 读到旧数据；最后执行正确转移。真实 Linux 驱动应把模拟函数替换为 DMA Mapping API，而不是手写 `memcpy`。
