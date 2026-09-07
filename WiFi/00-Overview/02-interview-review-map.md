# 面试复习图谱：从问题追到芯片实现

这不是背诵题库。每组问题都给出面试官真正想确认的能力，以及回答必须覆盖的实现锚点。

## 1. 请讲一次 Wi-Fi TX

[展开正文与算例](../01-System-Architecture/01-end-to-end-data-path.md)

合格回答不能停在“协议栈→驱动→硬件”。至少覆盖：

- Socket/TCP/IP 形成 SKB，qdisc 选择 netdev TX queue；
- `ndo_start_xmit()` 的所有权语义以及 stop/wake 条件；
- priority/DSCP 如何映射 UP、TID、AC 和 Firmware queue；
- Host descriptor 如何携带 VIF、Peer、TID、长度、offload 与 cookie；
- Ring/Credit/URB/CMD53 如何建立在途事务；
- Firmware 如何做 admission、aggregation、rate/retry 和 power-state gating；
- Hardware MAC 如何执行 EDCA、NAV、加密、Sequence、A-MPDU 与 ACK/BA；
- PHY 如何根据 TXVECTOR 生成 PPDU，RF 如何完成上变频和发射；
- Bus completion、TX done、air ACK 的区别。

追问通常落在：“什么时候可以释放 SKB？”“队列满时为什么不能总返回 BUSY？”“总线成功是否等于发送成功？”

## 2. 请讲一次 Wi-Fi RX

[展开正文与算例](../04-Linux-Stack/02-skb-netdev-napi.md)

从 Packet Detect、AGC、同步、CFO、Channel Estimation 开始，经 FEC/CRC、MAC filter、decrypt/replay、duplicate、reorder/deaggregate，进入 Firmware buffer 和 Host RX。必须说明：

- RXVECTOR 与 RX descriptor 各表达什么；
- FCS、MIC、PN、Sequence 的检查顺序与 offload 边界；
- A-MPDU、A-MSDU 拆分后哪些元数据共享；
- reorder 位于 Hardware、Firmware、Driver 或 mac80211 时接口有何不同；
- NAPI budget、buffer refill 和 interrupt masking 如何避免丢中断；
- 802.11→802.3 转换位于哪里。

## 3. FullMAC 与 SoftMAC 的本质差异是什么

[展开正文与算例](../04-Linux-Stack/01-linux-wifi-stack.md)

不要只回答“MAC 在固件还是 Host”。真正差异是控制状态机、实时决策、数据封装和可观测性的责任边界。现实产品常是混合卸载：Host 使用 cfg80211，Firmware 负责连接和聚合，Hardware 完成 SIFS 响应。应能举出扫描、认证、Rate Control、reorder 和加密分别可能放在哪里，以及迁移边界后 ABI 需要增加什么语义。

## 4. EDCA 为什么会影响吞吐和尾延迟

[展开正文与算例](../02-80211-MAC/05-edca-aggregation-retry.md)

回答 AIFS、CWmin/CWmax、随机 Backoff、TXOP、Retry stage 与 Internal Collision。进一步解释高优先级不等于绝对优先；更小竞争窗口提升机会，也可能导致同类节点碰撞。调试要看 airtime、queue residence、contention/retry histogram，而不是只看 AC 包数。

## 5. A-MSDU 与 A-MPDU 如何组合

[展开正文与算例](../02-80211-MAC/01-mac-air-interface.md)

说明 MSDU/MPDU/PSDU/PPDU 层次、Delimiter、Padding、BlockAck 粒度和错误影响面。A-MSDU 子帧共享外层 MPDU 的 Sequence/PN；A-MPDU 中各 MPDU 可被 BA bitmap 选择性确认。聚合策略受 BA window、PPDU duration、Peer capability、cipher、latency budget 和 buffer 限制。

## 6. BlockAck 与 reorder 最容易错在哪里

[展开正文与算例](../02-80211-MAC/04-blockack-reorder-engine.md)

