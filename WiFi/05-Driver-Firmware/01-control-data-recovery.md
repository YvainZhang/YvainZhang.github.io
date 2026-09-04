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
