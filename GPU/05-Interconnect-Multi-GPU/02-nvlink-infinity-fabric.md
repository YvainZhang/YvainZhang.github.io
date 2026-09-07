# 02 NVLink 与 Infinity Fabric 专有互联协议

## 1. NVLink 核心架构与代际特性

- **硬件形态**：基于超高速 SerDes（100Gbps+ PAM4 per Lane）构成的专有点对点差分链路。
- **协议栈层次**：
  - **Physical Layer (PHY)**：实现高速信号均衡、时钟数据恢复（CDR）与链路重训练。
  - **Data Link Layer (DL)**：负责 128-byte / 256-byte 数据包打包、CRC 校验与硬件重传。
  - **Transaction Layer (TL)**：直接承载原生 GPU Load/Store 事务、原子操作（Atomic RMW）以及跨卡共享内存访问。
- **带宽指标**：单 GPU NVLink 总带宽已达 **900 GB/s ~ 1.8 TB/s**，是 PCIe 5.0 的 7~14 倍。
