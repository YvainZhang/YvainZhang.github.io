# 案例：STA 从扫描到 DHCP

!!! note "场景性质说明"
    本案例为合成教学场景（Synthetic Educational Model）。文中的日志切片与排查时序用于完整展示“从 802.11 关联到 DHCP 租约”的因果判定逻辑，不对应特定量产芯片的原始实测记录。

## 现象描述

系统 UI 长时间停留在“正在获取 IP 地址”或“正在连接”，随后提示“连接已断开”或转为受限网络（No Internet）。
从用户态直观体验来看，无法分辨故障究竟发生在 802.11 扫描、链路认证关联、WPA 安全握手、底层受控端口放行，还是上层 DHCP 协议栈。

## 状态迁移与证据对照表

| 阶段 | 正常完成标志 | 常见异常现象 | 最小证据与定位手段 |
|---|---|---|---|
| **1. 扫描 (Scan)** | 找到目标 BSSID，解析出正确 SSID、RSSI、AKM 与信道 | 搜不到目标 AP，或扫描超时 | `iw dev wlan0 scan dump`、查看国家码/信道限制 (Regulatory Domain)、检查是否处于并发离道限制 |
| **2. 认证 (Auth)** | `Authentication Response (status=0)` | AP 返回非 0 状态码，或空口无回包 | 空口抓包确认双向链路平衡性（STA 发射功率过低 AP 未收全，或 AP RSSI 假强） |
| **3. 关联 (Assoc)** | `Association Response (status=0, AID>0)` | `status=12` (拒绝关联) 或 IE 不支持 | 检查 RSN IE、HT/VHT/HE Capabilities 协商是否超出 AP 支持集 |
| **4. 安全握手 (RSN)** | 4-Way Handshake 完成，PTK/GTK 安装成功 | 卡在 M2 或 M3，不断重传超时 | 检查密码错误（AP 返回 MIC failure）、Replay Counter 错位、以及 Key 安装完成事件 |
| **5. 端口放行 (Port Open)** | Driver/Firmware Controlled Port 状态置为 Authorized | 802.11 显示已连接，但任何普通单播数据包均出不去 | 检查驱动中 `cfg80211_port_authorized` 调用，核对驱动 TX 队列中的安全阻断计数 |
| **6. IP 租约 (DHCP)** | 收到 DHCP ACK，本地网卡配置 IP/掩码/网关 | 发出 DHCP Discover 但收不到 Offer | Host/Device 广播包过滤 (ARP/DHCP Drop)、AP 侧隔离或 DHCP 服务池耗尽 |

## 教学推演：多源日志对齐示例

### 1. 用户态 wpa_supplicant 视角（正常完成 4 步握手）
```text
wlan0: SME: Trying to authenticate with 00:11:22:33:44:55 (SSID='Lab-WiFi' freq=5180 MHz)
wlan0: Trying to associate with 00:11:22:33:44:55 (SSID='Lab-WiFi' freq=5180 MHz)
wlan0: Associated with 00:11:22:33:44:55
wlan0: WPA: RX EAPOL-Key 1/4
wlan0: WPA: Sending EAPOL-Key 2/4
wlan0: WPA: RX EAPOL-Key 3/4
wlan0: WPA: Sending EAPOL-Key 4/4
wlan0: WPA: Key negotiation completed with 00:11:22:33:44:55 [PTK=CCMP GTK=CCMP]
wlan0: CTRL-EVENT-CONNECTED - Connection to 00:11:22:33:44:55 completed [id=0 id_str=]
```

### 2. 内核与网络栈视角（DHCP 客户端超时）
```text
[ 142.315621] wlan0: authenticated
[ 142.320431] wlan0: associate with 00:11:22:33:44:55 (try 1/3)
[ 142.325112] wlan0: RX AssocResp from 00:11:22:33:44:55 (capab=0x1511 status=0 aid=2)
[ 142.325810] wlan0: associated
[ 142.348920] wlan0: Limiting TX data: port unauthorized
[ 142.355120] dhcpcd[1842]: wlan0: broadcasting for a lease (DHCPDISCOVER)
[ 147.360123] dhcpcd[1842]: wlan0: broadcasting for a lease (DHCPDISCOVER)
[ 152.370150] dhcpcd[1842]: wlan0: timed out waiting for a valid DHCP offer
```

### 3. 空口抓包对账
使用 Wireshark / Radiotap 抓包比对：
- **空口看到**：Association 正常，EAPOL M1~M4 交互耗时正常（~20ms）。
- **但空口完全没有出现 DHCP Discover（UDP 67/68 广播帧）**！
- **结论**：DHCP Discover 在 Host 驱动或固件内部被拦截丢弃，未抵达空口。

## 典型根因推演与排查树

```text
现象：EAPOL 完成但没有 IP
 ├── 1. 空口是否有 DHCP Discover 发出？
 │    ├── 否 (本案例) -> 检查 Controlled Port 状态
 │    │    ├── 驱动是否在收到 Key Install 完成后再开 Port？（若未收到回调则永久阻塞）
 │    │    └── 固件是否把广播帧误当作未授权流量 Drop？（过滤规则未刷新）
 │    └── 是 -> 检查 AP 侧响应
 │         ├── AP 是否有对应 DHCP Offer 发回？
 │         │    ├── 否 -> AP 侧 DHCP 池满 / VLAN 隔离 / 交换机回程故障
 │         │    └── 是 -> 检查 STA 端接收
 │         │         ├── STA 是否收到 Offer？
 │         │         │    ├── 否 -> 组播/广播速率过低丢包、固件 RX multicast 过滤未放开
 │         │         │    └── 是 -> 本地防火墙 (iptables/nftables) 拦截
```

### 关键修复点示例

在许多 FullMAC/SoftMAC 驱动中，握手由 Host 的 `wpa_supplicant` 完成，但底层驱动维护独立的受控端口标志：
```c
/* 错误实现：仅在 cfg80211_connect_result 时打通端口，但此时握手尚未开始 */
/* 正确实现：在 set_key 或 port_authorized 回调确认后，才放行普通业务数据包 */
void my_driver_set_port_authorized(struct my_vif *vif, bool authorized)
{
    spin_lock_bh(&vif->lock);
    vif->port_authorized = authorized;
    spin_unlock_bh(&vif->lock);

    /* 唤醒因等待握手而阻塞的发送队列 */
    if (authorized)
        netif_tx_wake_all_queues(vif->ndev);
}
```

## Wireshark 关键过滤语法备忘

- 过滤 802.11 认证/关联流程：`wlan.fc.type_subtype == 0x000b || wlan.fc.type_subtype == 0x0000 || wlan.fc.type_subtype == 0x0001`
- 过滤 EAPOL 4 次握手：`eapol`
- 过滤目标 AP 的 DHCP 交互：`bootp && wlan.addr == 00:11:22:33:44:55`
- 查看重放计数：`wlan_rsna_eapol.keydes.replay_counter`

## 回归验证矩阵

1. **协议覆盖**：开放网络 (Open)、WPA2-PSK (AES-CCMP)、WPA3-SAE (H2E/Hunting-and-Pecking)。
2. **频段与信道**：2.4 GHz (1/6/11)、5 GHz (36/149 及 DFS 信道 52~64)。
3. **异常场景**：故意输入错误密码（验证状态机能否在 3s 内报错退出而非卡死）、AP 突然断电、DHCP 服务器耗尽租约。
4. **长稳测试**：反复重连 500 次，验证每次连接断开后 Session 与 Port 状态完全清空，无内存泄漏与僵尸队列。

