# 从一段报文看 C 对象与 ABI

一个 backend 返回了 51 字节：48 字节头部，后面跟着 `ABC`。接收端怎样知道这三个字节在哪里、能否读取，以及属于哪次请求？这几个看似简单的问题，决定了跨进程、跨 OS 接口的第一层边界。

本文围绕源码包中的 `platform/core/wire.c` 展开。下载及路径说明见[源码与版本](https://xidianedu.cc/tech/platform/reference/source/)，编译环境见[实验环境](../guide/environment.md)。

## 地址、容量、长度是三件事

传给解析器的 `p` 是地址，`len` 是调用方确认收到的字节数；报文头里的 `length` 是对端的声明。解析器不能用声明证明内存存在。

例如，实际收到 20 字节，头部声明 payload 有 256 字节。此时连完整头部都没有，读取长度字段以外的后续字段、复制 payload 都没有依据。检查顺序应当从已知范围逐步扩大：

```text
实际长度覆盖固定头部？
  → magic / version 能否识别？
  → 声明长度是否在本地上限内？
  → 实际长度是否恰好等于头部 + 声明长度？
  → 消息类型与该类型的长度约束是否合法？
  → 解码字段并复制 payload
```

本实现的 wire header 固定为 48 字节，控制 payload 上限为 256 字节，数据 payload 上限为 1024 字节。这里的数字是协议和本地资源契约，不由 `sizeof(struct wire_message)` 推导。

## 结构体布局不能直接充当协议

`struct wire_message` 是程序内的对象：它包含 `enum`、`size_t`、键和字节数组。编译器如何填充、目标 ABI 如何对齐，与线上各字段所在字节位置分别定义。

| Wire 偏移 | 字段 | 编码规则 |
|---|---|---|
| 0–3 | magic、版本、类型 | 逐字节写入 |
| 4–7 | payload 长度 | 32 位小端 |
| 8–15 | instance、generation | 两个 32 位小端字段 |
| 16–23 | 请求 id | 64 位小端 |
| 24–31 | flags、status | 两个 32 位字段 |
| 32–47 | sequence、backend_dropped | 两个 64 位小端字段 |
| 48 起 | payload | 声明长度的字节 |

`get32()` 按字节拼值，避免把任意地址强转成需要特定对齐的结构体指针。比如字节 `78 56 34 12` 被解为 `0x12345678`，与本机原生端序无关。`packed` 能改变某些编译器的布局，但不能替代长度检查、端序规则或版本兼容。

下面是 `wire_decode()` 的关键检查。完整源码还会检查消息类型及控制长度：

```c
if (!m || !p || len < WIRE_HEADER || p[0] != 'P' || p[1] != 'S')
    return SDK_EINVAL;
if (p[2] != SDK_API_VERSION)
    return SDK_EVERSION;
uint32_t n = get32(p + 4);
if (n > SDK_DATA_MAX || len != WIRE_HEADER + n)
    return SDK_EINVAL;
```

先限定 `n`，再做总长比较；协议固定上限也让这里的加法范围可推理。其他允许任意长度的协议，应另外处理加法溢出，不能机械套用这一段。

## 跑一次边界向量

在工具容器的源码根目录执行：

```sh
make -C platform core-test
```

检查输出中的这两个向量：

```text
{"vector":"length-reject","result":"PASS"}
{"vector":"wire-truncation-version-endian","result":"PASS"}
```

这是测试通过时的预期输出格式。测试位于 `platform/tests/core_vectors.c`：构造包含 `ABC` 的报文，逐个尝试不足完整报文的长度，校验版本错误及字段往返。它验证这些输入对应的行为；更长的模糊测试、其他 ABI 或未知协议扩展仍需另做。

可以把声明长度改大而保持实际数据不变，观察拒绝发生在复制之前。另一项有价值的修改是降低控制上限：同时检查 API 参数、decoder、固定池、测试和协议兼容，不能只改一个宏后以编译成功结束。

## 从字节边界走向对象寿命

解码成功证明本次读取范围合法，并不证明调用方可以永久持有 payload 地址。栈对象返回后失效，池对象会复用，异步回调中的借用也可能只持续到回调结束。

因此跨平台接口需要同时写清两种契约：线上数据如何解释，以及程序内对象由谁保管多久。[并发与所有权](07-concurrency-ownership.md)继续展开 buffer 提前归池的问题；[SDK 契约](https://xidianedu.cc/tech/platform/design/02-sdk-contract/)把输入复制、接受与完成连接成完整接口。

Linux 和 FreeRTOS 可以共用这套 wire/core，因为协议不发送进程地址、原生 `size_t` 或编译器结构体布局。共享协议是跨 OS 的起点，线程、计时和退出语义仍需各自实现。
