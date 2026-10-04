# 持 fd 解绑设备：四种寿命怎样收尾

用户进程已经打开 `/dev/archlab0`，设备却被 unbind。进程接着 `read`，驱动能否返回已有数据？什么时候返回 EOF？最后谁释放实例？这个问题不能只靠模块引用，也不能只靠 `devm` 回收。

本节用两个软件 platform device 和 misc 接口演示退出顺序。代码在[源码包](https://xidianedu.cc/tech/platform/reference/source/)的 `kernel-labs/archlab/archlab.c`，用户测试为 `uapi_test.c`。先理解[fd 引用](03-fd-lifetime.md)、[同步与对象寿命](07-concurrency-ownership.md)，内核环境见[专用 VM 说明](../guide/environment.md)。

## 模块、实例、session、work 分别存活多久

| 对象 / 责任 | 本实现的保持方式 | 不自动保证什么 |
|---|---|---|
| 模块代码 | `file_operations.owner = THIS_MODULE` | 不阻止某个设备被解绑 |
| 实例内存 | 初始引用 + 每个 open 的 kref | 不表示还能接受新工作 |
| open session | `file->private_data` 指向实例，close 放引用 | 不提供每读者独立队列 |
| delayed work | dead 门闩 + 同步取消 | 不由一个内存引用自动停下 |

`kref` 管理对象寿命：在交给可能继续使用的持有者前取得引用，最后一次 put 才调用释放函数。它不能替代共享字段的锁或工作停止协议。[Linux kref 文档](https://docs.kernel.org/core-api/kref.html)

本例未用 `devm` 分配这份跨解绑存活的实例，而由 `release_instance()` 的 `kfree` 收尾。设备资源管理适合绑定相关资源；对仍被 open 或异步活动使用的对象，仍需明确实际最后使用者。

## 先跟踪引用，再跟踪工作

用一次 open 和两条排队记录举例，以下数字是寿命推演，并非固定的运行日志：

| 步骤 | kref | dead | 队列 | 发生什么 |
|---|---:|---|---:|---|
| probe 完成 | 1 | false | 0 | 初始引用，注册入口并安排生成 |
| open | 2 | false | 0 | open_session 取得 session 引用 |
| work 生成两条 | 2 | false | 2 | 同一 mutex 下写队列并安排下一次 |
| remove 置 dead | 2 | true | 2 | 从此禁止生成和重排 |
| deregister + cancel_sync | 2 | true | 2 | 新入口撤下，现有 work 完成 |
| remove 放初始引用 | 1 | true | 2 | open 仍保持实例 |
| 旧 fd 读取两条 | 1 | true | 0 | 消费既有记录 |
| 旧 fd 再 read | 1 | true | 0 | 返回 0，即 EOF |
| close / release | 0 | true | 0 | 最后引用消失，实例释放 |

`remove_device()` 在 mutex 内设置 dead。`generate()` 在同一把锁内检查 dead，并决定是否重排。这样停止门闩与生成许可属于同一同步关系。

随后 remove 在锁外调用 `cancel_delayed_work_sync()`：等待 work 完成时，不能持有它需要取得的锁，否则双方会互等。同步取消前先禁止重排也很关键，否则周期 work 的许可仍存在。[workqueue 同步取消说明](https://docs.kernel.org/core-api/workqueue.html)

## read：先证明能交付，再消费

`read_record()` 的顺序为：

```text
用户容量不足一条记录 → EMSGSIZE
取得 mutex
  有记录 → copy_to_user → 成功后推进 head/count
  无记录且 dead → EOF
  无记录且非阻塞 → EAGAIN
  其他情况 → 等待 count || dead，醒来重新判断
```

`copy_to_user` 失败返回 `EFAULT`，代码不推进队列，因此记录仍在。这个保证来自源码分支；测试覆盖范围应与实际断言对应，不能仅凭实现存在就声明所有坏地址路径都已执行。

这里使用可睡眠 mutex，并处于可睡眠的进程上下文，避免在普通 spinlock 保护区内调用可能缺页睡眠的用户复制。真实 IRQ、DMA 与具体内核配置的规则需要另外审查，软件设备实验没有覆盖它们。

## poll 的 HUP 可以与数据同时出现

`poll_records()` 有数据时报告 IN，dead 时报告 HUP；两者可以同时置位。调用者按 UAPI 排空后再看到 EOF，不能见 HUP 就假设最后几条记录不存在。

多个 open 共享消费一个实例的队列，某个读者拿走一条后，其他读者不会再得到同一条。若要每读者完整订阅，应设计各 session 队列或广播存储，并重新核算容量和慢读者策略。

UAPI 使用固定宽度 record/stats 字段，返回版本与长度，拒绝未知 ioctl，不传内核指针。统计满足 `generated = delivered + dropped + queued`。接口类型、队列边界与错误结果应在用户代码可独立检查，而不是依赖驱动内部结构布局。

## 在专用 QEMU 中运行

下面两步都在宿主的源码根目录执行：

```sh
./scripts/run-container.sh kernel-build
python3 kernel-labs/run-vm.py
```

第一步在工具容器中只构建模块、匹配内核和 initramfs；第二步在独立 ARM64 QEMU 中加载模块。共享容器的内核不是实验 VM，模块加载留在这个 VM 内。

正常串口中应有 `uapi-unbind-multi-instance` 的 PASS，最后有 `KERNEL_VM_PASS`。用户测试同时打开两个实例，解绑 0 并排空至 EOF，检查 HUP，随后核对实例 1 仍能读数据；VM 启动脚本还运行两处 probe 故障注入和有限次数装卸。

`build/vm/` 保存内核版本、config、镜像与串口。当前配置未启用 KASAN / lockdep 时，这两项保持 SKIP：串口没有报警不证明不存在所有 UAF 或锁问题，软件实例也没有替代真实 MMIO、DMA 与中断验证。

从持 fd 解绑这个问题，可以继续推到平台退出接口：停止新工作、同步既有活动、排空或拒绝已有数据，最后归还引用。[停止与排空案例](../cases/01-stop-drain.md)在用户态执行环境里处理同一组责任，但 Linux driver 仍通过独立 UAPI 接入，不并入用户态 OS 抽象层。

## 进一步证明退出

[驱动静止与退出证明](../advanced/04-driver-quiescence.md)按并发交错分析 dead、重排、等待和引用，并讨论用户复制与真实硬件活动加入后的责任。
