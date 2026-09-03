# Ring Buffer、无锁队列与内存序

## 1. SPSC Ring 的最小模型

Single Producer/Single Consumer Ring 只允许一方更新 `head`，另一方更新 `tail`：

```text
Producer owns head                  Consumer owns tail
        │                                   │
        ▼                                   ▼
+------+------+------+------+------+------+------+
| slot | slot | slot | slot | slot | slot | slot |
+------+------+------+------+------+------+------+
          tail                 head
```

对于大小为 `2^N` 的 Ring：

```c
next = (head + 1) & (RING_SIZE - 1);
full = next == tail;
empty = head == tail;
```

这种写法牺牲一个 Slot 区分 Full 和 Empty。也可以使用单调递增计数器，通过差值判断占用量，但必须定义整数回绕语义。

## 2. 发布与消费顺序

Producer 的正确顺序：

```c
ring->slot[head] = message;                 /* 普通数据写 */
atomic_store_explicit(&ring->head, next,
                      memory_order_release); /* 发布 */
```

Consumer：

```c
head = atomic_load_explicit(&ring->head,
                            memory_order_acquire);
if (tail != head)
    message = ring->slot[tail];
```

Release/Acquire 建立的是 Happens-Before：Consumer 一旦通过 Acquire 观察到新 `head`，必须能够观察到该 Head 发布前写入的 Slot 内容。

只把 `head` 声明为 `volatile` 不够。`volatile` 主要约束编译器对单次访问的处理，不提供跨线程原子性和 C/C++ 内存序关系。

Ring 的反向所有权移交同样需要成对设计。Producer 以 Acquire 读取 `tail`，确认 Consumer 已经 Release 归还 Slot 后，才允许覆盖该位置：

```c
/* Producer：确认可复用。 */
tail = atomic_load_explicit(&ring->tail, memory_order_acquire);
if (next == tail)
    return -ENOSPC;

/* Consumer：读完 Slot 后再发布归还状态。 */
message = ring->slot[tail];
atomic_store_explicit(&ring->tail, next_tail, memory_order_release);
```

Acquire/Release 保证的是内存操作次序和所有权边界，不是“让一次普通读取被另一端看见”。Producer 关心的是：只有在观察到新 `tail` 后，才能把该 Slot 当作空闲空间重新写入。

在异构核共享区中还要确认原子访问的硬件条件。C11 `atomic_uint` 并不自动证明两个不同 ISA、不同编译器和不同一致性域之间具有系统级原子性。ABI 必须规定字段宽度、自然对齐、Shareability、原子指令能力以及 Cache 属性；条件不满足时，应使用 Mailbox 仲裁、硬件队列或单写者协议。

## 3. 避免 Head/Tail False Sharing

若 `head` 与 `tail` 位于同一 Cache Line，两端每次推进索引都会争夺同一行：

```c
struct bad_ring {
    atomic_uint head;
    atomic_uint tail;
    uint32_t slots[64];
};
```

应按参与者中最大的 Cache 维护粒度隔离，而不是在所有平台上固定假设为 64 字节：

```c
#define IPC_CACHELINE_MAX 128U /* 由平台契约生成或静态校验 */

struct ring_index {
    _Alignas(IPC_CACHELINE_MAX) atomic_uint value;
    uint8_t padding[IPC_CACHELINE_MAX - sizeof(atomic_uint)];
};

struct ipc_ring {
    struct ring_index producer;
    struct ring_index consumer;
    _Alignas(IPC_CACHELINE_MAX) uint32_t slots[64];
};

_Static_assert(sizeof(struct ring_index) == IPC_CACHELINE_MAX,
               "ring index must occupy one maintenance unit");
```

实际工程还要检查编译后的 `offsetof`、结构总尺寸和链接地址。对齐只解决行共享问题，不替代 Release/Acquire 或 Non-coherent Cache 维护。

## 4. Non-coherent 系统

C11 原子并不会替软件完成 Cache Clean/Invalidate。对于不一致的异构核：

```text
写 Slot
→ Clean Slot Cache Line
→ 完成屏障
→ 写 Head
→ Clean Head Cache Line
→ Doorbell
```

Consumer 必须在读取 Head/Slot 前按平台规则 Invalidate。为了避免双方维护同一行，`head`、`tail` 和 Slot Array 应分别对齐到共享系统要求的最大维护粒度。

