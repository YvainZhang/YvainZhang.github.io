# Linux DMA API 与内存屏障

## 三种地址不能混用

CPU Virtual Address 供内核解引用；CPU Physical Address 是处理器物理视图；DMA Address 是设备端使用的地址，可能经过 Offset 或 IOMMU。DMA API 同时处理地址转换、Cache 所有权和平台限制，驱动不能把 `virt_to_phys()` 当成通用 DMA Mapping。

## Coherent Allocation

```c
struct ring *ring;
dma_addr_t ring_dma;

ring = dma_alloc_coherent(dev, sizeof(*ring), &ring_dma, GFP_KERNEL);
if (!ring)
    return -ENOMEM;

/* CPU accesses ring, device is programmed with ring_dma. */
```

它适合 Descriptor、Doorbell Record 等长期共享控制结构。返回内存对双方具有一致可见性，但 CPU 仍可重排字段写入，所以发布 Descriptor 前需要 `dma_wmb()`；“Coherent”不是“所有访问都自动有序”。释放用 `dma_free_coherent()`，Size 和 DMA Address 必须匹配。

## Streaming Mapping

```c
dma_addr_t dma = dma_map_single(dev, buf, len, DMA_TO_DEVICE);
if (dma_mapping_error(dev, dma))
    return -EIO;

/* publish dma to hardware and wait for completion */
dma_unmap_single(dev, dma, len, DMA_TO_DEVICE);
```

`dma_map_single()` 建立设备可用映射，并在非一致平台把 CPU 写同步到设备；Map 后到 Unmap/Sync-for-CPU 前，Buffer 归设备所有，CPU 不应继续访问。`DMA_FROM_DEVICE` 的 Buffer 在交给设备前也可能需要平台规定的准备，完成后 `dma_sync_single_for_cpu()` 才能由 CPU 读。

循环复用 Buffer 时无需每包 Unmap：

```c
dma_sync_single_for_device(dev, dma, len, DMA_FROM_DEVICE);
/* give ownership to device */
...
/* after hardware completion */
dma_sync_single_for_cpu(dev, dma, actual_len, DMA_FROM_DEVICE);
```

再次交给设备前必须执行 for-device。方向、地址和长度要与原 Mapping 一致；只同步实际接收长度是否安全取决于 Cache Line 边界和 DMA API 约定。

## Scatterlist

`dma_map_sg()` 可能把多个相邻物理段合并为较少的 DMA Segment。驱动遍历硬件段时必须使用 `for_each_sg(..., count returned by dma_map_sg)` 的正确模式和 `sg_dma_address/sg_dma_len`，不能继续用原始 `sg_phys`。Unmap 时传入原始 Entry 数，具体 API 契约需严格遵守内核文档。

## 描述符发布顺序

```c
desc->dma_addr = cpu_to_le64(buf_dma);
desc->length   = cpu_to_le16(len);
desc->flags    = cpu_to_le16(flags_without_own);

dma_wmb();                     /* fields visible before ownership */
WRITE_ONCE(desc->flags, cpu_to_le16(flags | OWN));
writel(queue_tail, doorbell);  /* ordered MMIO accessor */
```

设备归还 Ownership 后：

```c
if (!(le16_to_cpu(READ_ONCE(desc->flags)) & OWN)) {
    dma_rmb();                 /* status/length after observing OWN */
    consume(desc->status, desc->length);
}
```

这段代码只表达常见协议。若硬件规定 Doorbell 前需要读回、Descriptor 位于 Streaming Memory 或 Completion 写序不同，应按设备规范调整。

## DMA Mask

驱动在 Probe 时用 `dma_set_mask_and_coherent()` 声明设备可寻址位数。32-bit 设备在无 IOMMU 平台只能取得低地址 Buffer；API 失败必须停止 Probe，不能截断 `dma_addr_t`。Descriptor 中地址字段也应用 `dma_addr_t` 和显式 Endian 转换。
