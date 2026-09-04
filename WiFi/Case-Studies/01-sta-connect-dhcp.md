# 案例：STA 从扫描到 DHCP

## 现象

系统 UI 长时间停留在“正在连接”，或显示已连接但没有获得 IP。仅凭 UI 无法判断问题属于扫描、802.11 建链、安全握手还是 IP 配置。

## 状态表

| 阶段 | 成功证据 | 失败时继续检查 |
|---|---|---|
| Scan | 目标 BSS、BSSID、channel、capability | regulatory、信道、dwell、并发角色 |
| Authentication | Response status=0 | 空口双向性、AP 拒绝原因 |
| Association | Response status=0、AID | capability/RSN/速率兼容性 |
| Security | EAPOL 完成、密钥安装 | AKM/cipher、MIC、replay、超时 |
| Port open | 普通数据允许通过 | Driver/Firmware port state |
| DHCP | DORA 完整 | 广播过滤、队列、BA、bridge/AP |

## 定位方法

1. 用 `iw event -t` 和 supplicant 日志确定最后一个成功状态。
2. 同时抓取目标信道，确认该事件是否与空口一致。
3. 若四次握手成功但 DHCP Discover 只在 Host 可见，沿 TX enqueue、bus submit、Firmware queue、air TX 逐段核对计数。
4. 若 Discover 在空口出现但无 Offer，检查 AP/DHCP 服务和回程方向，不要继续修改 STA 认证逻辑。

## 回归矩阵

覆盖开放/WPA2/WPA3、2.4/5 GHz、错误密码、AP 拒绝、快速重连、断电恢复与 DHCP 无响应。验证失败状态能在有限时间内退出，并且下一次连接不受旧 session 影响。
