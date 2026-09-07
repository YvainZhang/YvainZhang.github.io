# 吞吐、时延与 CPU 开销分析

## 先建立可重复基线

记录 AP/STA 型号和能力、频段、带宽、信道、RSSI、MCS/NSS、距离、干扰、加密、Firmware/Driver 版本、CPU governor、测试协议、方向、并发流数与包长。每个场景预热后运行多轮，报告中位数和波动，而不是只保留最好的一次。

## 瓶颈分类

| 症状 | 优先检查 |
|---|---|
| PHY Rate 低且重试高 | RSSI、噪声、信道、天线、速率控制 |
| PHY Rate 高但 MAC 吞吐低 | 聚合、BA、airtime、PS、加密 |
| Device 侧高但 Host 低 | 总线聚合、credit、RX buffer、错误 |
| netdev 高但应用低 | TCP 窗口、丢包、qdisc、Socket、对端 |
| 吞吐周期性归零 | queue stop/wake、扫描、PS、GC/调度、watchdog |
| CPU 单核打满 | IRQ/NAPI affinity、回调负载、拷贝、锁竞争 |

## 排队与尾延迟

大队列能掩盖瞬时背压，却会产生 Bufferbloat。对交互业务，应观察 p50/p95/p99 RTT 与 queue residence time。合理目标不是“队列永不空”，而是在吞吐稳定时保持有限在途数据，并让高优先级流量不被批量数据长期阻塞。

## CPU 与多核

用 `perf top/record`、ftrace 和软中断统计识别热点。IRQ、完成回调、RX 处理和应用线程若频繁跨核，会增加 Cache miss；全部绑在一个核又可能形成单核瓶颈。调优时一次只改变一个变量，并同时记录吞吐、CPU、软中断和迁移次数。

## 聚合参数

TX/RX 聚合同时存在于 MAC 与 Host Bus。建议观测实际分布，而不只看最大配置：

- 每个 A-MPDU 的 MPDU 数量与字节；
- 每个 URB/SDIO transaction 的 Packet 数；
- 聚合等待时间；
- BA 成功率、重传率和 reorder timeout；
- 内存 high-watermark。

如果提升平均吞吐却恶化小包 RTT、内存或弱信号稳定性，就不是完整收益。

## 实验设计：一次只改变一个因果变量

基线至少拆 TCP/UDP、TX/RX、包长、单流/多流、短时/长稳。TCP 低吞吐可能是拥塞窗口/RTT/重传限制，UDP 提高 offered load 则可能只增加 drop。两者不能仅凭最终 Mbit/s 互相替代。

教学实验表应记录多次运行的中位数、离散程度和尾延迟；对于 p99，还要保存样本数。只有100个样本时，所谓 p99 基本被最慢几次决定，难以证明稳定改善。

| 对照改变 | 预期如果假设成立 | 需要防止的混淆 |
|---|---|---|
| 增加 RX posted buffer | inflight 空洞减少 | 内存与排队增长 |
| 降低 MAC aggregation wait | 小包 queue delay 降低 | 空口效率下降 |
| 固定工作 CPU | migration/cache miss 下降 | 单核饱和 |
| 改变 RSSI/衰减 | retry/MCS 改变 | AP 自适应与温漂 |

## PPS 与 CPU 算例

教学目标为应用 payload 600 Mbit/s，payload 1,500 byte，则约 50,000 packet/s；换成100 byte则为750,000 packet/s。相同吞吐，固定 per-packet 开销相差15倍。

假设平均每包消耗8 μs单核CPU时间：前者约占0.4核，后者约需6核，尚未考虑中断、提交固定成本和内存带宽。由此可预测小包先触发 CPU 瓶颈，而不应继续只看总线字节率。

`CPU_time / packets` 应来自同一统计范围。把整机利用率除以单方向 packet count 会混入应用和对端工作。

## 排队守恒不能直接比较不同字节口径

对同一对象层、同一时间窗：

```text
Δenqueue = Δterminal + (pending_end - pending_start)
Δterminal = Δsuccess + Δdrop + Δcancel
```

Byte counter 跨层包含不同 header、padding 和 retry，需归一化。MAC attempt bytes 高于应用 bytes 是正常现象，不能把差值直接命名为丢包。

## 可操作的定位顺序

先证实空口实际 MCS/重试/airtime和聚合；再确认 Device queue 与 HIF 字节；再比较 Driver RX/NAPI 与 netdev；最后看 TCP/Socket。每轮定位只扩大可疑段的观测。

如果 Device queue 持续增长且 USB inflight归零，Host refill值得怀疑；如果 HIF持续工作、NAPI积压而 CPU热点在复制，则深度增加可能只延后崩溃，需减少消费成本。

## 复习追问与答案

**平均吞吐提高就算优化吗？** 还要检查 p99、内存、功耗、弱信号与公平性，避免把成本转移到别的维度。

**多 TCP 流变快证明什么？** 说明可能绕过单流窗口/调度限制，不能单独证明射频或总线有问题。

**首个不守恒点必然是根因吗？** 它是优先检查位置；计数口径、采样不同步、trace drop和缓存变化也可能造成假差异。

深入：[量化预算](03-throughput-budget-model.md)、[USB 案例](../Case-Studies/02-usb-rx-throughput.md)。
