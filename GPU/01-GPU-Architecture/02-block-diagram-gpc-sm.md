# 02 Block Diagram 与 GPC/TPC/SM 层次拓扑

## 1. 现代高性能 GPU 顶层框图 (Top-Level Block Diagram)

```mermaid
graph TB
    subgraph HostInterface["Host 接口与管理总线"]
        PCIe["PCIe Gen5/Gen6 x16 控制器"]
        NVLink_IF["NVLink4/5 端口控制器 (1.8 TB/s)"]
        HSP["High Speed Port / D2D PHY"]
        PMU_Subsys["PMU 电源管理 / 安全引擎 / JTAG"]
    end

    subgraph CommandProcessor["前端指令与任务调度"]
        GigaThread["GigaThread 硬件任务分派引擎"]
        CmdFIFO["Command FIFO & PushBuffer Ring"]
    end

    subgraph ComputeFabric["GPC 计算集群阵列 (128 SMs)"]
        GPC0["GPC 0 (8 TPCs / 16 SMs)"]
        GPC1["GPC 1 (8 TPCs / 16 SMs)"]
        GPCN["GPC 7 (8 TPCs / 16 SMs)"]
    end

    subgraph InterconnectNetwork["高带宽片上 NoC / Crossbar (50 TB/s)"]
        XBAR["Distributed Crossbar Interconnect & Tile Routing"]
    end

    subgraph MemorySubsystem["显存与缓存子系统"]
        L2_0["L2 Cache Slice 0 (32MB)"]
        L2_1["L2 Cache Slice 1 (32MB)"]
        L2_N["L2 Cache Slice 7 (32MB)"]
        HBM_Ctrl0["HBM3e Controller 0"]
        HBM_Ctrl1["HBM3e Controller 1"]
        HBM_CtrlN["HBM3e Controller 5"]
        HBM_Stack0["HBM3e Stack (24GB)"]
        HBM_Stack1["HBM3e Stack (24GB)"]
    end

    PCIe & NVLink_IF --> CmdFIFO --> GigaThread
    GigaThread --> GPC0 & GPC1 & GPCN
    GPC0 & GPC1 & GPCN <--> XBAR
    XBAR <--> L2_0 & L2_1 & L2_N
    L2_0 <--> HBM_Ctrl0 <--> HBM_Stack0
    L2_1 <--> HBM_Ctrl1 <--> HBM_Stack1
```

---

## 2. GPC、TPC 与 SM 的物理微架构展开

每个 GPC（Graphics Processing Cluster）由独立的时钟树分支和电源门控开关驱动，内部包含若干 TPC（Texture Processing Cluster），而每个 TPC 包含 2 个独立的 **SM（Streaming Multiprocessor）**：

```mermaid
graph LR
    subgraph TPC_Detail["TPC 内部结构"]
        TexUnit["Texture Unit (纹理采样/滤波/解压缩)"]
        SM_A["SM 0"]
        SM_B["SM 1"]
        PolyMorph["PolyMorph Engine / 几何前处理"]
    end
    TexUnit --- SM_A & SM_B
    PolyMorph --- SM_A & SM_B
```

### 单 SM 内部四路处理分区 (Processing Block / Warp Scheduler)

每个 SM 内部被严格切分为 4 个物理对等的 **Sub-Core (Processing Block)**：
- 每个 Sub-Core 拥有独立的 **1 个 Warp 调度器 (Warp Scheduler) + 1 个指令分派单元 (Dispatch Unit)**；
- 独立映射 **16K 个 32-bit 寄存器 (64KB SRAM)**；
- 包含 **16 个 FP32 ALU、16 个 INT32 ALU、4 个 FP64 ALU、1 个 Tensor Core 矩阵乘单元、4 个 SFU 特殊函数单元**；
- 4 个 Sub-Core 共享统一的 **228KB Shared Memory / L1 Data Cache** 与 L1 Instruction Cache。
