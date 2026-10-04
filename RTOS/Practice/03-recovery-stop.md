# 恢复以后拒绝旧回复，停止以后交付剩余结果

device task 恢复以后，新请求可能再次从 id=1 开始。旧队列里的一条回复若只凭 id 匹配，就可能误完成新请求。队列和任务都仍有效，并不意味着它们属于当前会话。

先读 [队列与 owner](02-queue-owner.md)，代码与测试分别位于 [源码包](https://xidianedu.cc/tech/platform/reference/source/)的 `platform/runtime/freertos/runtime.c` 和 `platform/tests/freertos_test.c`。

## 用完整身份隔离恢复前后的工作

core 在恢复时关闭 admission、终结旧 generation 请求，再推进代际并等待 backend READY。旧排队回复仍可能被取出，因此接收时检查完整请求身份。重建失败进入 FAILED，保留诊断并等待显式决策。

这里的代际检查解决会话身份，任务退出与队列存储释放仍各自需要同步。共同恢复契约见 [跨运行时案例](https://xidianedu.cc/tech/platform/cases/03-cross-runtime-recovery/)。

## CLOSED 以后仍要处理入口

owner 正常循环按预算处理输入；停止时先禁止新入口，再处理剩余有界集合。已经成功入队的 ticket 必须收到 ACCEPT 或 REJECT，已接受请求必须有终态。

```text
queued ticket = accepted + rejected + pending_admission
accepted = completed + timed_out + cancelled + failed + live
```

停止成功时，`pending_admission` 和 `live` 都应为零。runtime 在 CLOSED 后继续取入口项，交由 core 拒绝，避免普通预算留下最后一项。

## 谁来等待任务退出

owner 收尾后等待 `device_done`，确认 backend 不再访问队列和实例，再给出 `owner_done`。外部等待者通过停止接口取得完成结果，destroy 才释放队列、同步对象和实例。

callback 在 owner 上运行，调用同步停止或等待自己退出会被拒绝为 `SDK_ECONTEXT`。`stop_wait` 返回 `SDK_ETIME` 时，对象仍可能被任务使用，不能立即释放；外部还要禁止新 API 调用，等待当前调用者退出。

## 用 gate 留下一项工作

回归让 owner 在首个 ACCEPT callback 上等待，再向入口提交 64 个请求并发出停止。短等待先超时，gate 释放后再等待成功，最终断言：

```text
queued=65  accepted=1  rejected=64  live=0
```

按 [实验环境](01-environment.md)运行 `make -C platform freertos-test`，检查 `V09-ingress-full-stop-timeout-cleanup`。上述数值是受控测试断言，不是跨平台停止时间承诺。无限阻塞的 callback、调度延迟和目标设备退出耗时都会影响完成时间。

公开快照的实际回归见 [验证记录](https://xidianedu.cc/tech/platform/reference/verification/)，RAM、栈与排空预算的推导见 [资源预算](https://xidianedu.cc/tech/platform/design/06-resource-budget/)。