必须讨论 12-bit Sequence modulo 4096、window head、SSN、bitmap、BAR、timeout release、duplicate 和 teardown。直接用整数比较 Sequence 会在回绕处失败；旧 session 的迟到帧需要 generation 隔离。BA 生成属于 SIFS fast path，Host 上送属于 slow path，两者不应互相阻塞。

## 7. Wi-Fi 6 OFDMA 的难点是什么

[展开正文与算例](../02-80211-MAC/03-he-ofdma-trigger-path.md)

不是“把带宽切成 RU”，而是多用户在同一 PPDU 内完成频率、时间、功率和 duration 对齐。DL HE MU 需要 AP Scheduler 选择 user/RU/MCS；UL HE TB 要在 Trigger 后 SIFS 内解析 AID12、RU、UL length、GI/LTF、coding、target RSSI 并发射。Host 只能预配置上下文，不能参与实时响应。

## 8. 四次握手之后为什么仍可能没有数据

[展开正文与算例](../03-Connection-Security/03-wpa-roam-port-state.md)

区分 PTK 本地派生、GTK 在 M3 Key Data 中传递、Key 安装、controlled port authorization 和数据队列放行。检查 EAPOL replay counter、M3/M4 重传、Key index/generation、硬件表项生效时机、TX PN 与 RX replay context。不能记录密钥本身，只记录元数据和状态。

## 9. `NETDEV_TX_OK` 与 `NETDEV_TX_BUSY` 的所有权语义

[展开正文与算例](../04-Linux-Stack/02-skb-netdev-napi.md)

返回 OK 后 Driver 接管 SKB，最终必须完成或释放；返回 BUSY 时不能保留或释放它。正常背压应在资源接近耗尽前 stop queue，并在资源真正可用后 wake。经典竞态是“检查无资源→准备 stop”之间发生 completion，导致永久停队，因此 stop 后要重新检查资源。

## 10. NAPI 为什么能缓解中断风暴

[展开正文与算例](../04-Linux-Stack/03-qos-qdisc-driver-flow-control.md)

中断只负责屏蔽/调度 NAPI，poll 在 budget 内批量消费。队列未空则继续 poll；完成前先确认队列为空，再恢复中断，并处理“恢复中断前新 completion 到达”的 lost-interrupt 窗口。要同时管理 RX refill，避免 poll 很快但没有可供 Device 使用的 Buffer。

## 11. DMA Ring 为什么需要内存屏障

[展开正文与算例](../06-Bus-Data-Path/02-ring-dma-memory-ordering.md)

CPU、Device 与总线观察写入的顺序可能不同。发布方必须确保 payload 和 descriptor 字段先可见，再发布 owner/valid、producer 和 doorbell；消费方先观察 completion/owner，再读取其余字段。`volatile` 只约束编译器，不能替代 DMA mapping、cache sync 和 memory ordering。

## 12. Ring 与 Credit 有什么区别

[展开正文与算例](../06-Bus-Data-Path/02-ring-dma-memory-ordering.md)

Ring slot 是 Host Interface 容量；Credit 可能代表 Firmware 内部 buffer、queue 或 Peer/TID 配额。两者必须同时满足才能提交，也可能在不同完成阶段归还。Reset 若只重置其中一侧，最容易形成“Ring 有空位但永不发包”的永久背压。

## 13. Command/Event ABI 如何演进

[展开正文与算例](../05-Driver-Firmware/02-host-device-abi.md)

Header 至少包含 type、version、length、transaction、generation 和 flags。接收方先验证长度与版本，再访问可选字段；不要裸拷贝编译器结构体。同步命令需要 deadline、pending table、cancel 语义；异步 Event 必须用 VIF/Peer/session generation 拒绝旧结果。

## 14. Firmware Watchdog 应该监控什么

[展开正文与算例](../05-Driver-Firmware/03-firmware-state-machines.md)

只喂一个全局狗无法发现单 Task 饥饿。应观察 scheduler heartbeat、关键 task progress、interrupt progress、command age、ring movement 和 deadline miss。Dump 在 Reset 前冻结，至少保存 task/stack、关键 context、ring indices、最近事件和硬件错误寄存器。

## 15. Suspend/Resume 最危险的竞态

