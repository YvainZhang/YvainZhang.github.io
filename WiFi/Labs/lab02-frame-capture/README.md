# 实验 02：管理帧抓取与状态机对齐

## 目标

用 Monitor 接口抓取 Beacon、Probe、Authentication、Association 和 EAPOL，并与用户态事件对齐。

## 准备

使用支持 Monitor Mode 的独立无线网卡。确保实验信道和频段符合当地法规，不进行干扰、注入或未授权网络测试。

## 步骤

```bash
sudo iw phy phy0 interface add mon0 type monitor
sudo ip link set mon0 up
sudo iw dev mon0 set channel 36
sudo tcpdump -i mon0 -s 0 -w wifi-connect.pcap
```

接口名、phy 和信道必须按测试机修改。另开终端运行：

```bash
sudo iw event -t
```

让测试 STA 连接自有 AP，完成后停止抓包并用 Wireshark 查看。

## 分析清单

- 用 BSSID/STA MAC 过滤目标会话；
- 找到 Authentication 与 Association status code；
- 检查 RSN/AKM/cipher 协商；
- 对齐 EAPOL M1–M4 的 replay counter；
- 记录空口时间与 `iw event -t` 的偏移；
- 判断缺帧是协议事实还是抓包点遗漏。

## 清理

```bash
sudo ip link set mon0 down
sudo iw dev mon0 del
```
