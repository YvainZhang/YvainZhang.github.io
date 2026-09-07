# 帧、信道访问、可靠性与聚合

## 先分清数据单位

```text
上层数据 → MSDU
MAC 封装 → MPDU
多个 MSDU 合并 → A-MSDU
多个 MPDU 聚合 → A-MPDU
PHY 加前导码并发射 → PPDU
```

A-MSDU 减少 MAC Header 开销，但其中一个错误可能影响整个聚合体；A-MPDU 允许 Block ACK 对多个 MPDU 选择性确认，是现代 Wi-Fi 吞吐的关键。二者可以组合，但调试工具展示层次可能不同。

## 竞争信道

DCF/EDCA 的基本节奏是监听、等待帧间间隔、随机退避、发送、等待确认。高优先级 AC 通过 AIFS、CWmin/CWmax 与 TXOP 获得不同机会。拥塞环境里，空口时间比“包数”更有解释力：低速终端、重试或隐藏节点可能消耗大量 airtime。

## 可靠性与 Block ACK

普通单播 MPDU 通常由 ACK 确认。建立 BA Session 后，一段 Sequence Number 窗口由 Block ACK 位图批量确认，发送端据此选择重传，接收端按 MPDU Sequence 与本地窗口重排序。分析异常时关注：

1. ADDBA Request/Response 是否成功；
2. TID、起始 Sequence 与 window size 是否一致；
3. BAR/BA 是否持续推进窗口；
4. 接收端是否因缺帧长期等待，最终超时释放；
5. 断链或重建时旧 BA 状态是否清理。

## 分片与聚合不是同一件事

分片把一个 MSDU 拆成多个带独立 MAC Header 的 Fragment，并通过 Fragment Number 与 More Fragments 重组；聚合则把多个数据单元放进一次传输机会。现代网络更常见聚合，分片主要用于理解兼容性和特殊阈值问题。详细背景可参考博客文章 [IEEE 802.11 分片机制](/2024/12/08/ieee-80211-fragmentation/)。

## 抓包判读顺序

- 先确认抓包位置和信道，避免把“没抓到”当“没发送”。
- 对齐发射端、空口和接收端的 Sequence/TID。
- 再看 Retry、速率、RSSI、BA Bitmap 与间隔时间。
- 最后结合 Driver/Firmware 计数判断帧在哪一段消失。

## 地址、序列与帧类型的具体含义

Frame Control 的 To DS/From DS 决定地址映射。普通 STA→AP（三地址）中 Address1 为接收无线节点 AP/BSSID，Address2 为 STA，Address3 为分布系统中的最终目的地址；AP→STA 则 Address1 为 STA、Address2 为 AP/BSSID、Address3 为原始源。四地址 WDS/桥接使用额外地址，不能直接套三地址转换。

QoS Control 提供 TID 与 ACK policy 等信息；Sequence Control 中 Sequence 为 12 bit、Fragment Number 为 4 bit。TID 是流量类别/序列上下文之一，AC 是竞争实体，二者不是同一个对象。

常见 UP→AC 对应是 0/3→BE、1/2→BK、4/5→VI、6/7→VO，但上层 DSCP 到 UP 的策略可能由 QoS Map 或平台改变。把 DSCP 数值直接当 TID 会产生错误分类。

## DCF/EDCA 的一次教学演算

选用 5 GHz OFDM 的示例参数 SIFS=16 μs、slot=9 μs，某 AC 的 AIFSN=3、CW=15：

```text
AIFS = 16 + 3 × 9 = 43 μs
E[backoff] = 15/2 × 9 = 67.5 μs
```

这仅为无冻结、无碰撞的一次竞争模型。真实 Backoff 遇 Busy 会暂停；重试改变 CW；同一 TXOP 内也不是每个帧都重新竞争。不要把这个结果写成跨频段和 AC 的恒定时延。

物理 CCA 和 NAV 分别表示物理与虚拟载波侦听。分析不发包要区分 ED、preamble detect、NAV、退避、功耗或切信道 gate，单独一个“channel busy”计数不够。

## Aggregation 与可靠性边界

A-MSDU 的多个子帧放在一个 MPDU 中，共享外层 FCS/Sequence/PN；一个 MPDU 失败会影响其内部所有 MSDU。A-MPDU 中 MPDU 各自有 FCS，可按 BA bitmap 选择性确认。

接收端依据收到的 MPDU Sequence 和本地窗口 reorder；发送端依据 BA 决定重传。不能把 BA 说成接收端的排序输入。BA 成功还不代表 crypto、replay 或上层交付成功。

## 复习追问与答案

**为什么接入优先级不是固定带宽保证？** AIFS/CW 改变获得机会的概率；碰撞、其他 BSS、低速 airtime 和自身队列仍会影响结果。

**聚合为什么可能增加延迟？** 凑包、等待 BA window 和多级排队增加驻留时间；需要同时限定字节数、数量与最大等待时间。

**如何抓一个重传？** 联合 TA、TID、Sequence、Fragment、Retry、时间与会话，而不是只比较 IP ID。

继续：[EDCA 与 Retry](05-edca-aggregation-retry.md)、[BlockAck 窗口演算](04-blockack-reorder-engine.md)。
