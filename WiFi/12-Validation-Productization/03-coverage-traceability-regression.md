# Coverage、需求追溯与回归闭环

“跑过很多 Case”不等于验证充分。芯片验证需要把需求、场景、检查器、覆盖率、缺陷和量产反馈连成可追溯闭环。

## 从需求到 Checker

每条需求拆成：前置条件、Stimulus、可观察行为、时限、异常行为和覆盖点。例如“收到合法 Trigger 后响应 HE TB”至少包含 AID/RU 匹配、上下文有效、SIFS deadline、TXVECTOR、空口波形和失败 reason。

```text
Requirement
→ feature/scenario matrix
→ stimulus + reference result
→ assertion/checker/scoreboard
→ functional/code coverage
→ regression result
→ silicon/field correlation
```

需求若没有可自动判断的 checker，回归只能证明“没有崩溃”，不能证明行为正确。

## 覆盖率的四个层次

| 类型 | 回答的问题 |
|---|---|
| Code coverage | RTL/代码哪些结构被执行？ |
| Functional coverage | 协议参数与场景组合是否命中？ |
| Assertion coverage | 时序与不变量是否被激活并通过？ |
| Cross coverage | 边界条件组合是否真正相遇？ |

100% code coverage 不代表协议空间充分。Wi-Fi 的有效交叉维度包括 role、bandwidth、MCS/NSS、GI/LTF、RU、cipher、BA window、power state、bus type、error injection 和 concurrency。

Cross 不能无脑笛卡尔积；应根据架构风险选择，例如 `reset × DMA inflight × non-coherent`、`rekey × reorder buffered × A-MSDU`、`MCC channel switch × TBTT × BT grant`。

## Golden Model 与 Scoreboard

PHY bit-true model 对 TX vector 生成 reference waveform/bitstream，对 RX 输入生成预期 field/PSDU；MAC model 生成 Sequence、BA bitmap、retry 和状态变化。Scoreboard 应允许实现延迟不同，但不允许语义不同。

每个 Golden Vector 保存：输入、期望输出、模型版本、定点配置、随机种子、容差和需求 ID。只保存“一个通过的波形文件”无法在算法升级后追溯。

## Fault Injection

正常流量覆盖不了生命周期 bug。至少注入：

- Command 丢失、重复、乱序、迟到；
- descriptor 长度/版本/owner 异常；
- DMA completion 延迟、bus error、credit 丢失；
- Interrupt coalesce、lost wakeup 窗口、NAPI budget exhaustion；
- Key install/rekey 与 TX/RX 并发；
- BA window 回绕、BAR、timeout、DELBA 竞态；
- suspend/reset/remove 位于每个关键提交点；
- RF impairment：CFO、SFO、AWGN、multipath、phase noise、power imbalance。

注入要有预期结果：拒绝输入、局部恢复、连接重建或芯片 Reset。只确认“最终恢复”仍不足，还要确认无泄漏、无旧状态污染、证据被保存。

## 回归分层

1. 每提交快速 smoke：编译、基础 register/ABI、单包 TX/RX；
2. 每日 feature regression：协议场景与边界；
3. 每周 stress：长稳、并发、功耗切换、故障注入；
4. 版本门禁：interop、法规、性能、功耗和已知问题矩阵；
5. Silicon/客户缺陷回灌：最小复现成为永久 Case。

失败分类要区分 DUT、testbench、环境、模型、仪表和 flaky infrastructure，不能用重复运行把不稳定直接洗成通过。

## First Silicon 证据梯子

Bring-up 每一步只增加一个未知量：

```text
power/clock/reset
→ register/SRAM/JTAG
→ FW boot/heartbeat
→ interrupt/timer
→ DMA/bus loopback
→ PHY digital loopback
→ RF CW / conducted packet
→ MAC ACK/BA
→ association/security
→ throughput/power/concurrency
```

每一级定义进入条件、通过标准、失败采集和回退动作。跨级调试会把模拟、数字、固件和协议问题混在一起。

## 量产与现场反馈

ATE/Factory Test 数据不只用于 pass/fail，还应按 wafer/lot/board/calibration version 建立分布。良率漂移、EVM margin、frequency error 或 RX sensitivity 的慢性变化应回流设计和制程。

现场问题匿名化后映射到需求和回归：触发条件、版本、修复、测试 Case、覆盖点和发布版本。没有永久回归的缺陷不算真正闭环。

## 发布门禁

- 所有高风险需求有 checker、coverage 与 owner；
- 新 ABI 有向前/向后兼容测试；
- Reset/suspend/rekey/roam 完成 fault-injection 矩阵；
- 性能报告同时包含吞吐、尾延迟、CPU、功耗和环境；
- RF/法规结果记录 reference plane、仪表、线损、温压与校准版本；
- blocker defect 有明确 disposition，不以“低概率”代替风险评估。

## 面试追问

- code coverage 100% 为什么仍可能漏掉严重 Bug？
- 怎样为 Trigger Response 写可验证需求？
- 哪些交叉覆盖最容易暴露 Wi-Fi 生命周期问题？
- 客户偶现问题如何变成稳定的永久回归？

## 答题要点与适用边界

Code coverage覆盖执行结构，不保证协议参数和并发组合。Trigger需求应包含前置条件、合法参数、允许不响应条件、deadline与可观察输出。Reset/DMA、rekey/reorder、MCC/TBTT等交叉由共享资源和生命周期风险决定。现场缺陷先提取可重复事件序列，再回灌最早可复现层，并保留系统回归和原始证据。
