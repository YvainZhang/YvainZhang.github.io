# eMMC、UFS 与 NVMe：接口、队列和性能对比 {#emmc-51ufs-3140-nvme}

## 1. 三种存储协议的主要差异

管理型存储（Managed Flash）在物理颗粒外部封装了专用的硬件控制器（Controller），负责固件级磨损均衡（Wear Leveling）、坏块替换、垃圾回收（GC）以及纠错（ECC）。在嵌入式、移动终端与高性能计算领域，主要分为 **eMMC、UFS 与 NVMe** 三大阵营：

```mermaid
flowchart TD
    subgraph Storage_Evolution ["存储协议架构演进"]
        eMMC["1. eMMC 5.1 (Legacy Embedded)\n• 8-bit 并行总线, 半双工 (Half-Duplex)\n• 峰值带宽 ~400 MB/s, 软件栈路径较深"]
        UFS["2. UFS 3.1 / 4.0 (Mobile Flagship)\n• M-PHY 差分串行, 全双工 (Full-Duplex)\n• 峰值带宽 2.9 ~ 5.8 GB/s, 基于 SCSI 协议栈"]
        NVMe["3. NVMe over PCIe (High-End & Server)\n• PCIe SerDes 差分链路, 多队列软件栈\n• 带宽取决于 PCIe 代际与 Lane 数"]
    end

    eMMC -->|串行化与全双工升级| UFS
    UFS -->|使用 PCIe 与 NVMe 多队列模型| NVMe
```

### 接口与性能参数对比
| 参数维度 | eMMC 5.1 | UFS 3.1 / 4.0 | NVMe 1.4 / 2.0 (PCIe 4.0 x4) |
| :--- | :--- | :--- | :--- |
| **物理接口** | 8-bit 并行数据线 + CMD + CLK | M-PHY 差分对（2-Lane 全双工） | PCIe Gen4 SerDes（4-Lane 全双工） |
| **双工机制** | **半双工**（读写无法同时进行） | **全双工**（读写独立物理通道） | **全双工**（读写独立通道） |
| **最大理论带宽** | 400 MB/s (HS400) | 2900 MB/s (UFS 3.1) / 5800 MB/s (UFS 4.0) | 7880 MB/s (PCIe 4.0 x4) |
| **软件驱动模型** | Linux MMC 子系统 | Linux SCSI / UFS 子系统 | 专用 **`blk-mq` NVMe 驱动（直通内核）** |
| **硬件队列结构** | 单队列 CQE（Command Queue Engine, 深度 32） | 单请求列表 UTRL（最多 32 个 UTRD 任务） | **多达 64K 个独立队列对（SQ/CQ）**，每个队列深度可达 64K |
| **多核扩展性** | 取决于 Host 控制器和驱动锁粒度 | 取决于请求队列与 Host 控制器实现 | 多队列有助于减少共享竞争，仍需核对队列映射与锁开销 |
| **典型 4K 随机读 IOPS** | 15K ~ 30K IOPS | 100K ~ 400K IOPS | 500K ~ 1000K+ IOPS |
| **典型访问延迟** | 100 ~ 200 $\mu\text{s}$ | 30 ~ 60 $\mu\text{s}$ | 8 ~ 20 $\mu\text{s}$ |

表中的 IOPS 与延迟范围用于说明量级，不能作为接口规范的保证值。比较具体设备时，还要记录容量、读写比例、队列深度、数据块大小、缓存和温度条件。

---

## 2. 软件驱动栈路径与队列投递机制对比

