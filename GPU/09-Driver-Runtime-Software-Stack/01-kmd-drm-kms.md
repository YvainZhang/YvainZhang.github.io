# 01 Linux KMD 内核驱动与 DRM / KMS 架构

## 1. Linux DRM (Direct Rendering Manager) 架构

Linux 内核中的 GPU 驱动标准子系统采用 DRM 架构，主要由两大部分构成：
- **KMS (Kernel Mode Setting)**：负责管理显示输出接口（CRTC、Encoder、Connector、Plane）和屏幕分辨率设置。
- **GEM (Graphics Execution Manager) / TTM**：负责管理 GPU 物理显存与系统内存页面的分配、回收与跨进程共享（dma-buf）。

```mermaid
graph TD
    UserApp["用户空间应用程序 (CUDA / OpenGL / Vulkan)"] --> UMD["用户态驱动 (UMD - libcuda.so / Mesa)"]
    UMD -->|ioctl /dev/dri/card0| DRM_Core["Linux 内核 DRM Core"]
    
    subgraph KMD_Vendor["原厂 KMD 驱动模块 (如 nvidia.ko / amdgpu.ko)"]
        GEM_Mgr["GEM / 显存内存管理器"]
        Scheduler["GPU 任务调度器 (DRM Scheduler)"]
        IRQ_Handler["MSI-X 中断与 Fault 处理函数"]
    end
    
    DRM_Core --> KMD_Vendor
    KMD_Vendor --> Hardware["GPU 物理硬件 (BAR0 MMIO / Doorbell)"]
```
