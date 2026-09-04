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

普通单播 MPDU 通常由 ACK 确认。建立 BA Session 后，一段 Sequence Number 窗口由 Block ACK 位图批量确认，接收端据此重排序。分析异常时关注：

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
