# 02 802.11 MAC 与空口

本模块不按标准章节逐条复述，而是围绕三个工程问题：设备怎样获得发送机会，接收方怎样确认可靠性，聚合怎样改变吞吐与故障形态。

## 帧类型

- **管理帧**：Beacon、Probe、Authentication、Association、Action。
- **控制帧**：ACK、Block ACK、RTS/CTS、PS-Poll 等。
- **数据帧**：承载业务、EAPOL 或 Null/QoS Null 状态通知。

帧类型决定状态机含义；Sequence Control、Retry、Protected、More Fragments、QoS Control 等字段决定重传、重排序、加密与省电行为。

继续阅读：

- [帧、信道访问、可靠性与聚合](01-mac-air-interface.md)
- [Hardware MAC 实时路径](02-hardware-mac-realtime-path.md)
- [802.11ax OFDMA 与 Trigger 实时路径](03-he-ofdma-trigger-path.md)
- [BlockAck、Sequence 与 Reorder Engine](04-blockack-reorder-engine.md)

## 本章检查点

- 区分 MSDU、MPDU、A-MSDU、A-MPDU 与 PPDU。
- 能用 Sequence/Fragment Number 判断重传、分片和丢失。
- 能解释 PHY Rate 很高但 TCP Goodput 仍低的原因。
