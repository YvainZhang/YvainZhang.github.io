# Lab 02：DMA Cache 所有权错误模拟

普通 QEMU `virt` 与 Host Cache 不能稳定复现真实非一致 DMA 的 Dirty Line 覆盖。本实验用两个显式副本模拟 CPU Cache 与 Device-visible Memory，准确展示 Clean/Invalidate 和 Ownership；它验证软件协议，不声称验证物理 Cache 指令。

```bash
cc -O2 -Wall -Wextra coherency_sim.c -o coherency_sim
./coherency_sim
```

程序先演示 CPU 写后未 Clean，设备读到旧数据；再演示设备写后 CPU 未 Invalidate，CPU 读到旧数据；最后执行正确转移。真实 Linux 驱动应把模拟函数替换为 DMA Mapping API，而不是手写 `memcpy`。

## 模型与所有权转换

```text
CPU 修改 cpu_cache[]
        │
        ├── 未 Clean ────────────> Device 从 memory[] 读到旧数据
        │
        └── Clean for Device ────> cpu_cache[] 复制到 memory[]

Device 修改 memory[]
        │
        ├── 未 Invalidate ───────> CPU 从 cpu_cache[] 读到旧数据
        │
        └── Invalidate for CPU ──> memory[] 复制到 cpu_cache[]
```

这里的两个数组只是教学模型。真实硬件中的 CPU Cache、PoC、互联和 DDR 并不是通过 `memcpy()` 维持一致性。

## 完整源码：`coherency_sim.c`

```c
#include <stdio.h>
#include <string.h>

struct buffer_view { char cpu_cache[64]; char memory[64]; int cpu_valid; };

static void clean_for_device(struct buffer_view *b) { memcpy(b->memory, b->cpu_cache, 64); }
static void invalidate_for_cpu(struct buffer_view *b) { memcpy(b->cpu_cache, b->memory, 64); b->cpu_valid = 1; }

int main(void)
{
    struct buffer_view b = { .cpu_cache = "old", .memory = "old", .cpu_valid = 1 };
    strcpy(b.cpu_cache, "cpu-new");
    printf("missing clean: device sees '%s'\n", b.memory);
    clean_for_device(&b);
    printf("after clean: device sees '%s'\n", b.memory);

    strcpy(b.memory, "device-new");
    printf("missing invalidate: CPU sees '%s'\n", b.cpu_cache);
    invalidate_for_cpu(&b);
    printf("after invalidate: CPU sees '%s'\n", b.cpu_cache);
    return 0;
}
```

预期输出：

```text
missing clean: device sees 'old'
after clean: device sees 'cpu-new'
missing invalidate: CPU sees 'cpu-new'
after invalidate: CPU sees 'device-new'
```

在 Linux 驱动中，应使用 `dma_map_*()`、`dma_sync_*_for_device()`、`dma_sync_*_for_cpu()` 和对应的 Unmap API 表达所有权转换，不能把本实验中的复制函数照搬到驱动。
