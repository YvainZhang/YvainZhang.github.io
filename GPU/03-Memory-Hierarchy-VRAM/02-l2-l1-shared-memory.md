# 02 L2 Cache 切片与 Unified Shared Memory / L1

## 1. 存储层次结构与访问延迟/带宽

```text
[ 寄存器堆 Register File ] : ~0.5 cycle 延迟 | >100 TB/s 片上带宽
       ↓
[ L1 Cache / Shared Memory (SRAM) ] : ~15 cycles 延迟 | ~50 TB/s 带宽
       ↓
[ 全局共享 L2 Cache (SRAM 切片) ] : ~150 cycles 延迟 | ~15 TB/s 带宽
       ↓
[ HBM3e / GDDR7 物理显存 (DRAM) ] : ~300~500 cycles 延迟 | 3.35~8.0 TB/s 带宽
```

---

## 2. 统一 L1 Data Cache 与 Shared Memory (SRAM)

现代 GPU 的 SM 采用统一的 SRAM 物理阵列（如单个 SM 配置 256KB SRAM）：
- **可动态配置比例**：软件可通过驱动或 API 将 SRAM 划分为不同比例（例如：160KB Shared Memory + 96KB L1 Cache，或 228KB Shared Memory + 28KB L1 Cache）。
- **Shared Memory 特性**：
  - 由程序员显式控制与分配（Software-Managed Scratchpad）。
  - 同一个 Thread Block 内的所有线程共享访问，用于实现高效的跨线程数据交换与复用。
- **L1 Cache 特性**：
  - 硬件自动缓存 Global Memory 与 Local Memory 的读写请求，对软件透明。
