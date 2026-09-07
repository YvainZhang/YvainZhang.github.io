# 03 Host-Device 异构交互边界与 PCIe/AXI 接口

## 1. 异构系统接口拓扑

- **端侧 SoC NPU**：通过片上 AMBA AXI5 / NoC 总线直接挂载在主系统总线上，与 CPU/ISP 共享统一 LPDDR 物理内存。
- **云端 PCIe NPU**：作为 PCIe Gen5/Gen6 独立扩展卡插入服务器，拥有独立的板载 HBM3 / GDDR6 显存。

```mermaid
sequenceDiagram
    autonumber
    participant CPU as Host CPU (Runtime)
    participant BAR as NPU BAR0 MMIO
    participant TQ as 片上 Task Queue (SRAM)
    participant NPU_Core as NPU 硬件调度引擎

    CPU->>BAR: 分配并写入 Task Descriptor (模型图参数、输入输出物理地址)
    CPU->>BAR: 写入 Doorbell 寄存器触发 NPU
    NPU_Core->>TQ: 抓取 Task Descriptor 并译码
    Note over NPU_Core: 启动 Tensor DMA 搬运与脉动阵列计算
    NPU_Core-->>CPU: 计算完成，发出 MSI-X 中断或写回 Completion Flag
```
