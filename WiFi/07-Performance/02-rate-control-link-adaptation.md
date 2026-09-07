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

## 两个候选速率的教学选择

假设每次尝试传相同12,000有效bit，候选A包含固定开销的尝试airtime为200 μs、成功率0.95，B为150 μs、成功率0.65。单次尝试的期望交付率：

```text
A: 12000 × 0.95 / 200 μs = 57 Mbit/s
B: 12000 × 0.65 / 150 μs = 52 Mbit/s
```

B的PHY速率更高也可能收益更低。这里是单次尝试模型；若再把重试后的最终成功概率放入分子，分母必须同步变成整个 retry chain 的期望时间，不能重复计算或漏算重试。

## Retry chain 的概率模型

两阶段最多各尝试一次，成功率p1、p2，每阶段耗时T1、T2，简化独立模型：

```text
P_delivered = p1 + (1-p1) × p2
E_time = T1 + (1-p1) × T2
Expected_goodput = L × P_delivered / E_time
```

实际各次失败相关、竞争窗口会变化、聚合也会改变样本。这个模型用于检查方向和预算，不替代真实 per-stage airtime 测量。

## 更新统计的口径

对 A-MPDU，PPDU success 一个布尔值不能表达每个MPDU是否被BA确认。Rate样本应说明 attempt按MPDU还是PPDU计、BA丢失如何归类、PHY abort是否进入失败样本。

一种平滑方案为 `p_new=(1-α)p_old+αp_batch`。α大响应快但抖动，α小稳定但跟踪慢；低流量时还要记录样本置信程度。不能把0次尝试当0成功率。

## 探索、退化与重新学习

长时间空闲后信道可能变了，应降低旧统计权重；漫游到新Peer、带宽/RU改变或stream数改变时，必须区分历史有效范围。探测速率与正常发送比例需要受业务deadline约束。

RSSI突降可作为快速退化信号，但高retry也可能来自碰撞；一味降MCS增加占空时间，反而让拥塞更严重。可结合CCA、碰撞保护试验、EVM和peer结果交叉判断。

## 复习追问与答案

**最优MCS由RSSI唯一决定吗？** 不，干扰、channel matrix、payload/聚合和接收机差异都影响PER。

**AP下发HE TB MCS时STA还做什么？** 校验所选参数、功率与buffer约束并执行对应响应；最终本次参数受Trigger控制。

**怎样发现算法输出未被执行？** 同时记录selected chain、硬件实际attempt vector和空口观测，检查fallback/限制覆盖。

关联：[OFDMA](../02-80211-MAC/03-he-ofdma-trigger-path.md)、[MAC重试](../02-80211-MAC/05-edca-aggregation-retry.md)。
