# 04 Linux Wi-Fi 软件栈

Linux 把 Wi-Fi 能力分散在用户态守护进程、nl80211/cfg80211、mac80211、具体 Driver 和网络协议栈中。理解责任边界，才能知道日志应该在哪一层打开。

## 主要组件

| 组件 | 责任 |
|---|---|
| wpa_supplicant | STA 网络选择、认证与密钥协商策略 |
| hostapd | AP 配置、认证、关联与管理 |
| nl80211 | 用户态和内核之间的 Netlink ABI |
| cfg80211 | 无线配置、能力、regulatory 与事件框架 |
| mac80211 | SoftMAC 通用 MLME、队列与帧处理能力 |
| Vendor Driver/Firmware | 设备数据通路、硬件与卸载状态机 |

继续阅读：

- [cfg80211、mac80211 与用户态组件](01-linux-wifi-stack.md)
- [SKB、Netdev Queue 与 NAPI](02-skb-netdev-napi.md)

## 本章检查点

- 能从用户操作追到 nl80211 command 和 Driver callback。
- 知道 FullMAC 与 SoftMAC 的回调及事件边界不同。
- 不把 netdev UP、无线关联和 IP ready 混为一谈。
