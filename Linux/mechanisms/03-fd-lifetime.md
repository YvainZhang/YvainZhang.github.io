# fd 数字复用以后，旧资源去了哪里

程序把 `fd` 存在一个整数里，关闭后又打开文件，发现新文件拿到了同一个数字。再拿旧整数写入，写到了哪里？这个问题把描述符表、打开文件对象、偏移和异步身份连在了一起。

实验代码是[源码包](https://xidianedu.cc/tech/platform/reference/source/)中的 `labs/mechanisms.c:fd_lab()`。运行前按[环境说明](../guide/environment.md)进入工具容器。

## 分开看三个层次

fd 是进程描述符表的索引；表项引用内核的打开文件描述（open file description），后者保存文件偏移和状态标志。再次 `open` 同一路径通常建立新的打开文件描述；`dup` 新增表项，并引用原来的打开文件描述。[open 手册](https://man7.org/linux/man-pages/man2/open.2.html)、[dup 手册](https://man7.org/linux/man-pages/man2/dup.2.html)

```text
进程表项                  打开文件描述               文件内容
one ─┐
     ├─────────────────→ A：offset 共享 ─────────→ ABCDEF
two ─┘（dup）
three ─────────────────→ A2：offset 独立 ────────→ ABCDEF
```

把 `int saved = one` 理解为复制一个索引值。它没有新增表项，也没有保住资源。`dup(one)` 才建立另一份描述符引用。

## 按每一步推导结果

`fd_lab()` 用临时文件 A 写入 `ABCDEF`，定位到开头；建立 `two = dup(one)` 和 `three = open(A, O_RDONLY)`。下面的表对照源码里的断言：

| 操作 | 读到的字节 / 结果 | A 共享偏移 | A2 独立偏移 |
|---|---|---:|---:|
| `read(one, 1)` | A | 1 | 0 |
| `read(two, 1)` | B | 2 | 0 |
| `read(three, 1)` | A | 2 | 1 |
| `close(one)` | 表项删除，two 仍有效 | 2 | 1 |
| `read(two, 1)` | C | 3 | 1 |
| `open(B, O_RDWR)` | 受控实验中复用 one 的编号 | 3 | 1 |
| `write(saved, "NEW", 3)` | 写入 B | 3 | 1 |

前四步说明关闭一个表项不等于销毁所有引用。后两步说明数字相同不等于身份相同。本实验在单线程中控制所有 fd 分配，因此可以断言低编号复用；真实服务的其他线程也可能在这个空隙分配 fd。

## 运行，并在系统调用层核对

容器内源码根目录：

```sh
make -C labs all
./build/labs/mechanisms fd
strace -f -e trace=openat,dup,close,read,write,lseek \
  -o build/fd-syscalls.log ./build/labs/mechanisms fd
```

`fd` 参数只运行本节实验。对应的预期记录是：

```text
{"lab":"L1-fd-dup-offset-reuse","result":"PASS"}
{"lab":"L1-errno-only-after-failure","result":"PASS"}
{"lab":"all-fd-resources-return-to-baseline","result":"PASS"}
```

查看 `build/fd-syscalls.log` 中带 `platform-fd-a-` / `platform-fd-b-` 的临时路径，跟踪对应 fd 的 `dup/read/close/openat`。编号由本次进程环境决定，无需与某个示例编号一致。程序的断言核对读到的字节，trace 核对引用关系的操作顺序。

## 返回值决定怎样解释错误

对 `open` 检查 `fd < 0`，fd=0 可以合法。对 `read`，正数是实际读取量，0 在这里表示 EOF，负数才按接口约定解释 `errno`。成功调用没有义务清空先前的 `errno`；pthread 的许多接口则直接返回错误码。

Linux `close` 报错后不能盲目按同一数字重试：描述符通常已被释放，其他线程可能复用了它。是否需要预先 `fsync`、如何报告落盘错误，应按文件用途设计。[close 手册的重试说明](https://man7.org/linux/man-pages/man2/close.2.html)

## 异步系统还要保存代际身份

事件循环已经取出一个 ready batch，处理第一项时关闭某个 fd，随后新连接复用该数字；batch 后面的旧记录仍留在用户空间。此时只比 fd 数字可能把旧事件交给新对象。

`labs/extra.c:stale()` 用保存的旧 epoll 记录与新 generation 对照，展示这种身份检查。可在容器内执行 `./build/labs/mechanisms extra` 查看它与公平性等补充实验的结果。实际设计可使用受保护的 slot + generation，保证访问前能确认对象属于当前代际；销毁和引用规则仍需另外落实。[事件与时间](06-events-time.md)进一步讨论 ready 信息和真正工作之间的区别。

同样的问题会出现在 buffer、SDK 请求和驱动对象中。引用保护寿命，锁保护访问的并发规则，generation 识别对象版本；各自承担的职责需要写进接口。[设备解绑](10-kernel-lifetime.md)展示持有引用却已经禁止新工作的对象，[exec 描述符案例](../cases/04-exec-fd.md)讨论继承边界。完成单节观察后，用 `make -C labs test` 跑全部机制与构建回归。
