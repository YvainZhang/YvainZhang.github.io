# 命令、事件、数据与故障恢复

## 命令与事件

同步等待实现简单，但容易在总线异常、Firmware 卡死或 suspend 时把调用线程永久阻塞。可靠设计至少包含：

- 单调 request/transaction ID；
- 每类命令的明确 deadline；
- 返回码与 Firmware reason 分离；
- pending table 的并发保护；
- reset/remove 时批量取消等待者；
- event 携带 session/generation，拒绝过期结果。

事件处理不应在总线接收上下文执行耗时恢复。先验证长度、类型和版本，再入队到可控工作上下文；事件格式错误应计数和采样，避免无限日志反过来拖垮系统。

## 数据与流控

TX credit、descriptor、bus request 和 MAC queue 是不同资源。只观察一种资源可能误判瓶颈。应为每级维护 enqueue、dequeue、drop、high-watermark 和等待时间，并保证 stop/wake 成对。

RX 路径要防御非法长度、聚合边界、descriptor 越界和重复包。所有权模型应写成状态转换，而不是依赖“调用者应该知道”：

```text
FREE → HOST_QUEUED → BUS_INFLIGHT → DEVICE_OWNED
     ← COMPLETION / ERROR / RESET ←
```

## Watchdog 与恢复等级

恢复不应一上来就重启整颗芯片。可以按影响面分级：

1. 重试单个命令或重新提交 bus request；
2. 清理单个队列/BA Session；
3. 重连当前 VIF；
4. 重置 Wi-Fi Function/Firmware；
5. 芯片级 Reset 并恢复所有角色。

每次升级必须保留触发原因、最后心跳、pending command、队列水位、总线错误和 Firmware dump。否则自动恢复虽然掩盖了用户故障，却也抹掉了根因。

## 生命周期竞态

Probe、open、connect、suspend、resume、disconnect、stop、remove 和 reset 可能交错。工程上应有单一生命周期状态机，异步工作持有可验证的引用或 generation；在释放资源前先阻止新入口，再取消工作、等待 inflight 完成，最后销毁对象。

## 一次命令超时不代表 Device 没执行

以设置信道命令为例：Host 成功提交、Firmware 已切换、响应在总线丢失，Host 最终 timeout。再次无条件发命令可能重复切换；若该操作是 add peer，重复可能消耗新 slot。

为命令分类：幂等 set-state 可以查询/重试；create 类使用去重 token 或查询创建结果；不可逆动作必须有明确事务设计。transaction ID 解决一次请求匹配，Device/session generation 隔离重启或重连，二者用途不同。

```text
allocate request
→ publish pending entry
→ submit
→ response: atomically claim terminal state
or timeout/cancel: atomically claim terminal state
→ detach waiter, retain tombstone if late response possible
→ reclaim transport memory when last reader is gone
```

terminal claim 只能成功一次。Timeout 后迟到响应即使 generation 没变，也必须因 transaction 已终止被识别，不能依赖所有 timeout 都触发 Reset。

## 数据与控制公平

共用 HIF 时，bulk data 可能用尽全部 Credit/Buffer，导致 disconnect、Key 或 power command 无资源；没有控制命令，又无法解除数据阻塞。可为控制保留资源、使用独立队列或有限抢占策略，并验证保留资源不会被数据路径借走后无法回收。

调度观测至少区分 command wait、bus wait、FW dispatch wait、handler execution 和 response return。总 timeout 只给出症状，分段时延才能识别 head-of-line blocking。

## 恢复级别不是固定逐级重试

“先重试命令”仅适用于已证明可重试的故障。DMA 越界、内存损坏或身份不明的 completion 可能要求立即隔离相关硬件；无意义地重试会扩大破坏范围。

恢复表应为每类故障给出：可继续使用的资源、需要停止的生产者、dump 范围、终止时限和成功条件。例如仅 BA session 卡住可以局部处理；HIF 不可访问时无法依赖 Firmware flush 命令完成 quiesce。

## 恢复验收与教学守恒

假设 Reset 前有 100 个已接受 TX：70 个 terminal completion、20 个 Host queue cancel、10 个 bus inflight abort。恢复结束应能解释全部 100 个，而不是把计数器清零就认为无泄漏。

如果某些空口结果未知，单独记录 unknown outcome；资源回收成功和业务投递成功分别统计。验证既要查内存/引用，也要确认新会话可发可收、Control queue 不再阻塞。

## 复习追问与答案

**Timeout 后还要保留什么？** transaction 终止身份、晚到判定所需信息及尚被总线/Device 引用的内存，保留范围由 ABI 定义。

**为何不能在 RX callback 中完成整个 Reset？** 它可能持有总线/队列锁，Reset 又等待相同 callback 退出；需要切换到允许睡眠并定义锁顺序的恢复上下文。

**恢复后 heartbeat 正常就算好了吗？** 不够，还需验证 Control、TX/RX、Credit、Context 和功耗状态。

继续：[Context 与代际](04-context-generation-and-reset.md)、[调试证据](../10-Debug-Recovery/01-evidence-workflow.md)。
