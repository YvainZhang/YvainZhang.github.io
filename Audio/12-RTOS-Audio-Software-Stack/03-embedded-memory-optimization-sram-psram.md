# 03 极限内存受限优化与 SRAM/PSRAM 异构调度

## 1. 为什么要做极端内存优化：AIoT 芯片的生存红线

以片内 SRAM 为 **256KB ~ 512KB** 的 MCU 为例，音频、网络和应用需要共享内存。下面列出几类占用，具体大小取决于功能和缓冲配置：
* **WiFi 6 / BLE 协议栈**：通常需独占 120KB ~ 180KB（用于网络收发 Descriptor 环、TCP 滑窗缓冲与 lwIP pbuf）。
* **RTOS 基础内核与系统任务栈**：WiFi 任务、系统管理任务、Shell 调试任务等需消耗 30KB ~ 50KB。
* **应用层业务逻辑与网络连接**：TLS/mbedTLS 握手临时 buffer（高达 30KB+）。

若项目留给音频子系统的 RAM 预算为 **50KB 以内**，就需要分别检查输入、解码工作区、输出缓冲和任务栈。

评估 `libmad`、`Helix MP3` 或 `fdk-aac` 等库时，可以先检查这些配置和数据结构：
* 习惯性一次性申请 **32KB ~ 64KB** 的输入读取缓冲（Input Buffer）；
* 内部维护庞大的静态全局解码表（Huffman 表、反量化表、ID3 标签解析结构体）；
* 若特定构建的堆栈总开销达到 **100KB ~ 150KB**，需要检查它是否超过项目预算，并确保所有分配失败路径都能返回错误。

---

## 2. 优化前后架构对比与 50KB 达成路径

```mermaid
graph TD
    subgraph Before["优化前: 开源库标准架构 (开销 > 120KB)"]
        A1[大块静态 Input Buffer: 32KB]
        A2[Layer I/II/III 全量解码表: 24KB]
        A3[全量 ID3v2 标签元数据缓冲: 16KB]
        A4[全量 PCM 输出乒乓缓冲: 16KB]
        A5[解码任务栈: 16KB]
        A6[动态堆碎片与中间结构: 20KB+]
    end

    subgraph After["优化后: 极致裁剪与分层架构 (总开销 < 50KB)"]
        B1[微型流式输入 RingBuffer: 2KB]
        B2["Layer III 专用精简表: 6KB (固化 Flash/SRAM)"]
        B3["ID3 头部流式跳过 (零元数据驻留)"]
        B4[Direct-to-DMA 输出零拷贝: 0KB]
        B5[精简任务栈: 4KB]
        B6[SRAM / PSRAM 异构堆调度]
    end

    Before -->|三维优化手段| After
```

---

## 3. 核心优化手段：三大重构策略

### 3.1 策略一：流式解码（Streaming Decode）重构输入流控
* **传统模式缺陷**：解码器要求预先读入一整段乃至数个完整的物理帧才开始解析，甚至在内部开辟双缓冲做帧同步，造成内存极大浪费。
* **流式解码重构**：
  * 重写解码器的底层输入接口，与外部 SPSC 环形缓冲深度协同。
  * 解码器不再持有独立的 32KB 大输入缓冲区，仅保留一个 **2KB 的滑动读取窗口**。
  * 按解码器实际消费量推进输入，保留未消费数据。若从原来的大缓冲改为小窗口后测得开销下降 **90%**，还要验证跨帧、重同步和位库依赖是否完整。

### 3.2 策略二：代码与数据结构深度裁剪（Structure Pruning）
* **按格式裁剪**：若产品输入只包含 MPEG-1/2 Audio Layer III，可以评估删除 Layer I/II 支持。不能以“99.9%”作为未检查音源的依据；文中 **18KB** 的节省量也只适用于相应库版本与构建配置。
* **剔除元数据解析（ID3v2 Stripping）**：开源库通常开辟大块内存存储专辑封面（JPEG/PNG）、歌词与艺术家字符串。在嵌入式轻量级播放器中，重写解封装状态机，在检测到 `ID3` 标头（10 字节头中的 `size` 字段）后，直接通过文件指针 `seek` 或环形缓冲跳过整个标签体，**元数据内存开销直接归零**。