## 5. MPSC/MPMC 为什么更难

多个 Producer 不能同时普通写 `head`。常见方案包括：

- CAS 抢占 Reservation Ticket；
- 每个 Slot 单独维护 Sequence Number；
- 每 Producer 私有 Ring，Consumer 轮询合并；
- 加锁保护提交路径；
- 硬件 Queue Manager 分配 Entry。

“无锁”不等于“更快”。在高争用下，CAS 会造成 Cache Line 迁移；每核私有队列往往比全局 MPMC Ring 更稳定。

## 6. Descriptor 生命周期

一个描述符不能只用 `valid` 布尔值描述全部状态。推荐显式状态：

```text
FREE → RESERVED → READY → PROCESSING → COMPLETE → FREE
```

需要考虑：

- Producer 写到一半崩溃；
- Consumer 超时后 Producer 又迟到；
- Ring Reset 与旧 Completion 并发；
- 16/32 位 Index 回绕；
- 描述符复用导致 ABA；
- Payload 先释放、Remote 仍在 DMA。

使用单调 Generation/Cookie 可以区分同一 Slot 的不同生命周期。回收前必须确认 Remote 和 DMA 都已停止访问。

## 7. ABA 与 Sequence Number

若一个 Slot 从 `FREE → READY → FREE` 恰好恢复为旧值，观察者只比较状态可能无法判断它是否经历过一次完整循环。可以把 Index 与 Generation 组合：

```c
struct slot_state {
    uint32_t sequence;
    uint32_t owner;
};
```

Consumer 只接受与预期 Sequence 相等的 Slot。Sequence 必须定义回绕宽度和比较规则，不能假设计数器永不溢出。

### 跨 32/64 位参与者的撕裂访问

32 位 Remote 写一个 64 位字段时，编译器或总线可能把它拆成两次 32 位传输；64 位 Host 若在中间读取，就可能得到“新低位与旧高位”的组合。是否原子取决于处理器指令、对齐、内存类型和互联能力，不能仅根据 AXI 数据总线宽度判断。

跨核 ABI 的稳妥做法是优先传递 Buffer ID 或可覆盖共享区的固定宽度 Offset。确实需要 64 位值时，可以用 Sequence Lock 检测撕裂：

以下是协议伪代码；`READ_ONCE`、`WRITE_ONCE` 和屏障必须替换为目标 OS/BSP 提供的原语：

```c
struct shared_u64 {
    uint32_t seq;
    uint32_t low;
    uint32_t high;
};

/* Writer：seq 奇数表示更新中，偶数表示稳定。每次发布均需平台屏障。 */
seq = READ_ONCE(value->seq);
WRITE_ONCE(value->seq, seq + 1U);
ipc_write_barrier();
WRITE_ONCE(value->low, low);
WRITE_ONCE(value->high, high);
ipc_write_barrier();
WRITE_ONCE(value->seq, seq + 2U);
```

Reader 读取 `seq1 → low/high → seq2`；只有两次 Sequence 相等且为偶数时结果才有效，否则重试。Sequence 本身必须是双方都能原子访问的宽度，并配套 Acquire/Release 或相应平台屏障。若等待必须有界，使用锁、Mailbox 仲裁或双缓冲通常更容易验证。

## 8. Barrier 选择错误

- CPU SMP 队列使用语言原子或内核 `smp_*` 原语；
- DMA/外设队列使用 DMA API 和 `dma_wmb()/dma_rmb()`；
- MMIO Doorbell 使用平台 I/O Accessor，例如 Linux `writel()`；
- Non-coherent Remote 还需要 BSP Cache 维护；
- 不要通过到处添加最强 `DSB SY` 掩盖协议不清晰，它会降低性能，也未必修复所有权错误。

## 9. 可观测性

Ring 至少应暴露：

- Producer/Consumer Index；
- Peak Occupancy；
- Full/Empty 次数；
- Doorbell 次数与合并比；
- Drop、Timeout、Bad Length、Bad Epoch；
- 每个阶段时间戳；
- 最近 N 条状态转换 Trace。

故障快照必须先冻结写入者或使用一致快照协议，否则读取到互相不匹配的 Index 与 Descriptor 会制造假线索。
