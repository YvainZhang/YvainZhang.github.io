# 用一个 owner 串起异步请求

提交请求以后，API 返回成功，设备却还没回复。此时哪些数据已经复制，谁负责更新状态，停止又该等到哪里？Linux runtime 把这些责任交给一个 owner 线程。

前置阅读：[并发与所有权](../mechanisms/07-concurrency-ownership.md)、[事件与时间](../mechanisms/06-events-time.md)。代码位于 [公开源码](https://xidianedu.cc/tech/platform/reference/source/) 的 `platform/runtime/linux/runtime.c`。

## 数据与唤醒分开

```text
API → mutex 保护的有界入口 → eventfd 唤醒
                                 ↓
                       pthread owner / epoll
                                 ↓
                       core 事件 → backend 动作
                                 ↓
                       seqpacket → 设备模拟进程
```

API 在入口复制 payload，入队结果只表示 ticket 进入等待处理的集合。owner 将输入送进 core，core 再决定 ACCEPT 或 REJECT。eventfd 提示 owner 检查真实入口，不承担请求存储；唤醒次数也不等于工作数量。

core 由 owner 单独修改。runtime 负责锁、线程、描述符、时间与进程收尾。业务状态转换的共同规则见 [SDK 契约](https://xidianedu.cc/tech/platform/design/02-sdk-contract/)。

## 时间与停止分别处理

单调时钟与 timerfd 为 deadline 检查提供时间和唤醒。回包已就绪时仍要检查身份与 deadline，不能只按 epoll 返回的顺序决定成功。每轮入口、回复和数据处理都有预算，避免一类持续到达的工作占住整个循环。

停止先关闭入口，随后处理剩余 ticket、终结 live 请求、关闭后端并等待线程退出。普通公平预算不能截断最终收尾，具体反例见 [停止时的排队请求](../cases/01-stop-drain.md)。callback 在 owner 上执行，不能同步等待 owner 自己退出；阻塞 callback 也会拖住其它结果交付。

## 启动时先发布可见状态

`pthread_create` 成功不表示新线程会晚于调用者的下一行运行。当前实现用 mutex 协调 owner / started 的发布与首次运行，避免 READY callback 看到尚未发布的启动状态。

定向 startup 测试控制 owner 到达入口，并在测试构建中注入线程创建错误，检查回滚与重试。普通构建没有这些钩子；这些受控交错的结果见 [验证记录](https://xidianedu.cc/tech/platform/reference/verification/)。

## 运行与观察

按 [环境准备](../guide/environment.md)进入 Linux 工具容器，在源码根目录执行：

```sh
make -C platform linux-test
make startup-test
```

核对复制、身份、deadline、恢复、停止与启动失败的断言，结合 fd 基线观察资源收尾。容器中的功能结果不推导硬实时最坏延迟。跨系统复用时保留业务结果义务，各端单独实现运行机制，见 [运行时边界](https://xidianedu.cc/tech/platform/design/03-linux-freertos/)。
