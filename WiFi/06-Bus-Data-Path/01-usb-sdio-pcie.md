# USB、SDIO 与 PCIe 数据路径

## USB

USB Wi-Fi 常用 Bulk Endpoint。Host 将一个或多个 Packet 封装进 URB，HCD 调度后才真正传输；完成回调表示 USB 事务结束，不代表 MAC 已获 ACK。优化抓手包括：

- 预提交足够 RX URB，避免设备有数据却无 Host buffer；
- TX/RX 聚合减少每次提交和回调开销；
- 将解析、协议栈处理与完成回调分层，避免回调上下文过重；
- 观察 URB 长度分布、inflight 数、完成间隔与错误码；
- 对齐 CPU affinity，减少跨核迁移与 Cache 抖动。

聚合并非越大越好。设单包固定成本为 `C`，聚合 `N` 个包可摊薄为 `C/N`；但等待凑包会增加排队时延，并扩大一次错误的影响面。需要针对吞吐与交互流量设置大小和时间双阈值。

## SDIO

SDIO 通常通过 CMD53 批量读写数据端口。关注 block size、对齐、host claim、IRQ/thread 调度和设备侧可用长度寄存器。频繁小事务会被命令开销吞噬；一次搬运过大又可能阻塞控制命令和高优先级事件。

## PCIe

PCIe 方案常用 Host/Device 共享的 DMA Ring。Producer/Consumer 指针更新需要明确内存顺序，Doorbell 之前确保 descriptor 和 payload 对设备可见；回收前确保完成状态已同步。还要处理 IOMMU mapping、MSI/MSI-X affinity 与 Function Level Reset。

## 通用守恒关系

无论哪种总线，都可以用相同计数建立第一层定位：

```text
Host enqueue
= bus submit + host-side pending + host drop

bus submit
= bus complete + bus inflight + bus error/cancel

device receive
= firmware consume + device queue + parse/drop
```

在固定时间窗取差分。第一处明显不守恒的位置，就是下一轮增加 Trace 的地方。

详细 USB 驱动案例可参考博客文章 [Wi-Fi USB 驱动架构与多核性能调优](/2025/07/13/wifi-usb-driver-performance-tuning/)。
