# 04 Cache 一致性协议与硬件原子操作

## 1. GPU Cache 一致性模型

与 CPU 复杂昂贵的硬件监听一致性协议（如全互联 MESI/MOESI）不同，GPU 拥有数万并发线程，硬件监听开销无法承受：
- **L1 Cache 非一致性策略**：各个 SM 的 L1 Data Cache 默认**不对其他 SM 保持实时硬件 Snoop 一致性**。
- **L2 Cache 作为全芯片一致性锚点点（Point of Coherence）**：所有跨 SM 的同步与全局共享数据，必须穿透（Write-Through / Bypass L1）或通过显式 Cache Flush / Invalidation 指令同步至全局统一 L2 Cache。

---

## 2. 硬件原子操作 (Atomic RMW) 电路实现

- **Shared Memory 原子操作**：在 SM 内部的 Shared Memory Controller 硬件 ALU 直接执行，单周期即可完成。
- **L2 Cache 全局原子操作**：现代 GPU 将原子操作执行单元（Atomic ALU）直接下沉至 **L2 Cache Slice 内部**。当 SM 发出 `atomicAdd(&g_val, 1)` 时，SM 仅通过 NoC 发送一个轻量级原子操作请求包，L2 控制器在 SRAM 端直接完成 Read-Modify-Write，无需将整条 Cache Line 搬回 SM，大幅削减 NoC 总线拥塞。
