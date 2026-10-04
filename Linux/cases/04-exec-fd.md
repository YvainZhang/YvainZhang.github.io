# 同一个 fd 编号，dup2 与 spawn 文件动作有什么区别

Linux runtime 用带 `SOCK_CLOEXEC` 的 socketpair 建立 IPC，并把子端安排到固定 fd=198，再启动设备模拟器。源 fd 也恰好是 198 时，CLOEXEC 应怎样处理？这个问题必须分别核对直接 `dup2` 和 `posix_spawn` 文件动作的语义。

本例是一组语义对照与启动回归。现有证据没有证明省去源编号规范化分支会导致通道消失，因此不把该分支描述为已证实事故的必要修复。实现和测试见[源码与版本](https://xidianedu.cc/tech/platform/reference/source/)，fd 对象关系见[文件描述符生命周期](../mechanisms/03-fd-lifetime.md)。

## 描述符标志与对象状态分开

fd 是进程描述符表中的编号，引用底层 open file description。复制描述符以后，两项可能共享文件偏移和状态标志，但各自的 `FD_CLOEXEC` 是描述符标志。[Linux dup 手册](https://man7.org/linux/man-pages/man2/dup.2.html)

`FD_CLOEXEC` 的作用是在成功 exec 时关闭这一描述符。父进程希望普通内部 fd 自动关闭，同时又需要明确保留子进程的 IPC 通道，就要在启动动作中安排继承。

## 两个同编号操作采用不同规则

| 操作 | 有效源与目标相同 | CLOEXEC 结果 |
| --- | --- | --- |
| 直接 `dup2(fd, fd)` | 不创建新表项，返回原 fd | 保留原描述符标志 |
| `posix_spawn_file_actions_adddup2(&actions, fd, fd)` | 注册在 child 启动阶段执行的动作 | 该动作清除目标 CLOEXEC |

spawn 的同编号动作有明确特殊规则，不能只看函数名里含 `dup2` 就套用直接调用的行为。[Oracle spawn 文件动作说明](https://docs.oracle.com/cd/E88353_01/html/E37843/posix-spawn-file-actions-adddup2-3c.html)

注册文件动作不会立即修改父进程 fd。动作在 child 启动期间执行；parent 的 CLOEXEC 仍保持原样。对于有效同编号 fd，成功启动的 child 可以继续使用安排好的描述符。

## 先做语义实验，再测 SDK 路径

公开源码的 `platform/tests/runtime_test.c` 包含两项不同目的的测试。在[专用 Linux 工具容器](../guide/environment.md)的项目根目录运行：

```sh
make -C platform linux-test
```

第一项 `dup2-vs-spawn-same-fd-CLOEXEC`：

1. 打开带 CLOEXEC 的 `/dev/null`，复制到受控编号。
2. 直接执行 `dup2(fd, fd)`，用 `F_GETFD` 检查 CLOEXEC 仍设置。
3. 注册同编号 spawn 动作，启动测试程序的 child probe。
4. child 检查该 fd 有效且 CLOEXEC 已清除，正常退出。
5. parent 再检查自己的 CLOEXEC 仍设置，关闭资源并核对 fd 基线。

这项测试回答两个 API 的差异，避免把端到端成功误当成语义已经解释正确。当前执行环境与结果从[验证记录](https://xidianedu.cc/tech/platform/reference/verification/)查阅。

第二项 `spawn-child-fd-collision-roundtrip` 先占用低编号 fd，让 runtime 创建的 socketpair 子端落在 198，随后验证 start、回显、destroy 与 fd 基线。它检查当前完整实现的碰撞路径。

## 当前实现保留的源编号规范化

源端等于 198 时，runtime 用 `F_DUPFD_CLOEXEC` 把它复制到至少 199 的其他编号，关闭原源，再注册不同源到 198 的 spawn 动作。该处理使当前分支始终使用不同源编号，失败路径同时关闭资源。

按照上面的 spawn 语义，同编号动作已经应当清除 CLOEXEC。现有规范化是一项额外处理，不能据它通过回归就反推原方式必然失败。评估是否移除时，可以在固定 libc 和源码版本下做受控对照，保留启动、握手、失败回滚和 fd 泄漏检查。

## 跨进程接口还要定义关闭责任

启动协议同时包含消息和资源规则：child 通过哪个 fd 通信，parent 何时关闭子端，其他 fd 怎样防止误继承，启动失败由谁清理，backend 退出后由谁 waitpid。

误继承的额外引用可能使 EOF 迟迟不出现；保存整数也不能延长描述符对象的寿命。固定编号、参数传递和描述符传递协议各有成本，选择以后把继承、关闭和启动握手一起测试。[进程与 IPC](../mechanisms/05-process-ipc.md)
