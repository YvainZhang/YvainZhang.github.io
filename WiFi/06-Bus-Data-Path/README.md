# 06 总线与数据通路

USB、SDIO 与 PCIe 不只是不同带宽的管道，它们的事务模型、并发方式、完成语义和故障恢复完全不同。Wi-Fi 性能与稳定性经常受 Host Interface 主导。

## 快速比较

| 总线 | 典型数据模型 | 主要优势 | 常见瓶颈 |
|---|---|---|---|
| USB | URB、Endpoint、批量传输 | 通用、易集成 | 调度间隔、拷贝、URB 深度、CPU |
| SDIO | CMD53、Block、Function | 嵌入式常见、引脚少 | 中断/轮询、block size、claim host |
| PCIe | DMA Ring、MSI/MSI-X | 高吞吐、低时延 | Ring 管理、IOMMU、顺序与恢复 |

继续阅读：[USB、SDIO 与 PCIe 数据路径](01-usb-sdio-pcie.md)。

## 本章检查点

- 区分“总线提交完成”和“空口发送成功”。
- 能计算 inflight 深度是否足以覆盖传输往返延迟。
- 能解释聚合为何同时影响吞吐、时延和内存。
