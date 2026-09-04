# 10 调试与恢复

高质量 Wi-Fi 调试的核心不是日志量，而是时间对齐、状态快照、计数守恒和可复现条件。目标是回答“第一处偏离预期发生在哪里”。

## 四类证据

- 用户态状态与策略：supplicant/hostapd、NetworkManager/Android。
- 内核与 Driver：nl80211 event、netdev 统计、tracepoint、bus error。
- Firmware/Device：命令事件、队列、assert、dump、MAC 统计。
- 空口：管理帧、EAPOL、数据、ACK/BA、RSSI/MCS/Retry。

继续阅读：

- [建立可复现的 Wi-Fi 证据链](01-evidence-workflow.md)
- [Host、Firmware、MAC、PHY 与 Sniffer 多源对齐](02-multi-source-trace.md)

## 本章检查点

- 所有日志使用可换算的单调时间。
- 结论能指出具体状态、计数或帧，而不是只描述现象。
- 自动恢复之前保留足够现场，并对恢复成功率和副作用计数。
