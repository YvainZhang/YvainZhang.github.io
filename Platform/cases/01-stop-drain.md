# 停止以后，已经入队的请求由谁收尾

owner 每轮最多处理 64 个输入，避免入口生产者持续占用线程。这项公平预算在正常运行时有用，但停止以后仍按相同预算退出，就可能留下已经返回 QUEUED 的 ticket。

本例对应教学 SDK 的 Linux 与 FreeRTOS owner。代码、测试和版本见[源码入口](../reference/source.md)，两阶段 admission 见[SDK 契约](../design/02-sdk-contract.md)。

## 用受控 gate 构造剩余输入

测试先提交一个请求，让 owner 进入 ACCEPT callback，并在受控 gate 上等待。这时它已处理了一个输入，但还没有离开 callback。生产者继续提交 64 个请求，填满入口，然后调用停止。

```text
owner：取出 A → ACCEPT → callback gate 等待
生产者：把 B1…B64 入队 → 再提交一项得到 EFULL
等待者：stop_wait(5ms) → gate 未释放，得到 ETIME
释放 gate → owner 收尾 → stop_wait(2000ms) 成功
```

这一轮共有 65 个成功入队的 ticket：A 已经被接受，另外 64 个仍等待 admission。普通预算已经用掉 1 个名额，剩余 63 个不足以处理全部 64 个输入。若只看到业务 CLOSED 就退出，最后一个调用者不会收到 ACCEPT 或 REJECT。

## 两本账说明为什么 live=0 还不够

业务账检查已经被接受的请求：

```text
accepted = completed + timed_out + cancelled + failed + live
```

ticket 账还要检查入口：

```text
成功入队的 ticket = accepted + rejected + pending_admission
```

停止完成以后，两个余项都必须为零。线程退出、live=0 或释放了队列内存，分别只能说明部分条件，不能证明所有通知义务结束。

本例 core 的 `stats.queued` 在输入实际到达 core 时递增，运行中快照不能表示全部 API 已返回 QUEUED 的 ticket。停止成功后才用最终快照与回调记录核对完整计数。

## 比较三种收尾方式

| 方案 | 优点 | 问题 |
| --- | --- | --- |
| 保持普通 64 项预算，CLOSED 即退出 | 保留正常公平循环 | 本轮剩余集合可能超出剩余预算 |
| 丢弃入口项后释放资源 | 清理存储容易 | 调用者失去结果，契约未结束 |
| 关闭 admission 后处理完整剩余集合 | 每个 ticket 有明确结果 | 需要有界入口和有限耗时 callback |

本实现采用第三种。runtime 先关闭新入口，再处理剩余有界集合；core 在 CLOSED 状态拒绝后续 submit，避免重新 ACCEPT。Linux 异常退出路径也先关闭入口，再执行最终 drain。

关闭 admission 后，剩余集合至多为 64 个入口项，不会再被生产者无限延长。这个条件让 drain 从“可能一直追赶生产者”变成有限工作集。

## 运行定向回归

在[专用 Linux 工具容器](../guide/environment.md)的项目根目录运行：

```sh
make -C platform linux-test
```

`runtime_test.c` 中的 `V09-ingress-full-stop-timeout-cleanup` 检查以下结果：

```text
queued=65  accepted=1  rejected=64  live=0
入口已满时下一次 submit 返回 SDK_EFULL
gate 未释放时 stop_wait 返回 SDK_ETIME
gate 释放后 stop_wait 成功，fd 数回到基线
```

这些数值是测试断言的预期，不是承诺跨机器相同停止耗时。历史 2026-10-02/03 记录还覆盖四生产者与 stop 竞争的八轮回归。它们支持已测试路径；本次修订源码的验证范围从[版本页](../reference/source.md)查阅。

## 有界停止还有哪些前提

callback 可以无限阻塞时，即使队列有界，也无法承诺有界完成。OS 不调度 owner 时，同样不能从软件数量推导硬实时上限。

`stop_wait()` 把等待时间限制在调用者这一侧；超时以后对象仍然有效，不能立即 free。应用还需要禁止新 API 调用并等待现有调用者退出，最后才 destroy。

这个问题从一轮公平预算，连接到 admission、通知守恒、回调上下文和生命周期。相关设计见[资源预算](../design/06-resource-budget.md)与[生命周期评审](../design/08-lifecycle-review.md)。
