# 从 PHY Rate 到 Goodput 的性能预算

优化前先建立预算，否则只能在 CPU affinity、聚合和队列参数之间盲试。

## 空口预算

单次成功传输的近似 airtime：

```text
T_success = AIFS + E[backoff] + T_PPDU + SIFS + T_ACK_or_BA
```

考虑失败概率 `p` 和 retry chain 后，分母还要加入失败尝试及更低速重传的 airtime。应用 Goodput 进一步扣除 MAC header、delimiter/padding、加密、LLC/IP/TCP、总线封装与空包等待。

不要用 `PHY rate × 固定系数` 作为跨场景模型：不同 PPDU、聚合深度、包长、竞争者和 retry 会让系数发生根本变化。

## Host Interface 覆盖条件

若平均一次提交从 Host 到资源归还的往返时间为 `L`，目标总线数据率为 `R`，至少需要约 `R × L` 的在途字节才能覆盖流水线空洞：

```text
required_inflight_bytes >= target_bus_rate × completion_latency
```

这是下界，实际还要考虑抖动、聚合边界和控制流量预留。URB/Ring 深度不足表现为周期性空闲；无限增大则提高内存与排队延迟。

## CPU 预算

把 CPU 成本拆成固定提交成本、每包成本和每字节成本：

```text
CPU_time ≈ submissions × C_submit
         + packets × C_packet
         + bytes × C_byte
```

总线/MAC 聚合主要降低前两项；zero-copy 主要降低第三项。但更大聚合增加等待和 burst，必须同时测 p95/p99 latency。

## 分层守恒

在同一时间窗记录：Air RX/TX bytes、Firmware enqueue/drop、bus submit/complete、Driver packets/drop、netdev bytes 和应用 bytes。第一处差异持续扩大才是瓶颈候选；瞬时差异可能只是排队。

## 报告模板

| 层 | Rate/量 | Queue/延迟 | Drop/Retry | CPU/功耗 |
|---|---:|---:|---:|---:|
| PHY/MAC | MCS/NSS/RU、airtime | BA/window | PER/retry | RF active |
| Firmware | enqueue/dequeue | residence p99 | reason | task latency |
| Bus | bytes/s、xfer size | completion p99 | errors | IRQ/CPU |
| Host | pps/Gbps | NAPI/qdisc p99 | SKB drop | softirq |
| App | Goodput | RTT p99 | TCP retrans | total power |

任何优化都应说明收益从哪一项预算得到，以及代价落在哪一项。

## 完整教学算例：空口、总线、CPU三项约束

以下数字只用于算式复核，不代表任何芯片实测或标准上限。假设每次成功聚合交付32个1,500 byte应用payload，整个PPDU实际占用600 μs；AIFS=43 μs、平均退避67.5 μs、SIFS=16 μs、BA=44 μs，暂忽略失败和竞争冻结。

```text
Payload = 32 × 1500 × 8 = 384000 bit
Cycle = 43 + 67.5 + 600 + 16 + 44 = 770.5 μs
Goodput = 384000 / 770.5 ≈ 498.38 Mbit/s
```

PPDU 600 μs已含其内部训练/信令和数据；不能再重复加preamble。假设每10次成功还多消耗一次500 μs失败，则平均每个成功多50 μs，Goodput降到约468.01 Mbit/s。真实系统用测得的attempt airtime分布，不能固定用一个PER系数乘吞吐。

## HIF在途容量

若希望有效传输600 Mbit/s即75 MB/s，资源归还平均延迟0.8 ms，则至少约60,000 byte有效在途容量。若每个URB真正承载16 KiB有效数据，平均条件下至少4个；抖动、请求短包、控制预留和调度空洞要求额外裕量。

若误把600 Mbit/s当600 MB/s，容量会算大8倍。若拿最大URB长度而非实际有效长度计算，则可能严重低估需要的请求数。

容量不是越大越好。120 KiB额外排队在75 MB/s下约产生1.64 ms服务时间，低速链路下会更长。用p99完成延迟设计裕量，同时监测内存和业务deadline。

## Little定律与稳定性

稳定系统、同口径对象中 `平均队列对象数 = 到达率 × 平均驻留时间`。50,000 packet/s、平均Driver驻留2 ms，对应平均约100 packet；该均值不代表最大队列，也不能推出p99。

若到达率长期超过服务率，队列不稳定，公式不能用有限窗口的表面均值掩盖持续增长。必须通过背压、admission或丢弃恢复有界性。

## TCP的独立上界

在窗口限制为主的简化条件下，吞吐约受 `inflight TCP bytes / RTT` 限制。256 KiB窗口、10 ms RTT，对应约209.72 Mbit/s，即便空口预算接近500 Mbit/s也无法单流跑满。

还要区分接收窗口与拥塞窗口，加入重传、delayed ACK、应用供给和对端性能。UDP跑满不能证明TCP实现有bug，只说明约束不同。

## 复习追问与答案

**总线上限与空口上限能相加吗？** 端到端受最慢服务段限制，且共享CPU/队列使它们相互影响；通常不能简单相加。

**R×L为什么只是容量起点？** 它覆盖均值流水线，不覆盖抖动、有效负载率、控制预留与突发。

**需要哪些原始数据复现结论？** 包长/有效字节、PPDU/BA/竞争时间、attempt分布、HIF完成延迟、CPU时间与TCP RTT/window，并记录采样窗口。
