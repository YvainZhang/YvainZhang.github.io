# buffer 提前归池：锁之外的所有权契约

生产者把 buffer 填成 `AAAA`，提交给异步发送，再把它归还到池。另一个生产者取到同一块内存，填成 `BBBB`。发送方最后从这个地址读到什么？只在入队时加锁，无法回答异步读发生时内容属于谁。

本节从这个时序展开复制、借用与转移，再看有界队列和停止。代码路径均指[公开源码包](https://xidianedu.cc/tech/platform/reference/source/)；命令在[工具容器](../guide/environment.md)内执行。

## 一次入队锁只覆盖一个区间

```text
t0  A 从池取 buffer，写入 AAAA
t1  A 持锁，把指针放入发送队列，然后解锁
t2  A 将 buffer 归池
t3  B 取到同地址，写入 BBBB
t4  发送线程取队列指针，读取该地址
```

如果 t1 只存指针，t4 读取的就可能是 B 写入的内容。锁保证队列节点的修改符合规则，却没有保证被指向的字节在 t1→t4 之间保持有效和不变。

| 输入契约 | 返回后调用者能做什么 | 实现的成本与责任 |
|---|---|---|
| 提交时复制 | 复用原 buffer | 复制时间、SDK 池容量 |
| 借用到约定完成点 | 保留且按契约禁止修改 | 明确最后使用点、失败/取消时归还 |
| 成功后转移所有权 | 放弃访问，失败时仍归调用者 | 释放者、分配器边界与所有返回分支 |

引用计数可以保持对象仍分配着，但本身不禁止其他持有者写 `BBBB`。对于可变 buffer，还需要访问权限、不可变性或锁规则。

## 本 SDK 怎样选择复制边界

`platform/runtime/linux/runtime.c:sdk_submit()` 把输入复制到 `core_event.payload`，锁内放入 ingress；返回 `SDK_QUEUED` 后，调用者可复用原输入。

```text
调用者原 buffer
    └─submit 内复制→ ingress 副本
                           └─owner 处理→ core 请求槽 / 输出报文
```

`SDK_QUEUED` 只表示进入本地传输入口，owner 之后发出 `SDK_ACCEPT` 或 `SDK_REJECT`。`SDK_EFULL` / `SDK_ESTATE` 是直接失败，本次调用没有增加一条已入队请求；此时不能等待一个不存在的异步完成。

接受后的请求承担一次终态通知：完成、超时、取消或失败。取消本地等待不表示远端操作一定撤销，协议能力需要单独描述。这条边界见[SDK 契约](https://xidianedu.cc/tech/platform/design/02-sdk-contract/)。

回调的 payload 则是借用：只在回调期间按约定使用，若要交给另一个异步消费者，应在返回前复制。调用者输入的复制契约和回调输出的借用契约不同，不能仅凭参数都叫指针就采用同一寿命。

## 条件变量为何必须配谓词

`labs/mechanisms.c` 的三项环形队列用 `head`、`count` 和 `stopped` 描述业务状态。生产者满时等待，消费者空时等待：

```c
pthread_mutex_lock(&q->mutex);
while (!q->count && !q->stopped)
    pthread_cond_wait(&q->ready, &q->mutex);
/* 此处重新取得 mutex，重新判断业务条件后消费或退出。 */
```

条件变量通知不储存队列内容，等待还可能被唤醒后发现条件已改变，因此使用同一 mutex 下的谓词和 `while` 重检。[pthread 条件变量说明](https://man7.org/linux/man-pages/man3/pthread_cond_wait.3.html)

环形位置使用 `(head + count) % capacity`，本实验故意选容量 3，防止只在二次幂容量下成立的位掩码写法。生产和消费 1000 个递增值，最终检查次序和 `push == pop`。

`atomic_lab()` 则展示单次发布：先写 `value = 42`，再 release 存储 ready；消费者 acquire 观察 ready 后读取 value。这里只解释一次初始化发布，不等于任意复杂队列都已无锁。`volatile` 不提供这种线程同步关系。

## 停止是一项剩余义务的清算

停止不能只设置一个 flag 然后释放内存。需要分别处理三类对象：

| 停止时状态 | 仍欠什么 | 何时能释放 |
|---|---|---|
| 尚未入队的调用 | 明确同步失败 | 调用者按输入契约处理 |
| queued，尚未 accepted | admission 的结果通知 | owner 完成拒绝/接受处理后 |
| 已 accepted 的 live 请求 | 一次终态通知 | 最后使用者停止访问后 |

本 SDK 的顺序是关闭接收入口，通知 owner 停止，取消 live 并拒绝剩余 queued，处理 backend 和 owner 退出，最后由外部调用者串行 destroy。正常循环的处理预算用于公平性；停止阶段若只处理一个预算批次就退出，会遗漏队列后面的通知。

owner 回调可以投递 `sdk_post_stop()`，等待 / join 由外部上下文完成。`sdk_stop_wait()` 返回超时意味着尚未等到停止完成，对象仍可能被线程访问；不能据此直接 free。[停止与排空案例](../cases/01-stop-drain.md)给出实际触发与守恒检查。

## 运行和观察

容器内源码根目录：

```sh
make -C labs all
./build/labs/mechanisms queue
./build/labs/mechanisms atomic
make -C platform linux-test
```

对应预期名称包括 `L4-bounded-queue-wrap-predicate-stop-conservation`、`L4-acquire-release-publication`、SDK 的 `copy-lifetime`、`submit-stop-ingress-budget` 和 `V09-ingress-full-stop-timeout-cleanup`。

`copy-lifetime` 在提交后立即把原输入改成 B，回调核对仍收到 A；这个测试具体覆盖提交复制，不应解释成所有传入指针都可立即释放。停止测试同时核对 queued、accepted、rejected 和 terminal 的关系，并在清理后检查资源基线。全部机制与构建回归另执行 `make -C labs test`。

这些机制在 Linux 与 RTOS 中都需要，但 mutex、queue、notification 分别承担共享状态、数据传输和唤醒，不能由一个泛化 lock API 代替。[运行时对照](https://xidianedu.cc/tech/platform/design/03-linux-freertos/)保留这些差异，[资源预算](https://xidianedu.cc/tech/platform/design/06-resource-budget/)核算复制与在途对象的成本。
