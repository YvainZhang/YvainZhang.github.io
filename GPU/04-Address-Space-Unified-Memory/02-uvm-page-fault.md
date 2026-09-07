# 02 统一内存 (UVM) 与硬件 Page Fault 机制

## 1. Unified Virtual Memory (UVM) 原理

统一内存允许 CPU 与 GPU 共享相同的单指针虚拟地址空间（`cudaMallocManaged`）：
- 程序无需显式执行 `cudaMemcpy`。
- 数据可以在 CPU 主存（Host DDR）与 GPU 显存（Device HBM）之间按需动态迁移。

```mermaid
sequenceDiagram
    autonumber
    participant GPU_SM as GPU SM Execution
    participant GPU_MMU as GPU MMU
    participant UVM_KMD as Linux UVM Driver (KMD)
    participant Host_DDR as Host DDR Memory
    participant GPU_HBM as GPU HBM Memory

    GPU_SM->>GPU_MMU: 发起 VA 访存请求
    GPU_MMU-->>GPU_SM: 页表项无效，触发 Hardware Page Fault 中断
    GPU_MMU->>UVM_KMD: 产生 MSI-X 中断，上报 Faulting VA 与 Context ID
    UVM_KMD->>Host_DDR: 锁定源数据页面 (Pin Pages)
    UVM_KMD->>GPU_HBM: 通过 DMA 搬运页面至 GPU 显存
    UVM_KMD->>GPU_MMU: 更新 GPU 页表项，置位 Valid 并 Flush TLB
    UVM_KMD-->>GPU_SM: 恢复 Warp 执行，重试访存成功
```
