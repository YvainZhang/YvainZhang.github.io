# 异步 SDK API 与调用契约

源码包中的 `platform/include/sdk.h` 是公开头文件；最小消费者在 `platform/examples/public-consumer.c`，交互示例在 `platform/examples/demo.c`。构建与运行见 [环境页](../guide/environment.md)，源码版本见 [下载页](source.md)。

## 一次会话的寿命

| 调用 | 行为与应用责任 |
|---|---|
| `sdk_create` | 校验配置并分配固定容量对象 |
| `sdk_start` | 启动 backend 和 owner，等到 READY；停止后不再次 start |
| `sdk_submit` | 复制 payload；成功返回 QUEUED ticket，随后通知 ACCEPT 或 REJECT |
| `sdk_cancel` | 提交取消事件；最终结果看 TERMINAL 通知，远端副作用仍可能发生 |
| `sdk_recover` | 关闭接收、终结旧请求、递增 generation 并重建通道；失败进入 FAILED |
| `sdk_post_stop` | 关闭输入并提交停止意图，适合从回调调用 |
| `sdk_stop_wait` | 有限等待停止；超时对象仍有效，继续等待收尾 |
| `sdk_stop` | 等待 owner 与 backend 退出 |
| `sdk_destroy` | 应用先关闭所有新调用，并等待全部 API 使用者结束，再销毁 |

create / start / destroy 由应用串行化。submit / cancel / recover / post_stop / snapshot 支持多个生产者，core 的业务状态只由一个 owner 线程或任务写入。

## ticket、接受与完成

ticket 是 `{instance, generation, id}` 三元组。提交成功表示进入输入队列；owner 才能接受业务请求。同步拒绝没有回调，QUEUED 请求会得到 ACCEPT 或 REJECT，只有 ACCEPT 的请求承担一次 TERMINAL 通知义务。

恢复后 generation 递增，id 可从 1 重新分配，因此只比较 id 会把旧响应误认成新工作。取消也可能晚于响应，只能以最终通知判断结果。详细账目与时序见 [SDK 契约](../design/02-sdk-contract.md)。

## 回调上下文与停止

回调不持内部锁，允许提交事件或 `sdk_post_stop`。从 owner 回调同步调用 stop / stop_wait / destroy 返回 `SDK_ECONTEXT`，由外部调用者执行等待与销毁。回调里的 payload 只在本次回调期间有效。

回调必须有限耗时。`sdk_stop_wait(timeout_ms)` 超时返回 `SDK_ETIME`，对象仍在停止中；另一 stopper 占用等待入口时返回 `SDK_EFULL`。等待成功才确认运行时已收尾，CLOSED 状态通知不能替代 join 或外部 API 调用者退出。

## 容量与资源预算

默认固定容量为 16 个请求、256 bytes 控制 payload、1024 bytes 数据 payload、32 个数据项、32768 data bytes、64 个输入事件和 64 项历史。config 可以缩小逻辑额度，结构分配大小保持固定。

`sdk_resource_budget` 的 runtime_bytes 已包含 core，core_bytes 是分解项。Linux owner 栈另配置 256 KiB，还需要计入子进程、libc / pthread、内核 socket、页表和日志。FreeRTOS 栈以 `StackType_t` 元素计数，POSIX port 还占用宿主线程资源。完整预算见 [资源专题](../design/06-resource-budget.md)。

## 数据、快照与能力

数据使用 drop-new：core 分别记录到达、排队、丢弃、交付。Linux backend 的 generated / dropped 来自最后一份上报计数，断连前未上报的量未知；序号缺口不能确定准确丢弃位置。

snapshot 返回 owner 最近发布的状态和统计。`post_stop` 已关闭入口时，快照仍可能暂时显示 READY。`stats.queued` 也在输入事件进入 core 后才增加；不能单靠某个快照判断所有生产者已经退出。

remote_cancel 与 pause_data 当前能力为 0。关闭 `SDK_ENABLE_DATA` 时 data_max 为 0，STREAM 请求明确拒绝；这不证明全部固定数据结构已从内存移除。API 与 wire 版本为 1，跨版本二进制布局兼容另行评审。

## 模拟器边界

DROP、DUP、DISCONNECT、STREAM、BAD_VERSION、DELAY、RECOVER_FAIL 用于注入教学故障。普通请求回显 payload，wire 显式序列化并拒绝错误版本、截断和超长。当前模拟器没有实现 USB / SDIO DMA、射频或真实固件执行。

相关内容：[停止收尾](../cases/01-stop-drain.md)、[跨运行时恢复](../cases/03-cross-runtime-recovery.md)、[验证范围](verification.md)。
