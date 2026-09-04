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