### 3.3 策略三：片内 SRAM 与片外 PSRAM 异构调度（Linker Script 编排）
现代 RISC-V AIoT 芯片通常配备片内高速 SRAM 和通过 QSPI/OPI 总线外挂的低成本 PSRAM：

| 存储介质 | 物理带宽与访问延迟 | 典型容量 | 适用数据类型 |
| :--- | :--- | :--- | :--- |
| **片内 SRAM** | 零等待周期（0 Wait-state），主频 320MHz | 256KB ~ 512KB | 极高频访问：霍夫曼表、IMDCT 临时运算缓冲、DMA 描述符、中断栈 |
| **片外 PSRAM** | 高延迟（100ns 随机访问），QSPI 80MHz | 4MB ~ 8MB | 偶发访问：播放器状态机、HTTP TCP 接收缓冲、长时延网络 Jitter Buffer |

解码表放在 PSRAM 后，应测量 Cache Miss 与单帧耗时。即使某次测试观察到 **300%** 的耗时增长，也不能直接推及所有平台；全部放入 SRAM 则需要核对剩余容量。可按访问频率和实时期限分配位置。

---

## 4. 四流全链路分析：SRAM/PSRAM 异构内存访问流

```mermaid
sequenceDiagram
    autonumber
    participant Net as 网络流 (lwIP)
    participant PSRAM as 片外 PSRAM (4MB)
    participant SRAM as 片内高速 SRAM (256KB)
    participant CPU as RISC-V CPU (Pipeline)
    participant DMA as Audio DMA

    Net->>PSRAM: 网络接收大容量 Jitter Buffer (128KB 抵御 WiFi 抖动)
    Note over PSRAM: 存放在 PSRAM 堆中 (psram_malloc)

    CPU->>PSRAM: 提取 2KB 压缩数据流至微型解码窗口
    loop 每 1152 采样点解码循环
        CPU->>SRAM: 极高频查阅定点霍夫曼解码表 (.sram.rodata)
        CPU->>SRAM: 执行 IMDCT 频时反变换，复用片内运算暂存区 (.sram.bss)
    end

    CPU->>SRAM: 解码输出 PCM 样点直接写入 DMA 乒乓环 (.sram.dma)
    DMA->>SRAM: 硬件通过 AXI 零等待总线直接读取 PCM 发送至 I2S
```

---

## 5. 软硬件设计约束：链接脚本（Linker Script）与堆管理器定制

### 5.1 链接脚本分区编排实战
在 GCC 链接脚本（`.ld`）中，明确分离 SRAM 与 PSRAM 物理段，并通过段属性（`__attribute__((section(...)))`）精确控制符号落位：

```ld
MEMORY
{
    FLASH (rx)      : ORIGIN = 0x23000000, LENGTH = 4M
    SRAM_TCM (rwx)  : ORIGIN = 0x22010000, LENGTH = 256K
    PSRAM_EXT (rwx) : ORIGIN = 0x50000000, LENGTH = 4M
}

SECTIONS
{
    /* 高速片内 SRAM 数据段 */
    .sram_data :
    {
        . = ALIGN(4);
        __sram_data_start = .;
        *(.sram.data*)
        *libhelix_mp3.a:*(.data*)      /* 将 MP3 核心运行数据强制拉入 SRAM (加载镜像存于 FLASH) */
        __sram_data_end = .;
    } > SRAM_TCM AT> FLASH

    .sram_bss (NOLOAD) :
    {
        . = ALIGN(4);
        *(.sram.bss*)
        *(.sram.imdct_scratchpad*)     /* IMDCT 变换频时工作区 */
    } > SRAM_TCM

    /* 片外大容量 PSRAM 数据段 */
    .psram_section (NOLOAD) :
    {
        . = ALIGN(32);
        *(.psram.bss*)
        *(.psram.net_buffer*)          /* 大容量网络抗抖动队列 */
    } > PSRAM_EXT
}
```

