# 术语表

| 术语 | 含义 | 所属边界 |
|---|---|---|
| AKM | Authentication and Key Management | 安全能力协商 |
| A-MPDU | 聚合多个 MPDU | MAC 聚合/Block ACK |
| A-MSDU | 聚合多个 MSDU | MAC 封装 |
| BA / BAR | Block ACK / Block ACK Request | 批量确认与重排序窗口 |
| BSS / BSSID | 基本服务集及其标识 | 无线网络实例 |
| cfg80211 | Linux 无线配置与事件框架 | 内核控制面 |
| Controlled Port | 密钥建立前后控制普通数据通行的端口状态 | 802.1X/WPA |
| DTIM / TIM | AP 在 Beacon 中提示缓存流量 | 省电 |
| EDCA | 按 Access Category 竞争信道 | QoS/信道访问 |
| EAPOL | 认证与密钥交换承载协议 | 安全握手 |
| FullMAC | 多数 MAC/MLME 状态机由 Firmware/硬件承担 | 架构分工 |
| Goodput | 应用实际得到的有效数据速率 | 性能结果 |
| MCC / SCC | 多信道并发 / 同信道并发 | 多角色并发 |
| mac80211 | Linux SoftMAC 通用框架 | 内核数据/控制面 |
| MLME | MAC Sublayer Management Entity | 扫描、认证、关联等状态机 |
| MPDU / MSDU | MAC 协议数据单元 / MAC 服务数据单元 | 数据封装 |
| NAPI | Linux 网络接收的轮询机制 | Host RX |
| nl80211 | Linux 用户态无线 Netlink ABI | 用户态↔内核 |
| PHY Rate | 物理层协商/使用的传输速率 | 不等于应用吞吐 |
| P2P GO | Wi-Fi Direct Group Owner | 类似组内 AP |
| PPDU | PHY 协议数据单元 | 实际空口发送单元 |
| PS / U-APSD | Legacy Power Save / QoS 自动省电交付 | 空口低功耗 |
| Radiotap | Monitor 抓包附带的无线元数据格式 | 抓包观测 |
| Reorder | 按 Sequence Number 恢复聚合帧顺序 | RX/BA |
| SoftMAC | 通用 MAC 逻辑主要由 Host/mac80211 承担 | 架构分工 |
| TID | Traffic Identifier | QoS、聚合与 BA 的流分类 |
| TWT | Target Wake Time | 协商式唤醒调度 |
| VIF | Virtual Interface | STA/AP/P2P 等逻辑接口 |
| wiphy | Linux 对无线 PHY 能力的抽象 | cfg80211 |

同一个词在 Host、Firmware 和抓包工具中可能使用不同命名。调试文档应同时注明接口、TID、session/generation 和时间基准，避免只靠缩写对齐现场。
