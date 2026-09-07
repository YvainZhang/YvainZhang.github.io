# 06 UMD 零系统调用提交延迟定量计算

## 1. 传统系统调用路径 vs 用户态直通提交路径

```mermaid
graph TD
    subgraph TraditionalSyscall["传统系统调用路径 (~2.35 us)"]
        App1["用户态应用"] -->|ioctl 系统调用| Kernel1["内核态 DRM 驱动"]
        Kernel1 -->|参数校验 + 锁竞争| Ring1["写入内核 Ring Buffer"]
        Ring1 -->|MMIO 写| Reg1["写硬件寄存器"]
    end

    subgraph UserModeDoorbell["用户态直通 Doorbell 路径 (~0.35 us)"]
        App2["用户态 UMD (libcuda)"] -->|直接写入 mmap 共享 Ring Buffer| Ring2["用户态映射 Ring Buffer"]
        Ring2 -->|一条 mov 汇编写 BAR0| Reg2["硬件 Doorbell 寄存器"]
    end
```

### 2. 详细耗时拆解与定量推导

| 执行阶段 | 传统 ioctl 提交耗时 | UMD 用户态 Doorbell 提交耗时 | 性能提升幅度 |
| :--- | :--- | :--- | :--- |
| **Command Packet 组包** | 100 ns | 100 ns | 相同 |
| **用户/内核上下文切换** | 850 ns (Trap, 寄存器保存恢复) | **0 ns (无系统调用)** | **$\infty$** |
| **内核互斥锁与参数校验** | 1150 ns (VMA 校验与 Mutex) | **0 ns** | **$\infty$** |
| **MMIO 触发 (PCIe Write)**| 250 ns | 250 ns (用户态直写 BAR0) | 相同 |
| **单次任务下发总时延** | **2350 ns (2.35 $\mu$s)** | **350 ns (0.35 $\mu$s)** | **快 6.7 倍** |
