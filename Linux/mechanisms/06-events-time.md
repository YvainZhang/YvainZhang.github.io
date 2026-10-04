# 三个字节之后：就绪、通知与 deadline

管道里写入 `ABC`，epoll 报可读，程序只取走 `A`，随后再次等待。还有 `BC` 留在管道里，为什么 ET 模式下可能等不到下一次事件？从这个反例可以推到事件循环的公平性、通知合并和超时设计。

需要先理解[fd 的引用与复用](03-fd-lifetime.md)、[非阻塞 IO 的进度](04-io-persistence.md)。以下代码在[源码包](https://xidianedu.cc/tech/platform/reference/source/)的 `labs/mechanisms.c:epoll_lab()`，运行方式见[环境说明](../guide/environment.md)。

## 先走完一次 ET 时序

ET（edge-triggered，边沿触发）围绕状态变化报告事件。该实验注册非阻塞管道的读端，监听 `EPOLLIN | EPOLLET`：

| 顺序 | 操作 | 管道里剩余 | 实验结果 |
|---|---|---|---|
| 1 | 写入 ABC | ABC | 从空变为有数据 |
| 2 | `epoll_wait` | ABC | 返回一次可读 |
| 3 | 读取 1 字节 | BC | 得到 A |
| 4 | 零超时 `epoll_wait` | BC | 没有新的事件 |
| 5 | 再次 read | 空 | 得到 BC |
| 6 | 再次 read | 空 | 返回 EAGAIN |

第 4 步返回 0 不等于第 5 步没有数据。就绪信息说明尝试 IO 可以有进展，应用仍要实施 IO；上一次事件也不会自动替程序读完。Linux epoll 文档用类似的管道反例解释 ET，建议非阻塞处理直到 `EAGAIN` 后再等待新事件。[epoll 手册](https://man7.org/linux/man-pages/man7/epoll.7.html)

关键代码对照如下，完整实现还负责创建和关闭描述符：

```c
assert(write(p[1], "ABC", 3) == 3);
assert(epoll_wait(ep, &ev, 1, 100) == 1);
assert(read(p[0], &c, 1) == 1 && c == 'A');
assert(epoll_wait(ep, &ev, 1, 0) == 0);
assert(read(p[0], b, sizeof(b)) == 2 && !memcmp(b, "BC", 2));
assert(read(p[0], b, sizeof(b)) == -1 && errno == EAGAIN);
```

这个受控实验观察到的时序，不能扩大为任意情况下 ET 都只报告一次；其他状态变化或并发活动仍可能产生事件。可靠设计以自己的未完成工作和 IO 结果为依据。

## LT 的预算，与 ET 的 ready 集合

LT（level-triggered，电平触发）在就绪条件保持时可以再次报告。实验切为 `EPOLLIN`，写入 `DEF`，读走 `D` 后，下一次等待仍报告可读。

这使 LT 容易采用每轮处理预算：从热点源读取少量数据后让出机会，控制事件与定时事件仍能得到处理。`labs/extra.c:fairness()` 同时放入热点数据和 `STOP`，对热点最多处理四字节，并核对控制数据得到处理。

ET 也可以预算化，但预算耗尽且尚未到 `EAGAIN` 时，必须把源保存到自己的 ready 集合；下一轮先继续已有工作，不能只等内核的新边沿。ready 项还需要有效身份，旧 batch 的 fd 数字复用问题见[fd 生命周期](03-fd-lifetime.md)。

## eventfd 保存计数，队列保存业务

本实验创建普通 eventfd，连续写两次 1，再读一次得到 2，之后非阻塞读取返回 `EAGAIN`。未启用 `EFD_SEMAPHORE` 时，读取取出当前计数并清零；它不携带两条请求的内容。[eventfd 手册](https://man7.org/linux/man-pages/man2/eventfd.2.html)

SDK 的使用关系是：

```text
生产者：锁内复制请求到 ingress → 解锁 → 唤醒 owner
owner ：消耗唤醒 → 检查 ingress → 处理可用工作 → 发布状态
```

不能用“一次唤醒处理一条请求”替代检查队列。多次唤醒可能合并，唤醒发生时队列也可能已被其他逻辑处理。若 owner 每轮限制处理数量，预算后还需安排继续处理；队列中仍有工作时直接睡眠，会把公平策略变成遗漏工作。

## 可写监听与时间到期分别管理

socket 经常处于可写状态，持续注册 `EPOLLOUT` 会使循环不断返回。`platform/runtime/linux/runtime.c:watch_output()` 仅在输出队列非空时启用它，发送到 `EAGAIN` 时保留队列，排空后移除监听。

定时等待则要围绕绝对 deadline：假设请求在单调时间 100 ms 提交、期限 50 ms，deadline 是 150 ms。110 ms 被其他事件唤醒后，仅剩 40 ms；每次醒来都重等完整 50 ms，会无限推迟完成义务。

本实验用 `CLOCK_MONOTONIC` 创建 timerfd，读取其到期计数；SDK 的 core 还用逻辑时间向量核对到期前、到期时和到期后的转换。真实毫秒调度受 OS 影响，不能拿一次近似 50 ms 的测量证明严格边界。signalfd 示例先屏蔽 SIGUSR1，再以 fd 读取该信号。

## 运行与预期

在容器内源码根目录：

```sh
make -C labs all
./build/labs/mechanisms epoll
./build/labs/mechanisms extra
make -C platform linux-test
```

机制输出中查找以下 PASS 名称：

```text
L3-ET-partial-read-counterexample-drain
L3-LT-budget-HUP-EOF
L3-eventfd-notification-coalesces
L3-timerfd-monotonic
L3-signalfd-mask
L3-LT-hot-source-control-budget
L3-ready-batch-generation-fd-reuse
```

`epoll` 运行三字节、LT、eventfd、timerfd 与 signalfd；`extra` 包含热点公平性与旧 batch 身份，也会运行 stdio/权限补充实验。HUP 实验关闭写端后核对事件及 EOF，提醒事件循环把关闭状态与剩余数据分别处理。以上是受控输入的通过条件，并非吞吐或实时延迟保证。全部机制与构建回归为 `make -C labs test`。

从三字节反例最终得到的是 owner 的职责：保留未完成工作、按预算安排处理、让停止与时间检查得到机会，并在对应对象仍有效时执行 IO。[并发与所有权](07-concurrency-ownership.md)继续把这些调度规则与资源寿命连接；[停止案例](../cases/01-stop-drain.md)解释停止时为什么必须处理剩余通知义务。
