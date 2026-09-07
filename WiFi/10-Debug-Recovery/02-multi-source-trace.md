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

## 时钟拟合必须带不确定度

Host发送命令时刻h1、收到回显h2，Device记录d。若暂按链路对称模型，可用 `(h1+h2)/2` 作为对应Host时刻，offset估计为 `d-(h1+h2)/2`。但误差可能达到半个往返时间，并受排队不对称影响。

用多组锚点拟合drift与offset，优先选择低往返样本，并报告残差。不能用100 μs不确定度的时钟对齐断言两个相差2 μs事件的因果先后。

教学例：起点Host=0 s对应Device=0 s，100 s后Device=100.002 s，漂移约20 ppm。只减一个固定offset会在100秒后产生2 ms错位，足以误判一轮调度。

## Counter回绕与复位

32-bit微秒计数器约每4294.97秒回绕一次。先用连续采样恢复扩展计数，再拟合时钟；Device Reset把counter清零不是自然回绕，需要boot generation区分。

TSF可能受BSS同步和角色影响，不应假定它与MCU monotonic timer完全等价。Trace元数据记录clock source、频率、位宽、复位规则和采样点。

## 单包映射与聚合

一个USB aggregate对应多个Packet，一个PPDU包含多个MPDU，一个MPDU可重传多次。建立显式父子表：

```text
transfer_id → [(cookie, subpacket_offset, length)]
cookie + session → (peer, TID, Sequence)
PPDU_id → [(Sequence, attempt_index, rate)]
```

Sequence在4096处回绕且不同TID可重复，还需TA/Peer、方向、session和时间。仅按Sequence join会把不同连接或重传错误匹配。

## 一条教学时间线

| Host校准时刻 | 事件 | 推断 |
|---|---|---|
| 0 ms | accepted cookie=42 | 已进入Driver责任域 |
| 0.3 ms | bus complete | transport已交付，不证明空口 |
| 0.4 ms | FW queue push | Device有数据 |
| 8.4 ms | grant允许 | 前8 ms主要等调度/共存 |
| 8.5 ms | PHY TX end | 实际发射 |
| 8.6 ms | terminal TX status | 结合具体reason判断 |

这是教学数据，不是实测。若直接用accepted→TX status统称“USB latency”，就会把调度等待归错层。

## 多核冻结与内存可见性

每核trace ring保存独立producer和序号；冻结请求不必在所有核同一周期生效，应记录每个核实际freeze时刻。Dump读取ring前仍需保证写入可见，防止读到半条record。

恢复后解析器按build ID选择符号/字段版本；旧解析器把新event layout读成合法数字比直接报错更危险。

## 复习追问与答案

**一个时间锚点够吗？** 只能估计某时刻offset，无法辨认drift和传输抖动。

**怎样处理未匹配Packet？** 保留unmatched、trace-loss、expired-session和sampling原因，不强行匹配最近Sequence。

**能否在不同源间比较纳秒精度？** 精度由最弱时钟、采样点和校准误差决定，输出更多小数位不增加可信度。
