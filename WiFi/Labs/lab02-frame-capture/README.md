# 实验 02：无线空口抓包 (Monitor Mode) 与协议状态机对齐

## 实验目标

通过配置独立无线网卡的 Monitor 模式（监听模式），无损捕获空口原始 802.11 管理帧（Beacon、Probe Request/Response、Authentication、Association）与控制握手帧（EAPOL 4-Way），学习 Radiotap 头部信息判读，并将空中抓包时间戳与操作系统日志（`iw event` / `dmesg`）进行毫秒级对齐分析。

## 硬件与环境准备

- **抓包硬件**：支持 Monitor Mode 的 USB 无线网卡（如芯片为 MediaTek MT7612U / RTL8812AU / AR9271，或直接使用 Lab 01 的虚拟无线 `hwsim0`）。
- **注意**：监听网卡必须锁定在与被测 AP 相同的信道与频宽（如 2.4G Channel 6，或 5G Channel 36 80MHz）。

## 步骤 1：创建并配置 Monitor 监听接口

```bash
# 1. 查找监听物理 Radio
iw dev

# 2. 在指定物理 Radio (如 phy1) 上增加 monitor 模式接口 mon0
sudo iw phy phy1 interface add mon0 type monitor flags fcsfail control otherbss

# 3. 启动接口并锁定目标信道 (以 5GHz Channel 36 80MHz 为例)
sudo ip link set mon0 up
sudo iw dev mon0 set freq 5180 80 5210

# 4. 验证接口工作状态
iw dev mon0 info
```

## 步骤 2：启动无损抓包与日志联动

在终端 1 中启动抓包（保留完整 Radiotap 与原始 FCS 校验码）：
```bash
sudo tcpdump -i mon0 -s 0 -y IEEE802_11_RADIO -w /tmp/wifi_air_capture.pcapng
```

在终端 2 中同步记录 Host 端内核与 Supplicant 时间戳：
```bash
sudo iw event -t > /tmp/host_events.log
```

在被测 STA 上发起一次正常的 Wi-Fi 连接，成功获取 IP 并上网后，按 `Ctrl+C` 停止抓包。

## 步骤 3：使用 tshark / Wireshark 深度解析过滤

### 1. 命令行快速提炼关键建链帧 (tshark)
```bash
tshark -r /tmp/wifi_air_capture.pcapng \
  -Y "wlan.addr == 00:11:22:33:44:55 && (wlan.fc.type == 0 || eapol)" \
  -T fields -e frame.time_relative -e wlan.fc.type_subtype -e _ws.col.Info
```
预期提取输出：
```text
0.000000    0x0004    Probe Request, SN=1234, FN=0, Flags=....
0.002410    0x0005    Probe Response, SN=567, FN=0, Flags=....
0.015201    0x000b    Authentication (Open System), Seq=1, Status=Success
0.017502    0x000b    Authentication (Open System), Seq=2, Status=Success
0.021034    0x0000    Association Request, AID=0, Capabilities=...
0.023810    0x0001    Association Response, AID=2, Status=Success
0.035120    0x0028    QoS Data (EAPOL-Key, Message 1 of 4)
0.038410    0x0028    QoS Data (EAPOL-Key, Message 2 of 4)
0.045201    0x0028    QoS Data (EAPOL-Key, Message 3 of 4)
0.048912    0x0028    QoS Data (EAPOL-Key, Message 4 of 4)
```

> **注意帧类型区分**：EAPOL 不是 802.11 管理帧（`type 0`），而是由受控端口特殊放行的**数据帧**，通过 LLC/SNAP 头（EtherType 0x888e）承载。在实际抓包中，它由普通 Data 帧（`type 2, subtype 0 -> 0x0020`）或 QoS Data 帧（`type 2, subtype 8 -> 0x0028`）承载，具体取决于 AP 与 STA 之间是否协商启用了 QoS（WMM）及具体驱动实现。示例中的 `0x0028` 代表开启了 QoS 的典型抓包现场；在 Wireshark 过滤时，建议使用通用的 `(wlan.fc.type == 2 && eapol)` 兼容两种形态，避免因硬编码特定子类型而漏抓。

### 2. Wireshark 关键展示字段判读

- **Radiotap 头部关键指标**：
  - `radiotap.dbm_antsignal`：接收信号强度 (RSSI)，判断是否距离过远或信号过载。
  - `radiotap.mcs.index` 与 `radiotap.flags.badfcs`：速率与校验错误标志。
- **管理帧 Capabilities**：
  - 在 `Association Request` 下查看 `Tagged parameters`：检查是否包含 `RSN Information` (AKM 套件与加密算法)、`HT Capabilities`、`VHT Capabilities`、`HE Capabilities`。
- **EAPOL 4-Way 握手防重放验证**：
  - 检查 M1 与 M2 的 Replay Counter 是否严格一致。
  - 检查 M3 的 Replay Counter 是否比 M1 递增。

## 步骤 4：对齐空口与 Host 软件日志

将 `/tmp/host_events.log` 与抓包相对时间轴对比：
1. **关联延迟**：空口收到 `Association Response` 到驱动触发 `connected to <BSSID>` 的微秒级差值（通常在 1~5ms 之间）。
2. **握手延迟**：空口 M4 确认发出后，Host 日志何时打印 `new key installed` 与 `port authorized`。若两者差距超过 100ms，说明驱动向固件下发密钥的 IPC 命令路径存在严重延迟。

## 实验清理

```bash
sudo ip link set mon0 down
sudo iw dev mon0 del
```

