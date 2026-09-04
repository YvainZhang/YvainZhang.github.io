# Rate Control 与链路自适应

速率控制不是 RSSI 到 MCS 的查表。它是在未知且变化的信道上，选择“期望有效吞吐最大”的发送策略，并为失败准备 retry chain。

## 目标函数

对候选速率 `r`，最简单的近似是：

```text
expected_goodput(r)
= payload_bits × success_probability(r)
  / expected_airtime(r)
```

`expected_airtime` 必须包含 preamble、数据 symbol、SIFS、ACK/BA、平均 backoff 与预期重试；只比较 PHY Rate 会系统性偏向高 MCS。小包、A-MPDU、不同 RU 和不同 ACK policy 的固定开销差异很大。

## 输入与输出

输入包括每个 rate 的 attempt/success、BA bitmap、retry、RSSI/SNR/EVM、移动性、带宽/NSS、RU、包长与时延等级。输出包括 initial rate、retry chain、MCS/NSS/BW/GI/LTF/coding、RTS policy 和可能的 TX power backoff。

RSSI 只应作为先验或快速降档依据。相同 RSSI 在不同干扰、多径、EVM 和接收机实现下具有不同 PER；真正闭环证据来自发送结果。

## Sampling 与稳定性

算法需要探索未使用速率，否则链路改善后无法升档；但探索比例过高会增加丢包和尾延迟。建议按 Peer/TID 或 traffic class 区分 bulk 与 latency-sensitive 流量，并在 roam、带宽变化、SMPS 和长时间空闲后重置或衰减历史。

## OFDMA 特殊性

RU 大小改变 tone 数、符号承载和链路预算，不能直接复用 full-band 成功率。UL HE TB 的 MCS/power 还受 Trigger 指定；STA 的 rate control 更像能力与建议输入，最终参数由 AP Scheduler 决定。AP 则要联合优化 RU、MCS、duration、用户组合与公平性。

## Debug 视图

按 rate/RU 输出 attempts、success、retry depth、airtime、sample count 和 EWMA probability；再关联最终 TXVECTOR 与 Sniffer。若算法选择 MCS 很高但硬件实际 fallback，Host 的“selected rate”不能代表空口事实。

评估不仅看峰值吞吐，还要覆盖弱信号、移动、窄带干扰、短包、上下行、单流/多流和恢复时间。
