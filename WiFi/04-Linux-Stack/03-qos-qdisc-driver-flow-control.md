# QoS、qdisc、多队列与 Driver Flow Control

Host 侧 TX 不是一个 FIFO。一个 SKB 可能经历 socket pacing、qdisc、traffic class、netdev TX queue、Driver software queue、Firmware TID queue 和 Hardware AC queue。

## 分类链路

常见映射是：

```text
DSCP / socket priority
→ skb->priority
→ 802.1D User Priority
→ 802.11 TID (0..7)
→ Access Category (VO/VI/BE/BK)
→ netdev/Firmware/Hardware queue
```

映射不是永远一一对应。VLAN、cgroup、qdisc、Driver policy、AP WMM admission 和平台策略都可能改写。调试 QoS 必须同时记录原始 DSCP、最终 TID/AC 与实际 queue，不能只看应用设置。

## qdisc 与 netdev TX queue

qdisc 决定软件排队、调度、整形或丢弃；多 TX queue 允许按 CPU/flow/traffic class 分散锁和执行。`ndo_select_queue()` 或框架映射选出 queue 后，`ndo_start_xmit()` 接受 SKB。

需要区分：

- qdisc backlog：Driver 尚未拥有；
- netdev queue stopped：内核暂不调用 Driver；
- Driver/Firmware queue：Driver 已拥有；
- Hardware queue：已进入 Device 调度；
- air pending：已获得或正在竞争 TXOP。

仅观察 `tx_queue_len` 解释不了后四级积压。

## Stop/Wake 的无丢唤醒模式

安全的背压逻辑通常是：

```text
fast path sees low resources
→ stop corresponding netdev subqueue
→ memory/order synchronization
→ recheck resources
→ if completion raced and resources exist, wake immediately
```

Completion 路径先归还 Ring/Credit，再发布可见性，最后 wake。若先 wake 后归还，Stack 可能立即再次进入并看到旧资源状态；若 stop 后不复查，刚发生的 completion 可能成为最后一次 wake，形成永久停队。

Stop/wake 应精确到受影响 subqueue，避免一个 TID/Peer 堵塞停止所有业务。

## BQL、队列与 Bufferbloat

Byte Queue Limits 的思想是根据完成反馈限制 Driver/Device 在途字节，避免软件看不到的深队列。Wi-Fi 中 completion 语义复杂：总线完成不代表空口完成，因此用于调节队列的反馈点必须明确。

吞吐场景需要足够 inflight 覆盖总线和调度延迟；交互场景又要求有限 queue residence。应按 AC/TID 记录字节、包数和驻留时间分布，而不是只设一个全局最大队列。

## SKB 元数据与 offload

Driver 需要正确处理 linear/non-linear data、fragments、headroom、checksum/GSO、VLAN、priority 和 cloned/shared buffer。是否可 zero-copy 取决于总线 DMA 能力、对齐、生命周期和 Firmware descriptor，而不仅是“减少 memcpy”。

SG 列表要校验段数、长度总和、DMA mapping 结果和硬件边界；失败路径逐项 unmap，不能假定全部成功。

## RX NAPI 细节

典型流程：IRQ 屏蔽 RX source 并 schedule NAPI；poll 消费最多 budget 个 packet；队列空时调用 complete 并恢复中断。关键竞态是 Device 在“确认队列空”和“恢复中断”之间产生 completion。

常见规避方式依赖硬件：恢复后重新检查 producer/consumer、使用 cause/doorbell handshake，或让 level-triggered interrupt 在未清空时保持。无论方案如何，都要把不丢唤醒写成不变量。

RX buffer refill 是独立资源环：

```text
posted = device_owned + completed
completed = napi_pending + delivered + dropped
```

内存压力下 refill 失败若没有退避与恢复机制，会表现为“中断正常但永远收不到新包”。

## 并发上下文

需要标出每个路径运行于 process、softirq/NAPI、hardirq、workqueue 还是 bus callback。锁选择取决于上下文；可能睡眠的操作不能进入 softirq/hardirq。跨 CPU producer/consumer 使用明确的 atomic/lock/barrier，不靠普通字段“通常没问题”。

## 可观测性

按 subqueue/AC/TID 记录 qdisc backlog、stop/wake reason、stop duration、Driver queue depth、Ring/Credit、completion batch、NAPI polls/budget exhaust、refill failure、GRO 和 drop reason。

配合 tracepoint/perf 观察 `net_dev_queue`、`net_dev_xmit`、softirq、IRQ affinity 和热点函数。先建立分层计数差分，再开启单包 Trace。

## 面试追问

- `NETDEV_TX_BUSY` 为什么不适合做正常流控？
- stop/wake 怎样发生 lost wakeup？
- qdisc backlog 为零为什么 Device 内仍可能排了大量包？
- NAPI complete 与恢复中断之间怎样避免漏包？

## 答题要点与适用边界

正常流控应提前停止相应队列，BUSY保留Stack所有权，不能作为无界重试机制。Completion先wake、发送方后stop可导致lost wakeup，需锁或stop后复查。qdisc为零只表示其自身无积压，Driver/FW仍可能持有大量包。NAPI完成与IRQ恢复要遵循budget/返回值要求，并结合硬件cause语义防止漏通知；详见本模块SKB/NAPI正文。
