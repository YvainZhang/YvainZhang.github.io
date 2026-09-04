# 07 性能工程

Wi-Fi 性能不是一个吞吐数字，而是一组互相制约的指标：Goodput、时延、抖动、丢包、CPU、内存和功耗。优化前必须固定测试拓扑、方向、协议、包长、信道条件与功耗策略。

## 分层预算

```text
PHY Rate
  - 前导码/训练字段
  - 信道竞争与帧间间隔
  - MAC/加密/聚合开销
  - 重试与速率回退
= MAC effective throughput
  - Host bus / copy / scheduling
  - TCP/IP 与应用开销
= Application Goodput
```

继续阅读：

- [吞吐、时延与 CPU 开销分析](01-throughput-latency.md)
- [Rate Control 与链路自适应](02-rate-control-link-adaptation.md)
- [从 PHY Rate 到 Goodput 的性能预算](03-throughput-budget-model.md)

## 本章检查点

- 报告同时给出 PHY、MAC、Bus、netdev 和应用层指标。
- 单向、多流、上下行、UDP/TCP 分开测试。
- 优化收益不以更高尾延迟、内存或功耗为隐藏代价。
