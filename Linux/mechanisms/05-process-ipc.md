# backend 消失后：IPC、请求和子进程怎样收尾

把设备模拟器放到独立进程，可以让断连与进程退出有清楚的边界；同时也增加了启动、描述符继承、活跃请求失败和子进程回收的责任。仅看 socket 返回 EOF，清理还没有结束。

先读[fd 与对象寿命](03-fd-lifetime.md)、[字节流与报文](04-io-persistence.md)。实验环境和包内路径分别见[环境说明](../guide/environment.md)、[源码说明](https://xidianedu.cc/tech/platform/reference/source/)。

## fork：初值相同，修改去往不同对象

`labs/mechanisms.c:ipc_lab()` 先设 `local = 3`，再 `fork`。子进程把自己的变量改为 7，通过 pipe 发送；父进程收到 7，自己的 `local` 仍为 3，最后用 `waitpid` 确认子进程成功退出。

```text
父进程 local=3 ──fork──→ 子进程初始 local=3
父进程仍为3               子进程改为7，pipe写出7
             ←──────────── 父进程读到7
waitpid回收子进程
```

普通私有内存的修改隔离，不表示 pipe/socket 等内核对象也各自独立。fork 继承的描述符仍可能引用同一个打开对象。共享映射可以让父子看到同一份数据，但访问顺序还要靠同步；本实验的共享映射用 `waitpid` 建立子进程完成后父进程再读的顺序。

## 一个线程阻塞，其他线程仍能推进

`blocking_lab()` 的工作线程进入阻塞 `read`，主线程确认它尚未完成，然后写入 `Q`。读线程得到数据后退出，主线程 join。

这里的等待只阻塞调用线程。若主线程持有了读线程完成所需的锁，再等待它，则可能因自己的锁依赖停住整个流程。设计问题因此落到“谁在等待，仍持有什么，谁能产生唤醒条件”。

## IPC 的选择带来什么代价

| 方式 | 本实验中的用途 | 需要另外处理的责任 |
|---|---|---|
| pipe / stream | 简单字节交换 | 分帧、部分读写、关闭多余端点 |
| Unix seqpacket | SDK 与模拟器的命令和响应 | 有界报文、容量、断连、协议身份 |
| 共享内存 | 显示共享修改与同步 | 发布顺序、容量和双方对象寿命 |

SDK 使用 Unix `SOCK_SEQPACKET`，保持单条协议报文的边界；模拟器经 `posix_spawn` 启动。源码入口为 `platform/runtime/linux/runtime.c:backend_open()` 和 `platform/backends/simulator.c`。这一选择让故障路径容易观察，并没有证明它在所有负载下比其他 IPC 更快。

## 继承关系会改变 EOF 条件

pipe 的读端只有在所有写端都关闭后才能观察到结束。父子进程遗留一份不使用的写端，会让预期 EOF 一直不出现。实验在 fork 后分别关闭不属于自身职责的端点；创建描述符时使用 CLOEXEC，避免非预期的 exec 继承。

`posix_spawn` 的文件动作还有专门的规则，不能把直接 `dup2(fd, fd)` 的行为照搬进去。[exec 描述符案例](../cases/04-exec-fd.md)单独核对这种边界。

对于对端退出，本实验临时忽略 SIGPIPE，再写入没有读端的 pipe，核对 `EPIPE`。服务程序应根据设计统一处理信号与发送错误；接收到错误仍需回收自己持有的端点。

## SDK 的三项收尾责任

```text
通道 EOF / 协议故障
  → 不再用这条连接发送
  → 将该连接的 live 请求推进到终态
  → 回收通道、子进程与等待状态
```

通道结束是传输事件；请求终态是对调用者的业务通知；`waitpid` 是子进程资源责任。遗漏任一项，都可能留下等待者、live 请求或僵尸进程。

正常停止应先约定退出条件和有界等待，再定义超时后的强制回收策略。先释放工作对象再 join，会让仍运行的线程访问失效地址。[停止与排空案例](../cases/01-stop-drain.md)把入口、queued 与 accepted 三层义务连接起来。

## 运行与核对

容器内源码根目录：

```sh
make -C labs all
./build/labs/mechanisms ipc
./build/labs/mechanisms blocking
make -C platform linux-test
```

机制记录中核对 `L2-fork-isolation-pipe-wait`、`L2-exec-failure`、`L2-peer-exit-EPIPE` 和 `L2-L3-blocked-thread-other-thread-progress`；SDK 记录中核对 `multi-instance-disconnect`、`recover-failure`、`cleanup-baseline`。这些是测试成功时的名称，具体路径见各断言及本次输出。完整机制回归为 `make -C labs test`，共享映射可继续执行[内存实验](08-memory-performance.md)。

`exec-failure` 示例在 exec 失败后 `_exit(127)`，父进程检查该退出码；它没有把 exec 失败误当成运行了目标程序。多线程进程的 fork→exec 间存在库状态继承限制，这里使用受控小例子，生产实现需要按接口规定设计该区间。[fork 手册](https://man7.org/linux/man-pages/man2/fork.2.html)

FreeRTOS task 通常共享一个地址空间。可以复用请求状态和错误结果，但不能把 Linux 子进程的隔离保证当成 task 的天然属性。[运行时边界](https://xidianedu.cc/tech/platform/design/03-linux-freertos/)给出两种执行环境的具体对照。