[展开正文与算例](../08-Power/02-wowlan-suspend-resume.md)

Suspend 必须停止新入口、排空或冻结队列、配置 WoWLAN/offload、同步 Key/PN/GTK rekey 状态、确认 Device 可睡，再关闭 Bus/Clock。Resume 顺序相反但不能简单倒放：先恢复供电/总线和 Firmware 通信，再同步 wake reason、Key/PN、连接状态，最后开放数据队列。迟到 completion 和 wake event 要靠 generation 处理。

## 16. 如何从 PHY Rate 推导 Goodput

[展开正文与算例](../07-Performance/03-throughput-budget-model.md)

先计算 `AIFS + E[backoff] + PPDU + SIFS + ACK/BA` 的 airtime，再加入 retry chain，最后扣除 Preamble、MAC/LLC/IP/TCP、Delimiter/Padding 和空包等待。Host 总线还要满足 `inflight >= target_rate × completion_latency`。因此不存在跨包长、聚合和竞争场景通用的“PHY rate 乘固定系数”。

## 17. Rate Control 的目标函数是什么

[展开正文与算例](../07-Performance/02-rate-control-link-adaptation.md)

不是最大 MCS，而是最大期望有效吞吐或满足 latency/reliability 约束。简化模型为 `expected_goodput = success_probability × payload_bits / expected_airtime`。输入包括 per-rate success、RSSI/EVM、retry、aggregation、移动性和 RU；采样要避免只用成功历史导致无法探索，也要避免过度 probing 引入抖动。

## 18. SCC、MCC、DBAC 如何区分

[展开正文与算例](../09-Scenarios-Integration/02-concurrency-coexistence.md)

- SCC：多个角色共享同一信道，主要竞争 airtime 和时序；
- MCC：单 Radio 在不同信道间切换，存在 dwell、switch cost、missed TBTT 和 off-channel latency；
- DBAC/DBDC/DBS：厂商命名并不统一，先核对实际同时工作能力与独立 RF/PHY/MAC/clock/antenna 资源；不能仅从名称推出两路并行。
- 即使支持双 Radio simultaneous，datapath、总线、热与功耗仍可能共享。

回答时应画出资源矩阵，而不是只背缩写。

## 19. EVM、PER、RSSI、SNR 的关系

[展开正文与算例](../11-PHY-RF-Calibration/02-rf-calibration-metrics.md)

RSSI 是接收功率估计，SNR 依赖信号与噪声参考，EVM 描述解调星座误差，PER 是整个接收链和协议条件下的结果。高 RSSI 不保证低 EVM；PA 非线性、phase noise、IQ imbalance、CFO 和 clipping 都可能在强信号下恶化 EVM。比较指标前必须统一 reference plane、bandwidth、chain、温度与校准状态。

## 20. First Silicon Bring-up 顺序

[展开正文与算例](../12-Validation-Productization/01-validation-bringup.md)

遵循“可供电、可访问、可观测、可发、可收、可闭环”：电源/时钟/Reset→JTAG/寄存器/内存→Firmware download/heartbeat→中断/DMA→数字 loopback→conducted CW/packet TX→RX detect/sync/decode→MAC ACK/BA→连接→性能与功耗。不要一开始就用完整 OTA 连接掩盖层次。

## 21. 如何证明根因而不是相关性

[展开正文与算例](../10-Debug-Recovery/01-evidence-workflow.md)

先建立单包 correlation key 和统一时间线，找第一处不守恒；提出可证伪假设，再改变一个变量或做故障注入。根因结论至少包含：必要条件、触发机制、证据、修复为何打断机制、回归如何覆盖边界。一次“改完没复现”不是闭环。

## 22. 面试前的五张白板图

1. 普通 TX/RX 与四种 completion；
2. EDCA + A-MPDU + BA/reorder；
3. Host–Device Ring/Credit/Command/Event；
4. HE Trigger → HE TB → Multi-STA BA；
5. Suspend/WoWLAN/Resume 与 Reset generation。

能在每张图上标出所有权、时限、失败分支和观测点，才说明知识真正连成了系统。
