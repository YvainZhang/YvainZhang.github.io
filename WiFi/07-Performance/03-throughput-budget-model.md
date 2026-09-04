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
