# write 成功以后，还欠哪些保证

`write` 返回 5，并不自动形成一条五字节的业务消息，也不证明对端处理完成。对配置文件而言，还要区分进程能看到新内容和断电后仍能看到新内容。这些差别会影响解帧、重试和保存顺序。

本节使用 `labs/mechanisms.c` 的 `stream_lab()`、`partial_write_lab()`、`persistent_file()`，以及 `labs/extra.c:buffering()`。先取得[源码](../reference/source.md)，按[环境说明](../guide/environment.md)运行。

## 用九个字节拆开流的边界

实验发出两条带两字节长度头的消息：

```text
00 03 A B C | 00 02 D E
```

发送端先写一个字节，再写剩下八个字节；接收端每次最多读两个字节，累计后核对完整内容。应用消息边界来自协议头，而不是两次 `write` 的边界。TCP 同样提供有序字节流，应用需要自行分帧。[TCP 接口说明](https://man7.org/linux/man-pages/man7/tcp.7.html)

如果换成 datagram，情况又不同。实验发送五字节 `ABCDE`，但只给接收端两字节容量：本次取出 `AB`，尾部不留给下一次 `recv`；切成非阻塞以后，下一次返回 `EAGAIN`。这不是“下一块消息尚未到达”，而是本次接收容量不足造成截断。

## 部分写需要记录进度

非阻塞 stream 发送大缓冲时，`send` 可以只推进一部分；发送缓冲满后返回 `EAGAIN`。恢复时必须从尚未发送的位置开始。下面是行为示意，错误分支需按接口进一步展开：

```c
while (sent < total) {
    ssize_t n = send(fd, bytes + sent, total - sent, MSG_NOSIGNAL);
    if (n > 0)
        sent += (size_t)n;
    else if (n < 0 && errno == EAGAIN)
        break;  /* 保存 sent，等待可写后继续 */
    else
        handle_error();
}
```

不能从头重发已经成功的前缀，否则接收端会得到重复内容。也不能把这个流式循环直接用于拆分一条 TAP 以太网帧：报文接口的发送边界另有约定。[网络与 TAP](09-network-tap.md)继续讨论帧边界。

## 配置替换的两个对象：文件与目录项

`persistent_file()` 在自己创建的临时目录中执行：

```text
独占创建 config.tmp
  → 写入 version=1
  → fsync 临时文件并关闭
  → rename 为 config
  → fsync 所在目录
  → 重新打开并核对内容
```

文件同步请求覆盖文件数据及相关元数据；文件名替换改变目录项，还需要对目录 fd 同步。`rename` 的可见原子性与介质上的持久性是不同保证。[fsync 手册](https://man7.org/linux/man-pages/man2/fsync.2.html)

实际实现还要处理每一步的错误，确保临时文件与目标在允许原子替换的文件系统范围内，并定义失败时保留旧配置还是恢复备份。实验只验证这组调用及可见结果，没有通过物理断电测试存储设备的承诺。

`fflush` 处理 stdio 的用户态缓冲。`buffering()` 对比正常 `exit` 与 `_exit`：未主动 flush 的 stdio 内容在后一条路径中没有写出。即使 flush 成功，仍需按用途考虑文件同步和介质保证。

## 运行与观察

容器内源码根目录：

```sh
make -C labs all
./build/labs/mechanisms stream
./build/labs/mechanisms partial-write
./build/labs/mechanisms save
./build/labs/mechanisms extra
strace -f -e trace=%file,fsync,write,close \
  -o build/io-syscalls.log ./build/labs/mechanisms save
```

对应测试通过时输出以下记录：

```text
L1-L6-stream-vs-datagram-boundary
L3-partial-write-EAGAIN-offset
L1-save-rename-file-directory-fsync
L1-stdio-exit-vs-unflushed-exit
```

每条记录都有 `result: PASS`。`extra` 同时包含 stdio、公平性、旧 ready 身份和权限补充实验。trace 中查找 `platform-save-` 路径，核对文件与目录分别被同步；`%file` 也捕获目标架构使用的 renameat 等路径调用。实际 partial-write 的分块大小由 socket 缓冲和环境决定，测试关心完整内容、没有重发前缀和确实经历 `EAGAIN`。全部回归另执行 `make -C labs test`。

## 接口上写清成功属于哪一层

| 返回 / 事件 | 本层可以承诺什么 | 后续仍需什么 |
|---|---|---|
| API 入队成功 | 本地队列接收了输入 | owner 处理及容量判断 |
| stream 写入成功 | 本次字节进入该发送接口 | 对端读取、解帧 |
| 业务响应 | 对端给出了协议规定结果 | 按产品语义确认执行或持久化 |
| 文件同步完成 | OS/文件系统按接口完成同步请求 | 实际设备的掉电验证 |

RTOS flash 文件系统的介质、磨损管理和缓存路径可能不同，不能凭 Linux 顺序直接扩大为另一平台的掉电保证。[SDK 契约](../design/02-sdk-contract.md)把这类分层成功用于接受、完成、取消和停止的定义。
