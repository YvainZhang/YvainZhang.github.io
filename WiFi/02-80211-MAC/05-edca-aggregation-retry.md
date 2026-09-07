# EDCA、聚合、重传与 Airtime

高吞吐不是由单一高 MCS 决定，而是竞争信道、获得 TXOP、形成足够聚合、在有限 Retry Budget 内被确认的共同结果。

## EDCA 的四组参数

每个 AC 具有 AIFSN、CWmin、CWmax 和 TXOP Limit。发送实体在介质空闲 AIFS 后按 `Uniform[0, CW]` 选择 Backoff，只有 Slot 空闲才递减；检测到 Busy 时冻结。

```text
AIFS[AC] = SIFS + AIFSN[AC] × SlotTime
E[initial_backoff] ≈ CWmin[AC] / 2 × SlotTime
```

碰撞或未确认后竞争窗口通常按 stage 增长并受 CWmax 限制。高优先级 AC 的参数更激进，但多个本地 AC 同时到零还会发生 virtual/internal collision，低优先级 AC 按失败处理。

## NAV 与物理载波侦听

CCA Busy 属于物理载波侦听；NAV 根据帧 Duration 建立虚拟载波侦听。发送条件通常要求两者都允许。调试“Backoff 不动”时要分别记录 PHY CCA reason、NAV expiry、TXOP owner 和 power/channel-switch gate。

RTS/CTS、CTS-to-self 可减少隐藏节点影响或保护混合网络，但增加 airtime。是否启用应依据 packet/aggregate duration、collision cost 和环境，而不是只用 RSSI 阈值。

## 从 MSDU 到 PPDU

```text
MSDU ─┐
MSDU ─┴─ A-MSDU subframes → one MPDU
MPDU ─┐
MPDU ─┼─ delimiters/padding → A-MPDU → PSDU → PPDU
MPDU ─┘
```

A-MSDU 降低每个 MSDU 的 MAC/crypto 开销，但一个 MPDU 失败会影响其中全部子帧。A-MPDU 让多个 MPDU 共享 PHY preamble，并由 BlockAck 选择性确认。两者组合时，调试必须保留 subframe→MPDU→aggregate 的映射。

## 聚合准入条件

并不是同一 TID 的包都能聚合。Scheduler 至少检查：

- Peer/TID BA Session 已建立且 Sequence 落在 TX window；
- cipher、key generation 和保护方式兼容；
- MPDU 数、字节数、delimiter/padding、PPDU duration 不超限制；
- rate/NSS/BW/GI 等 TXVECTOR 能共享；
- latency-sensitive 包不因等待聚合超过 deadline；
- power-save、TWT、channel absence 和 coexistence grant 允许发送。

因此应记录“为何停止继续聚合”的 reason，而不只记录最终 aggregate length。

## Sequence、BA 与 selective retry

发送端为 MPDU 分配 Sequence 后，在 BA window 中保留状态。收到 Compressed BA 时，SSN 决定 bitmap 起点，每一位确认一个 Sequence。未确认 MPDU可以进入 retry，已确认的释放；BAR 可用于推进或重新同步窗口。

需要区分：

- MPDU 从未真正发射；
- 已发射但 PHY abort；
- 已发射、未收到 BA；
- 收到 BA 但 bit 未置位；
- BA 本身解析失败或属于旧 session。

它们对应不同的 Retry、统计和 Rate Control 输入。

## Retry Chain

一次 MPDU 可以按多个 rate stage 重试。Retry Budget 既受 retry count，也受 TXOP、lifetime 和业务 deadline 限制。低速 fallback 提高成功概率，却可能消耗巨大 airtime并阻塞同 BSS 其他 STA。

简化期望 airtime：

```text
E[T] = Σ P(reach stage i) × T_attempt(rate_i)
Goodput ≈ P(success) × delivered_payload / E[T]
```

Rate Control 应以实际 attempt/success 和 airtime 更新，不能把“总线已提交”计作成功样本。

## TXOP 内调度

获得 TXOP 后仍要在 duration、BA window、硬件队列和多 AC 公平之间选择 aggregate。常见策略对 Voice 限制聚合等待，对 Best Effort 追求较大 aggregate，对 Background 控制 airtime。公平性最好按 airtime deficit 评估，而不是 packet round-robin。

## 关键 Trace

每次抽样 TX 记录：Peer/TID/AC、queue delay、AIFS/CW/backoff、CCA/NAV wait、TXOP、aggregate MPDU/bytes、TXVECTOR、per-stage retry、BA SSN/bitmap、最终 reason 和 airtime。

高频路径避免字符串日志；使用定长 binary record 与 ring buffer，在异常触发时冻结。

## 常见根因链

| 现象 | 可能的第一处异常 |
|---|---|
| PHY rate 高但吞吐低 | 聚合等待不足、BA window 卡住、TXOP 碎片化 |
| 小包延迟高 | 过度聚合、队列层级过多、低速 retry 占用 airtime |
| 某 TID 永久停发 | credit/window/key generation 不一致 |
| 吞吐呈周期锯齿 | Rate probing、PS/scan、queue stop/wake 或 BA teardown |
| AP 可见数据但无 BA 推进 | BA policy/SSN/bitmap/session 不一致 |

## 面试追问

- 为什么提高 A-MPDU 上限不一定提升吞吐？
- BA bit 为 0 与完全没收到 BA 的处理有何不同？
- 高优先级 AC 为什么仍可能出现很高尾延迟？
- 如何证明瓶颈在 contention 而不是 Host queue？

## 答题要点与适用边界

A-MPDU 上限只有在有足够同上下文数据、窗口和发送时限时才能利用，配置值不等于实际分布。收到 BA 且某 bit=0与完全没有BA的证据不同，后者无法确认对端的接收集合。高优先级仍受占用中的介质、低速重试和本地排队影响。区分contention与Host等待需要同时记录入队、HIF提交、MAC ready、backoff/NAV和PHY-start时刻。
