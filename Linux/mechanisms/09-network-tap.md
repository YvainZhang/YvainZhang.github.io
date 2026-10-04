# ping 通了，帧真的经过转发程序吗

两个本地 IP 可以互相 ping，并不能据此证明用户态链路程序转发了数据。同一个 network namespace 中，目的地址若属于本地，内核可能通过 local route 直接交付。要证明一条路径，需要能让该路径失效的对照。

本节围绕[源码包](https://xidianedu.cc/tech/platform/reference/source/)的 `src/link.c`、`scripts/smoke.sh`、`scripts/network-integration.sh` 和 raw-frame 测试展开。需要[环境说明](../guide/environment.md)中的独立网络实验容器。

## TAP 的两个方向先按内核视角解释

TAP 提供以太网帧接口：用户态从 TAP fd 读取，是取出内核向该接口发送的帧；用户态向 TAP fd 写入，是把帧注入该接口的接收路径。TUN 处理 IP 包，TAP 处理以太网帧。[Linux TUN/TAP 文档](https://docs.kernel.org/networking/tuntap.html)

```text
namespace A 的协议栈
       │ 发出的以太网帧
       ▼
     TAP A ──read──→ 用户队列 / 延迟 / 丢弃 ──write──→ TAP B
                                                        │ 收到的帧
                                                        ▼
                                               namespace B 的协议栈
```

反向有自己的一套队列与参数。TAP 写成功说明完成了该接口的注入，不能直接扩大为对端应用已经消费。

## 三组对照，核对谁承担交付

| 对照 | 配置 | 要观察的现象 |
|---|---|---|
| 同空间本地地址 | 同一 namespace 的两个 loopback 地址 | route get 显示 local，ping 可以绕过转发程序 |
| 跨空间正常转发 | 两个 namespace、各自 TAP、程序转发 | 帧抓包与 ping 结果同时出现 |
| block / resume | 保留接口，禁止后再恢复程序转发 | 禁止时通信失败，恢复时重新通信 |

第一组解释为何单独的 ping 成功证据不足。后两组把接口存在与程序参与分开。测试创建和清理自己命名的 namespace，不修改宿主网络配置。

冷邻居缓存下，IPv4 首先可能发送 ARP 以解析下一跳 MAC，随后出现 ICMP echo request/reply。已有邻居缓存会改变顺序，背景 IPv6 也会带来额外帧；抓包不能只靠“第几帧”认定业务包。

## 固定队列怎样实现延迟

本实现每方向最多 32 帧、同时有 1 MiB 字节预算。入队时给帧计算单调时间 `due`，owner 在到期时尝试写出，而不是对每一帧阻塞 `sleep(100ms)`。

后者会把两个方向和控制处理一并阻塞。前者把等待转成队列状态，循环可以继续读其他源、执行命令或处理停止，但必须限定帧数和字节总量。[事件与时间](06-events-time.md)解释 due、可写监听与处理预算的关系。

单向各添加 100 ms 时，ping 的来回路径约增加 200 ms；实际 RTT 还包含协议栈、调度和测量误差。网络脚本核对延迟下限，不把某一次 RTT 当成精确服务时间保证。

## 丢弃计数与端到端背压

队列满丢新帧、策略性丢帧、转发被禁止和停止时丢弃，都是应明确计数的不同原因。确定性隔帧测试使用专用 EtherType `0x88B5`，按该类型的序号核对 1/3/5，以免 ARP/IPv6 改变全体帧编号。

```text
源应用 → socket → qdisc → TAP → 用户态队列 → 对端协议栈 / 应用
```

每层有自己的容量和满时行为。用户态丢弃不一定能同步回传到源应用，更多缓存也无法弥补持续到达率高于服务率。[资源预算](https://xidianedu.cc/tech/platform/design/06-resource-budget/)用队列账和排空时间描述这些限制。

## 运行与输出位置

在宿主的源码根目录执行，网络权限由实验脚本放到一次性容器内：

```sh
./scripts/run-container.sh network
```

不要把这条命令再放进普通工具容器。脚本会构建与执行网络集成，正常通过时包括 local-delivery、ARP/ICMP 抓包、双向 100 ms 延迟和确定性丢弃结果。

输出集中在 `build/network/`，例如：

```text
normal.pcap       ARP / ICMP 抓包
frames.txt        抓包的文字展开
delay.log         添加延迟后的 ping 记录
local-route.txt   同空间目的地址的 local route
local-ping.txt    local route 对照的 ping
```

新的实际结果以脚本本次日志和退出码为准；这些是应生成的观察材料。若无法创建 TAP 或 namespace，应先检查环境能力，不能删除路径对照后仍宣布集成成功。

## 从模拟链路走向真实 backend

本实验解释 Linux 软件路径中的接口责任、队列和故障注入。它没有验证射频、固件、DMA、真实网卡功耗或 MCU 中断路径；MTU、TCP/UDP 慢消费者以及暂停 TAP 读取的上游传播，也需要按对应问题扩展实验。

TAP 因而是可观测的工程载体。把测试结论带入另一 backend 时，需要保留帧边界、容量、丢弃、时间和停止契约，再替换平台实现。[并发与所有权](07-concurrency-ownership.md)说明帧在途时谁还能复用 buffer，[运行时边界](https://xidianedu.cc/tech/platform/design/03-linux-freertos/)讨论共享契约与各平台机制的关系。
