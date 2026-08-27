# 非一致性 DMA 脏行覆写、环形缓冲区越界与调试实战

## 1. 经典故障：非对齐非一致性 DMA 脏行覆写（Dirty Line Eviction）复盘

```mermaid
sequenceDiagram
    participant CPU as CPU 核心
    participant Cache as L1 D-Cache (64B Cacheline)
    participant RAM as DDR 物理内存
    participant NIC as 网卡 DMA 引擎

    Note over CPU,RAM: Cacheline A (64 字节): 前 32 字节为 CPU 计数器变量, 后 32 字节为网卡接收 Buffer
    CPU->>Cache: 1. CPU 修改本地计数器变量 (Cacheline A 处于 Modified 脏态)
    NIC->>RAM: 2. 网卡收到以太网数据包, DMA 直接写入 DDR 中后 32 字节物理地址
    Note over RAM: DDR 内存已更新为最新的网络数据包!

    Note over CPU,Cache: 3. 内存发生冲突或发生 Cache 替换 (Cacheline Eviction)
    Cache->>RAM: 4. D-Cache 强制将 Cacheline A 的 64 字节整行全量写回 DDR!
    Note over RAM: 数据踩踏发生: D-Cache 中旧的后 32 字节数据写回覆写了网卡刚接收的新数据!
    CPU->>RAM: 5. 驱动读取网络包 -> 报头损坏, 校验和失败丢包!
```

- **微架构根本原因**：Cache 以 **64 字节整行** 为最小读写粒度，而 CPU 写入的数据与 DMA 写入的数据共享了同一条 Cacheline。
- **工业级标准规避**：
  1. 驱动应优先使用标准的 DMA 内存分配接口（如 `dma_alloc_coherent`）或通用分配器，非一致性架构会利用体系结构相关的 `ARCH_DMA_MINALIGN` 保证分配的缓冲区边界独立，避免驱动自行假定 Cacheline 大小；
  2. **所有权隔离原则**：同一个 Cacheline 内严禁混合 CPU 与设备的不同所有权区域，禁止在 DMA 接收缓冲区前后紧挨着定义由 CPU 频繁写入的常规变量（若在结构体内嵌缓冲区，需使用 `____cacheline_aligned` 进行独立行对齐隔离）。

---

## 2. 环形描述符（Ring Buffer）生产者-消费者无锁同步状态机

```mermaid
stateDiagram-v2
    [*] --> Init: 初始化 Ring Buffer (CPU 分配 Head=0, Tail=0)

    Init --> CPU_Producing: CPU 准备发送数据 (填充 Buffer & 描述符)
    CPU_Producing --> Release_Ownership: 执行 dma_wmb(), 将描述符 OWN 标志置 1 (移交所有权)

    Release_Ownership --> DMA_Processing: 敲击外设 Doorbell 寄存器, 外设 DMA 开始取指搬运

    DMA_Processing --> DMA_Done: 外设搬运完毕, DMA 回写描述符 OWN=0 并触发中断

    DMA_Done --> CPU_Consuming: CPU 进入 ISR, 执行 dma_rmb(), 确认 OWN=0
    CPU_Consuming --> Reclaim: 回收描述符并推进 Head 指针
    Reclaim --> CPU_Producing: 循环利用描述符槽位
```

---

## 3. DMA 踩内存（Silent Memory Corruption）硬件定位法

- **现象**：系统运行几小时后，内核调度器链表或页表突然被写坏为特定数据模式（如全 `0x00` 或带有以太网报头特征），CPU 触发 Panic。
- **定位四步法**：
  1. **特征逆向**：观察被踩内存的数据内容。若包含 `0x0800`（IPv4 协议号）或特定 MAC 地址，直接定界为网卡 DMA 越界；
  2. **使能 IOMMU / SMMU Guard Page**：在驱动申请的 DMA 物理页前后各插入一个未映射的虚拟保护页（Guard Page）。当 DMA 发生越界写时，SMMU 硬件瞬间捕获并记录 `Translation Fault` 与触发该事务的 `StreamID`（硬件外设标识）；
  3. **启用 `CONFIG_DMA_API_DEBUG`**：Linux 内核自带 DMA 调试框架，能够自动检查缓冲区未对齐、重复映射、内存越界和未释放泄漏。
