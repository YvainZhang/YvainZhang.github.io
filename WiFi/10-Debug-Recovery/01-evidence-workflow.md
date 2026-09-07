# 建立可复现的 Wi-Fi 证据链

## 1. 固化现象

先写清角色、拓扑、频段、信道、AP/对端、版本、复现概率、持续时间和判定标准。“断网”要被改写为更精确的事实，例如“关联保持，连续 5 秒没有 RX 数据，ARP Request 在 Host TX 可见但空口不可见”。

## 2. 建立统一时间线

为一次测试分配 case ID，在用户态、Driver、Firmware 和抓包中打同一标记。优先使用 monotonic timestamp；若设备与 Host 时钟不同，通过一个可同时观测的命令/事件估算偏移。

```text
T0 user action
T1 nl80211 command
T2 driver command submit
T3 bus completion
T4 firmware event
T5 cfg80211 event
T6 first/last packet
```

## 3. 用不变量缩小范围

- 连接状态转换必须成对且 session 一致。
- enqueue、complete、drop 与 pending 应大致守恒。
- Sequence/BA window 应持续推进。
- queue stop 必须有对应 wake 或 teardown。
- suspend 进入必须有明确退出或失败回滚。

## 4. 逐层增加观测

第一轮只收集关键事件与计数，确认问题位于控制面还是数据面。第二轮只对最小可疑区间增加 descriptor、packet ID 或 function trace。全量 per-packet log 容易改变时序，并产生误导性的“加日志后不复现”。

## 5. 验证根因而非相关性

一个可信结论至少包含：机制解释、支持证据、反证检查和定向实验。例如怀疑 RX URB 不足，应展示 inflight 降为零与断流时间一致，并通过提高预提交深度或人为缩小深度验证故障率变化。

## 6. 恢复与回归

修复后覆盖正常建链、压力、弱信号、并发角色、低功耗、反复 up/down、Firmware reset 和长稳。记录恢复耗时、数据丢失、IP/Socket 影响与用户可见状态。若只验证原始单点用例，很可能把问题移动到了生命周期的另一条分支。

## 最小现场包

- 版本与能力快照；
- case ID 与复现步骤；
- 用户态、内核、Firmware 的时间线；
- 空口抓包或无法抓包的明确说明；
- 分层计数差分；
- reset 前的 pending command、queue watermark 与错误寄存器/dump。

## 从症状到可证伪假设

把“RX慢”写成可重复条件：同一版本、固定衰减、UDP下行、单角色、开始流量30秒后，每隔约1秒出现20 ms无Host RX。然后区分三类证据：

| 层次 | 可以得出的结论 | 不能直接得出的结论 |
|---|---|---|
| 相关 | inflight=0与断流重叠 | refill一定是根因 |
| 机制 | callback阻塞使下一批RX未提交 | 为什么callback会阻塞 |
| 因果 | 定向触发/消除阻塞改变故障 | 所有平台都同一机制 |

若改变URB数量改善现象，还可能只是延后内存压力或改变调度。应追到callback阻塞的锁、耗时工作或资源竞争，给出能够反驳该假设的实验。

## Trace采集本身会改变系统

定长二进制记录包含event ID、clock、CPU/context、cookie/generation、reason与参数。必须统计trace ring丢失、覆盖和冻结时刻；没有该计数，“没看到事件”无法区分未发生与日志丢失。

以教学参数1 MiB、32 byte/record、10,000 record/s计，历史仅约3.28秒。需要为关键状态保留更长低频历史，为单包保留短期细节，并把触发前后窗口一起采集。

## 数值对账例子

同一Driver queue、同一测试时段，新增接受10,000个Packet，新增成功9,700、drop100，队列从50增长到250：

```text
10000 = 9700 + 100 + (250-50)
```

这组数据守恒，不存在200个“失踪包”。若期间Reset将pending清零，需把cancel/unknown outcome加入账本。airtime重试、A-MSDU和GRO后的对象数量不可直接放进同一等式。

## 修复证据的最小结构

记录故障触发条件、第一处异常、被破坏的不变量、修复如何改变该机制、原场景复验与边界回归。示意修复没有目标芯片实测时，明确称“候选方案/教学推演”，不要包装成项目战绩。

## 复习追问与答案

**没有空口帧证明没发吗？** 不能，先验证抓包信道、带宽、格式能力与capture loss，再结合PHY-start/end。

**日志正常为什么还故障？** 采样可能遗漏race，日志也可能只覆盖command而未覆盖数据；需要针对观测盲区补点。

**定位报告最有价值的附件是什么？** 能重建事件顺序、对象身份与计数口径的原始证据及可执行复现条件。