NVMe 使用独立的命令集和多队列模型，Linux 可通过 `blk-mq` 把请求分配到多个硬件队列，减少部分共享队列竞争。队列数及 CPU 映射取决于设备和驱动配置，实际性能还受到 PCIe 带宽、闪存介质、固件和负载影响。下图是简化示意，各驱动的队列映射需结合实现查看。参见 [Linux blk-mq 文档](https://docs.kernel.org/block/blk-mq.html)。

```mermaid
flowchart TD
    subgraph eMMC_UFS_Stack ["eMMC / UFS 软件栈 (简化示意)"]
        User1["用户空间 I/O 请求"] --> VFS1["VFS / Page Cache"]
        VFS1 --> Block1["Block Layer (通用块设备层)"]
        Block1 --> SCSI1["SCSI 中间适配层 (UFS 需要)"]
        SCSI1 --> Controller1["Host 控制器 (检查队列与锁粒度)"]
        Controller1 --> HW1["单个硬件命令队列 (深度 <= 32)"]
    end

    subgraph NVMe_Direct_Stack ["NVMe 多队列软件栈 (blk-mq)"]
        User2["用户空间 I/O 请求"] --> VFS2["VFS / Page Cache"]
        VFS2 --> BlkMQ["blk-mq 多硬件队列抽象"]
        BlkMQ --> Core0_SQ["Submission Queue 0"]
        BlkMQ --> Core1_SQ["Submission Queue 1"]
        BlkMQ --> CoreN_SQ["Submission Queue N"]
        Core0_SQ --> NVMe_HW["NVMe 控制器 (PCIe DMA 并行处理各核队列)"]
        Core1_SQ --> NVMe_HW
        CoreN_SQ --> NVMe_HW
    end
```

---

## 3. 掉电安全性（Power Loss Protection, PLP）与 Flush / FUA 语义

管理型存储设备通常包含两级存储介质：
1. **易失性缓存（Volatile Cache）**：控制器内部的高速 SRAM 或板载 LPDDR，用于写合并、地址映射表缓存与低延迟响应；
2. **非易失性介质（Non-Volatile NAND Flash）**：实际存储数据的物理颗粒。

```mermaid
sequenceDiagram
    participant OS as 操作系统 (文件系统 EXT4/XFS)
    participant Dev_RAM as 存储设备易失缓存 (DRAM Cache)
    participant Flash as 物理 NAND Flash 颗粒

    Note over OS,Dev_RAM: 1. 普通写操作 (Write Command)
    OS->>Dev_RAM: 传输数据与写请求
    Dev_RAM-->>OS: 数据进入 DRAM 即立即回复 Completion (快速响应)
    Note over Dev_RAM,Flash: 此时若突发掉电，DRAM 中的数据将永久丢失!

    Note over OS,Flash: 2. 关键元数据持久化 (Flush 语义)
    OS->>Dev_RAM: 发送 SYNCHRONIZE_CACHE (UFS) 或 FLUSH (NVMe)
    Dev_RAM->>Flash: 存储控制器强制将 DRAM 中的全部脏数据刷入 NAND
    Flash-->>Dev_RAM: NAND 编程完成
    Dev_RAM-->>OS: 回复 Flush 成功 (先前完成的写入已持久化)

    Note over OS,Flash: 3. 强制单元访问 (FUA: Force Unit Access)
    OS->>Flash: 发送带 FUA 标记的写请求 (要求完成前持久化)
    Flash-->>OS: 数据进入非易失性介质后才回复完成
```

这里假设设备和驱动正确实现了 Flush / FUA 语义。FUA 要求该请求完成前持久化，并不规定数据必须绕过 DRAM；它也不等于整个文件系统的更新已经具有原子性。参见 [Linux 写回缓存控制文档](https://docs.kernel.org/block/writeback_cache_control.html)。

### 工业级与企业级 PLP 硬件设计
- **无掉电保护设备（消费级 eMMC / 消费级 NVMe）**：突发断电时，DRAM 缓存中未刷盘的脏数据与 FTL 映射表完全丢失，可能导致**文件系统元数据损坏、出现 0 字节文件甚至固件死锁变砖**。
- **带硬件 PLP 设备（车载 / 工业级存储）**：PCB 配备**钽电容阵列**。当供电电压跌落触发掉电中断时，电容放电提供 $5\sim 20\text{ms}$ 的后备电力，控制器在此期间强制将易失缓存与最新 FTL 映射表完整固化到 SLC 缓存区。

---

## 4. 存储调优工程实践：队列深度（Queue Depth）与读写混合瓶颈

### 队列深度与吞吐/延迟的权衡法则
- **低队列深度（QD=1 ~ 4）**：适用于响应速度敏感的交互型业务（如 UI 渲染、数据库行锁同步读）。此时关注**单次 I/O 延迟（Service Time）**，增大 QD 不会提高性能，反而增加排队等待时间。
- **高队列深度（QD=32 ~ 128）**：适用于流式大文件传输与后台批量吞吐任务。此时高 QD 能够充分发挥 NAND 控制器的多通道（Multi-Channel）与多 Die 交织并行度（Die Interleaving），掩盖单颗粒的擦写延迟，跑满总线物理带宽。

### 读写混合场景下的“写阻塞读”现象
- **物理机制**：NAND Flash 的读取仅需 $25\sim 50\mu\text{s}$，但块擦除（Erase）需要 $2\sim 5\text{ms}$，页编程（Program）需要 $500\sim 1500\mu\text{s}$。
- **现象**：当系统后台存在高负载连续写时，偶发的一个小文件读取请求若被排在同一个 NAND Die 的擦除操作之后，读取延迟会从数十微秒瞬间飙升至数毫秒（**长尾延迟毛刺**）。
- **规避方案**：在 UFS/NVMe 中开启 **Erase/Program Suspend** 机制（允许高优先级的读取请求打断正在进行的擦除/编程操作）。
