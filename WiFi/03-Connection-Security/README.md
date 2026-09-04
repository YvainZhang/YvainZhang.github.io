# 03 建链与安全

“Wi-Fi 已连接”至少跨越无线发现、802.11 认证与关联、密钥协商、受控端口放行、IP 配置和连通性验证。UI 上的一个图标会隐藏这些不同阶段。

## 生命周期

```text
Interface Ready → Scan → Select BSS → Authentication → Association
→ Key Handshake → Controlled Port Open → DHCP / IPv6 → Connectivity
```

任一步都应具有明确的进入条件、成功事件、失败原因与超时。日志只打印“connect fail”会丢失最重要的状态信息。

继续阅读：[扫描到可用网络的完整生命周期](01-connection-lifecycle.md)。

## 本章检查点

- 能区分 Authentication Frame 与 WPA 四次握手。
- 知道 EAPOL 与 DHCP 在数据通路上的特殊放行条件。
- 能从空口、supplicant、Driver/Firmware 三侧对齐一次失败。
