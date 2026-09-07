# 04 高速互联工程问题排查与规避

## 1. 高速互联硬件故障与调优表

| 故障现象 | 根因分析 | 现场诊断工具与方法 |
| :--- | :--- | :--- |
| **PCIe 链路降速降宽 (x16 -> x8/x4)** | PCIe 金手指接触不良、插槽积灰或信号完整性 (SI) 劣化 | `lspci -vvv -s <bdf> | grep LnkSta` 检查降速告警 |
| **NVLink CRC 错误暴增** | NVLink 铜缆/背板连接器松动或 SerDes 均衡参数漂移 | `nvidia-smi nvlink -e` 统计物理层与数据链路层错误包 |
| **P2P 跨卡通信吞吐腰斩** | PCIe ACS (Access Control Services) 未关闭，强制数据绕行 CPU | 内核关闭 ACS 或在 BIOS 中启用 IOMMU P2P 直通 |
