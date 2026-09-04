# Host、Firmware、MAC、PHY 与 Sniffer 多源对齐

芯片问题的根因通常只在两个观测源的缝隙里出现。单独看 Host log、Firmware log 或 Sniffer，都可能得到自洽但错误的结论。

## 统一关联键

不同层未必能共享同一个 ID，可以建立映射链：

```text
case_id
→ host skb cookie
→ HIF descriptor id
→ firmware packet id
→ peer/TID/sequence
→ MAC trace id / PPDU id
→ sniffer TA/RA/TID/Sequence/time
```

控制面使用 transaction ID + session generation；数据面使用 cookie + Sequence/TID；PHY 使用 PPDU/RXVECTOR timestamp。敏感 payload 和 Key 不进入 Trace。

## 时钟对齐

Host monotonic clock、Device TSF/MCU counter、MAC timer 和 Sniffer clock不同。选择一个同时可见的锚点，例如 Host 下发带 cookie 的 vendor test command，Firmware 收到后触发可抓取的帧；用多次锚点估计 offset 与 drift，而不是只做一次平移。

```text
t_device ≈ a × t_host + b
```

长时间测试要考虑 `a` 的频偏和 counter wrap。

## Ring Buffer 与冻结

高频 Trace 应写入固定大小环形缓冲区，记录二进制 event id、参数和 timestamp；离线符号化，避免实时格式化影响调度。Assert/watchdog 先冻结各核 Trace，再收集寄存器、task/stack、Ring pointer、VIF/STA/Key/BA 和 PHY/MAC reason。

## 单包证据模板

| 层 | 预期事件 | 关键字段 |
|---|---|---|
| Host | enqueue/submit/complete | cookie、queue、generation |
| HIF | doorbell/xfer/IRQ | ring slot、length、latency |
| Firmware | schedule/drop | Peer/TID、reason、credit |
| MAC | attempt/ACK/BA | Sequence、retry、TXVECTOR |
| PHY | PPDU/result | MCS/NSS/RU、EVM/PER |
| Air | frame/response | TA/RA、Sequence、Radiotap |

## 根因判定

结论必须包含：第一处偏离、不变量被破坏的机制、支持证据、反证和定向注入。比如“Firmware 没调度”只是位置；若进一步证明 credit 在 reset 分支被重复扣减、Ring 有包而 scheduler 永久认为 credit=0，才是根因。
