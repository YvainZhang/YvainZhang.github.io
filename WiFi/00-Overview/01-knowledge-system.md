# Wi-Fi 芯片知识体系与掌握标准

这套 Atlas 不以“读过多少协议名词”为目标，而以能否解释、设计、验证和定位一条真实芯片链路为标准。每个主题都应同时落在协议、实现和证据三个坐标中。

## 六级掌握模型

| 级别 | 能力 | 可验证输出 |
|---|---|---|
| L0 名词 | 知道缩写和用途 | 能给出一句准确解释 |
| L1 关系 | 知道上下游和边界 | 能画模块图、区分相近概念 |
| L2 路径 | 能走完正常流程 | 能画 TX/RX 或状态时序 |
| L3 实现 | 知道数据结构和所有权 | 能定义 Context、Descriptor、Ring、状态机 |
| L4 异常 | 能推演竞态和失败分支 | 能列不变量、超时、回绕和恢复策略 |
| L5 证据 | 能用数据证明根因 | 能设计 Trace、计数、抓包和注入实验 |

博客正文至少达到 L3；标为“深入”的文章应达到 L4/L5。只介绍概念的页面保留为模块索引，不计作深入文章。

## 十二模块覆盖矩阵

| 模块 | 必须掌握的实现对象 | 必须能回答的系统问题 | 最小证据 |
|---|---|---|---|
| 01 架构 | VIF/Peer/TID、控制面、数据面、责任边界 | 一个包和一个连接分别由谁推进？ | 端到端时序、所有权表 |
| 02 MAC | EDCA、NAV、TSF、BA、Retry、Trigger | 哪些动作必须在 SIFS 内完成？ | MAC trace、BA bitmap、air capture |
| 03 建链安全 | Scan/BSS、Auth/Assoc、Key、Port | “关联成功”为什么仍不能传业务？ | nl80211、EAPOL、key generation |
| 04 Linux | skb、qdisc、netdev queue、NAPI | SKB 在什么时刻换所有者？ | tracepoint、queue/softirq 统计 |
| 05 Driver/FW | ABI、Command/Event、Task、Context | Host 与 Device 如何拒绝迟到事件？ | transaction、generation、dump |
| 06 总线 | DMA/URB/CMD53、Ring、Credit、Doorbell | 可见性、容量与完成语义如何保证？ | producer/consumer、completion latency |
| 07 性能 | Airtime、Goodput、Queue、CPU budget | 第一处不守恒发生在哪里？ | 分层计数、直方图、perf |
| 08 功耗 | PS、U-APSD、TWT、runtime PM、WoWLAN | 谁允许关钟，谁负责唤醒和恢复？ | power state trace、wake reason |
| 09 并发 | SCC/MCC/DBAC、角色、信道、共存 | RF/MAC/PHY 资源怎样被多个角色共享？ | dwell、missed TBTT、grant trace |
| 10 调试 | 统一时间线、Correlation、Freeze | 如何从现象收敛到唯一可证伪假设？ | 多源对齐、fault injection |
| 11 PHY/RF | Vector、同步、信道估计、EVM、校准 | 一次 PHY error 应归因到哪个阶段？ | vector、error code、仪表结果 |
| 12 产品化 | Golden model、UVM、Bring-up、ATE | 如何把实验室结果变成可量产结论？ | coverage、limit、版本与追溯 |

## 四条贯穿全库的主线

### 数据所有权

每个 Buffer 都必须能回答：当前归 Host、总线、Firmware 还是 Hardware；谁可以释放；错误和 Reset 如何归还。`NETDEV_TX_OK`、URB completion、DMA completion、MAC ACK 是四种不同的完成语义。

### 状态所有权

连接、Peer、Key、BA、功耗状态不能由多个层“各自认为”已经切换。每个状态需要唯一权威所有者，其他层通过带 generation 的 Command/Event 建立镜像。

### 时间约束

系统同时存在微秒级 SIFS fast path、毫秒级总线/调度、秒级连接超时。不能让 Host round-trip 参与 ACK/BA/Trigger Response，也不能用 SIFS 思维设计用户态状态机。

### 守恒与不变量

排查时优先比较守恒关系，而不是搜索错误字符串：

```text
enqueue = dequeue + queued + drop
submit  = complete + inflight + cancel
trigger_matched = response + explicit_failure
ring_used = producer - consumer
```

守恒第一次破坏的位置，通常比最后出现错误日志的位置更接近根因。

## 面试表达模板

回答一个系统问题时按六步展开：

1. **先限定场景**：STA/AP、SoftMAC/FullMAC、PCIe/USB/SDIO、TX/RX。
2. **给出主路径**：从入口到空口或从现象到证据，不跳层。
3. **指出关键对象**：SKB、Descriptor、Context、Ring、Vector 或状态机。
4. **说明所有权与并发**：谁修改、在哪个上下文、用什么同步。
5. **给出失败分支**：超时、重试、回绕、Reset、迟到事件。
6. **落到验证**：计数、Trace、Sniffer、仪表或故障注入。

如果只能说“标准规定了什么”，面试官会继续追问实现；如果只能说“代码这样写”，还会继续追问为什么。完整回答应把标准约束、实现选择和验证证据连成一条链。

## 自测方式

- 不看资料画出普通 EDCA TX、HE TB TX、RX reorder、四次握手和 suspend/resume 五张时序图。
- 从一个 DHCP 包出发，说清每次封装、排队、所有权转移和完成。
- 给出一个“吞吐周期性归零”的最小观测集合，而不是列十个可能原因。
- 解释一次 Firmware Reset 如何避免旧 Event、旧 DMA 和旧 Key 污染新 Session。
- 对任何性能数字同时给出场景、分母、统计窗口和代价。