### 5.2 多堆管理器实现（Multi-Heap Allocator）
在 C 运行时中，实现分级内存申请封装：

```c
#include <stdlib.h>
#include "hal_core.h"

/* 申请片内高速 SRAM (空间极小，仅限高频算法与 DMA) */
void *audio_sram_malloc(size_t size) {
    return pvPortMallocSRAM(size);
}

/* 申请片外大容量 PSRAM (空间充裕，用于控制结构体、网络缓冲) */
void *audio_psram_malloc(size_t size) {
    return pvPortMallocPSRAM(size);
}
```

---

## 6. 现场排错与调试清单

| 故障现象 | 现象抓取与定位手法 | 根本原因分析 | 规避与修复方案 |
| :--- | :--- | :--- | :--- |
| **播放特定歌曲时芯片突然 HardFault 崩溃** | 查看崩溃日志 `MTVAL` 寄存器记录的非法访问地址 | 歌曲附带了 300KB 的高清专辑封面 ID3v2 标签，开源库尝试在 SRAM 堆申请相应大 buffer 导致 OOM | 彻底废除全量 ID3 解析，改用流式字节跳过算法，遇到非音频帧直接丢弃 |
| **音频解码严重卡顿，CPU 占用率飙升至 95%** | 使用 Tracealyzer 或性能打点统计解码单帧耗时 | 霍夫曼解码表或 IMDCT 关键查找表被误分配在片外 PSRAM，导致总线访问剧烈等待 | 检查 Map 文件，确保所有解码常数查找表与紧凑中间变量均锁定在 `.sram_data` |
| **DMA 录播产生杂音或数据错乱** | 打印 DMA Buffer 地址，发现 Cache 与内存数据不一致 | DMA 缓冲区位于 PSRAM 且启用了 D-Cache，但驱动未在传输前后执行 Cache 清理 | DMA 缓冲首选置于不经过 Cache 的 SRAM 区域，若在 PSRAM 则必须调用 `csi_dcache_clean_invalid_range` |
| **长时间运行后出现系统死机** | 打印 Heap 剩余空间走势图，发现内存碎片化严重 | 播放器频繁创建/销毁不同码率解码器，反复在共享堆中 malloc/free 不同大小块 | 对解码器核心 Context 与工作区采用**静态预分配（Static Pool）**或定长内存池管理 |

---

## 7. 实验数据验证：优化前后内存开销对比实测

在某 RISC-V MCU 平台（160MHz 主频，搭载 FreeRTOS）上，对 128kbps/44.1kHz MP3 文件播放进行全量内存开销对比实测：

| 内存分类项 | 优化前 (原始开源 Helix 库) | 优化后 (流式解码 + 裁剪 + 异构调度) | 优化成果 |
| :--- | :--- | :--- | :--- |
| **输入缓冲 (Input Buffer)** | 32,768 字节 (32KB) | 2,048 字节 (2KB) | **缩减 93.7%** |
| **输出缓冲 (PCM Buffer)** | 16,384 字节 (16KB) | 0 字节 (Direct-to-DMA) | **消除 100% 独立缓冲** |
| **解码器结构体 (Context)** | 28,400 字节 | 14,200 字节 (剔除 Layer I/II) | **缩减 50.0%** |
| **任务栈 (Task Stack)** | 16,384 字节 (16KB) | 4,096 字节 (4KB) | **缩减 75.0%** |
| **查找表在 SRAM 占用** | 22,000 字节 | 6,800 字节 (精简表锁 SRAM) | **释放 15.2KB 高速 SRAM** |
| **总计 RAM 动态开销** | **115.9 KB** | **27.1 KB (SRAM) + 18.2KB (PSRAM)** | **总内存压减至 45.3KB (SRAM 降幅达 76.6%)** |

> 这组结果记录了音频运行时占用降至 50KB 以内，以及为 WiFi 6 保留超过 160KB 缓冲空间的配置。复现时需同时记录库版本、编译选项、内存统计口径和并发流量；内存余量增加仍需配合长时间播放、弱网和切换测试检查稳定性。
