# DMA Ring、Doorbell 与内存顺序

DMA 的正确性需要分别解决地址映射、缓存一致性、观察顺序和所有权。`volatile`、普通 CPU release/acquire、DMA sync 与 MMIO accessor 各有作用，不能相互替代。

## 先画三种地址

CPU 虚拟地址供内核访问，CPU 物理地址对应内存，DMA/bus 地址供 Device 使用。IOMMU 可能使后两者不同。Driver 应使用 DMA API 返回的地址，而不是把指针强转为整数写 descriptor。

Probe 阶段验证 DMA mask/coherent mask 与硬件地址宽度；错误截断会表现为低地址内存正常、某些分配地址随机损坏。参考 [Linux 6.12 DMA API](https://docs.kernel.org/6.12/core-api/dma-api-howto.html)。

## 本文具体模型：coherent descriptor + streaming payload

以下示意假设 ring 由 coherent DMA 分配，payload 用 streaming DMA 映射；slot 的 owner 协议、doorbell 访问方式已由硬件规范定义。伪代码不是可直接复制的完整驱动。

```c
/* slot 已回收到 Host，producer 受单生产者规则或锁保护 */
dma = dma_map_single(dev, payload, len, DMA_TO_DEVICE);
if (dma_mapping_error(dev, dma))
    return mapping_failed;

desc->addr = cpu_to_le64(dma);
desc->len = cpu_to_le32(len);
desc->cookie = cpu_to_le32(cookie);
dma_wmb();                         /* 字段先于 owner 对 Device 可见 */
WRITE_ONCE(desc->owner, DEVICE);
writel(next_producer, doorbell);    /* 使用平台规定的 ordered MMIO */
```

写 owner 之前字段必须完整；如果 Device 轮询 owner，只在 doorbell 前加屏障已经太迟。coherent 内存不需要常规 cache flush，却仍需要顺序保证。

Payload 映射到 Device 后，CPU 不应继续随意读写同一 streaming buffer。持续映射方案需要按所有权转换使用相应 sync；一次性方案在合法 completion 后 unmap。映射成功不表示发送成功。

## Completion 消费与 RX

仍假设 completion descriptor 是 coherent：

```c
if (READ_ONCE(cdesc->owner) != HOST)
    return no_completion;
dma_rmb();                         /* 先看到完成，再读取其余状态 */
cookie = le32_to_cpu(cdesc->cookie);
length = le32_to_cpu(cdesc->len);
validate_cookie_generation_and_length(cookie, length);
/* 根据契约确认 Device 不再访问 payload，再 sync/unmap 并消费 */
```

RX payload 若用 streaming DMA_FROM_DEVICE，在 CPU 解析前执行相应 sync 或 unmap；重投前再次转给 Device。不能在验证长度之前复制数据，也不能在网络栈仍持有页面时重新把它用于 RX。

## 非一致性 descriptor 不能套上面的 owner 轮询

若 descriptor 本身不是 coherent，CPU 可能连 owner 都读到旧 cache line。此时“先读 owner，再 dma_sync_for_cpu”不能成立。平台必须定义独立可见的完成通知及 descriptor 所有权转移，再同步整个受保护范围。

同样，不能在 CPU 清理包含 owner 的 cache line 时让 Device 并发改写同一行；否则后写回可能覆盖 Device 状态。需要 cache-line 隔离、分离的 producer/consumer 区域或专用 coherent control ring。屏障不能修复缓存行并发所有权冲突。

## Scatter-gather 的两个 nents

`dma_map_sg()` 可能合并相邻段。构造硬件 SG 使用返回的 mapped segment 数；unmap/sync 按 DMA API 要求使用原始输入 nents。混淆两者会在特定内存布局下才出错。

还要检查返回失败、硬件最大段数、每段长度/边界、映射方向和 unwind。不要把“SKB 有 N 个 frag”等同于“硬件一定需要 N+1 descriptor”。

## Ring 数学与回绕

采用单调无符号 producer/consumer、容量 N，定义：

```text
used = producer - consumer
free = N - used
0 <= used <= N
slot = producer mod N
```

仅当 N 为 2 的幂，`producer & (N-1)` 才等于取模。若硬件仅提供模 N 指针，则需要 phase/owner bit、单独计数，或约定保留一个空槽来区分满和空；不能混用两种容量算法。

教学例：N=8、producer=14、consumer=9，则 used=5、free=3，下一槽位为6。消费3项后 consumer=12，free=6。无符号计数回绕前提是差值始终在协议可表示范围内，不能把异常巨大差值当作合法空闲容量。

## Credit 与 Ring slot 分开归还

Ring slot 可能在 Device 取走 descriptor 时归还；Firmware buffer credit 可能到 MAC terminal completion 才归还。提交同时需要两者，不能收到任意 completion 就把两个计数都加一。

统计 `ring_used`、`fw_credit`、`bus_inflight` 和 `air_pending` 四项。Reset 后旧 completion 不能给新 generation 增加 Credit。单独把所有计数清零会掩盖所有权丢失。

## Stop、Reset 与释放顺序

先阻止新提交，再屏蔽/同步完成路径，按设备协议停止或隔离 DMA，等待 quiesce，最后 unmap/free。若 Device 已失联，无法仅凭“等待了一段时间”证明不再 DMA；需使用平台支持的复位/总线隔离机制。

不要在拿着 completion 所需的锁时等待 completion；否则恢复自身造成死锁。中断停止、NAPI 停止、Firmware 停止和总线 DMA 停止是不同条件。

## 故障注入与断言

- map failure、SG 合并数变化、DMA 地址高位非零；
- producer/consumer 回绕、满/空边界、重复 cookie；
- owner 已发布但字段不可见的模拟乱序；
- RX length 大于 buffer、旧 generation completion；
- reset 与 DMA/IRQ/Host 交付同时发生。

验收要同时证明无越界、无重复回收、映射/引用最终释放、可解释的终止状态以及恢复后继续发收。

## 复习追问与答案

**coherent 为什么仍需要 dma_wmb？** 缓存一致性保证可见内容，不自动保证 Device 观察字段与 owner 的先后关系。

**dma_sync 能保证 Device 停止访问吗？** 不能；它参与缓存/所有权协议，但 Device quiesce 仍需硬件或传输协议证明。

**为什么满环也可能被错误判为空？** 只比较取模指针时两个状态相同，必须有额外 phase 或容量约定。

关联：[总线请求](01-usb-sdio-pcie.md)、[SKB/NAPI](../04-Linux-Stack/02-skb-netdev-napi.md)、[Host–Device ABI](../05-Driver-Firmware/02-host-device-abi.md)。
