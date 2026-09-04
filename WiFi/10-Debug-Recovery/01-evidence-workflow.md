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
