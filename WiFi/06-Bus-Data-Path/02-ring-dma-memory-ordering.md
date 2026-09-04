# DMA Ring、Doorbell 与内存顺序

Ring 看起来只是 producer/consumer index，真正的 bug 往往来自“对方先看到指针，后看到 Descriptor”或“CPU 读取了旧的 completion”。`volatile` 不能替代 DMA API 和内存屏障。

## TX 发布顺序

概念顺序如下，但不能把它直接复制成跨平台代码：

```c
slot = ring[producer & mask];
map_or_sync_payload_for_device(payload);
fill_descriptor_fields(slot); /* 此时仍不可被 Device 消费 */
publish_descriptor(slot);     /* 按内存类型完成 sync + ordering + valid/owner */
dma_write_barrier();          /* descriptor publish before producer/doorbell */
update_producer(producer + 1);
mmio_write_doorbell();
```

`publish_descriptor()` 必须由平台明确实现：coherent ring 通常先写普通字段，再用 release/`dma_wmb()` 语义发布 `valid/owner`；non-coherent ring 则要在完整表项（包括最终所有权字段）写完后，对正确的 DMA 范围执行 sync。Payload 的 streaming mapping 与 Descriptor ring 的一致性属性要分开描述。

核心不变量是：Device 观察到 `valid/owner`、producer 或 doorbell 中任何一个“可消费”信号时，必须已经能看到完整 Descriptor 和 Payload。若 Device 会主动轮询 owner，仅在 doorbell 前加屏障并不充分。

## RX/Completion 消费顺序

```c
owner = read_owner(slot);
if (owner != HOST)
    return;
dma_read_barrier();           /* ownership before descriptor fields */
dma_sync_for_cpu_if_needed(slot);
validate_length_offsets_status(slot);
consume_and_refill(slot);
```

Host 读到 completion 后才能回收 DMA mapping 和 SKB。Reset 路径要阻止 Device DMA、等待或强制终止 inflight，再 unmap/free；否则会形成 use-after-free DMA。

## Ring 数学

单调 producer/consumer 比只存模 N 指针更容易区分空和满：

```text
used = producer - consumer
available = ring_size - used
0 <= used <= ring_size
```

比较使用无符号回绕语义，并限制任意时刻差值不超过可表示范围的一半。每次操作都断言 `used <= ring_size`；发现破坏后停止消费并保留现场，不要继续移动指针掩盖根因。

## Credit 与 Ring 不是同一个量

Ring slot 表示 Host Interface 容量，Firmware credit 可能表示内部 queue、Peer/TID 配额或 buffer。提交条件应同时满足两者；归还路径必须标明归还哪种资源。常见永久停队是 completion 归还 Ring slot，却遗漏 credit update，或 reset 时 credit 重置但 Host 仍保留旧值。

## 总线差异

- PCIe：Descriptor 与 payload 常通过 DMA，Doorbell 是 MMIO；关注 IOMMU、MSI-X 和 ordering。
- USB：URB 是 Host Controller 事务，没有共享 DMA Ring 也可在软件层形成 request ring；URB complete 不等于空口完成。
- SDIO：CMD53 与 block aggregation 主导，Host claim 与 IRQ thread 会影响控制/数据公平性。

建议为每次发布与消费记录 ring id、slot、cookie、producer/consumer、credit、generation 和时间戳，抽样即可，不要默认全量打印。
