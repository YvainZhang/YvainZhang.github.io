# SMMUv3 嵌套翻译、PCIe ATS、PRI 与共享虚拟寻址（SVA）深度解析

## 1. SMMUv3 两级流表与上下文描述符（CD）硬件查找架构

在系统级 IOMMU（ARM SMMUv3）中，外设发起的每一个 DMA 事务都携带 **StreamID（标识具体物理外设，通常由 PCIe RequesterID/BDF 派生）** 与可选的 **PASID（Process Address Space ID，标识进程）**。

```mermaid
flowchart TD
    DMA_Tx["外设发起 DMA 事务: StreamID + PASID + IOVA/VA"] --> ST_Lookup["SMMU 查流表: Stream Table (线性表或 2 级树状表)"]

    ST_Lookup --> STE["选中 Stream Table Entry (STE)"]

    subgraph STE_Config ["STE 配置模式判定 (STE.Config)"]
        STE -->|Config == 0b000| Bypass["Bypass: 物理地址直通 (不翻译)"]
        STE -->|Config == 0b100| S1_Only["Stage-1 Only: 主机普通 OS DMA 翻译"]
        STE -->|Config == 0b110| S2_Only["Stage-2 Only: 虚拟机传统设备直通"]
        STE -->|Config == 0b101| Nested["Nested (Stage-1 + Stage-2): 虚拟机 SVA 共享地址"]
    end

    STE -->|S1ContextPtr| CD_Table["Context Descriptor (CD) 表 (由 PASID 索引)"]
    CD_Table --> CD["选中 Context Descriptor (CD)"]

    CD -->|CD.TTBR0| S1_PT["Stage-1 页表: VA/IOVA → 中间物理地址 IPA"]
    STE -->|STE.S2TTB| S2_PT["Stage-2 页表: IPA → 最终宿主机物理地址 PA"]

    S1_PT & S2_PT --> Final_PA["输出合法 PA 发送至 NoC / DDR"]
```

---

## 2. 虚拟机直通两阶段嵌套翻译（Nested Translation）的硬件开销

在云计算虚拟化场景下（KVM / VFIO），当虚拟机内部运行的 Guest OS 试图让直通网卡直接使用用户进程虚拟地址（VA）时，SMMU 必须进行 **Stage-1（Guest 虚拟化）与 Stage-2（Hypervisor 隔离）的嵌套翻译**：

```mermaid
sequenceDiagram
    participant Dev as PCIe Endpoint (网卡/GPU)
    participant SMMU as SMMUv3 硬件翻译引擎
    participant GuestPT as Guest Stage-1 页表 (GPA/IPA 视图)
    participant HostPT as Host Stage-2 页表 (PA 视图)
    participant Memory as 真实 Host DDR 物理内存

    Dev->>SMMU: 发起 DMA 读写请求: GVA (Guest 虚拟地址)
    Note over SMMU: 阶段 1 走表: 查询 Guest L0~L3 页表
    SMMU->>HostPT: 读取 Guest L0 页表基地址 (其本身为 IPA, 需经 Stage-2 翻译)
    HostPT-->>SMMU: 返回 Guest L0 页表所在 Host PA
    SMMU->>Memory: 读取 Guest L0 表项
    Note over SMMU: ... 依次递归 4 级 ...
    Note over SMMU: 阶段 2 走表: 将 Stage-1 输出的 IPA 翻译为最终 PA
    SMMU->>HostPT: 翻译目标数据页 IPA → PA
    HostPT-->>SMMU: 返回最终数据 Host PA
    SMMU->>Memory: 执行真实 DMA 数据搬运
```

- **二维走表放大效应**：若未命中 TLB，一次完整的 4 级 Stage-1 + 4 级 Stage-2 走表，**硬件需要访问外部总线高达 $(4+1) \times (4+1) - 1 = 24$ 次！**
- **性能救星——IOTLB 与 Walk Cache**：SMMUv3 内部深度集成了 **Walk Cache**（缓存中间 Stage-2 转换条目），将平均走表内存访问次数压减至 2~3 次。

---

## 3. PCIe ATS（地址翻译服务）与 Device-TLB 硬件协议

为了彻底卸载 SMMU 的翻译压力，PCIe 规范定义了 **ATS（Address Translation Services）**，允许高性能外设（如 NVMe 控制器、高端 GPU）在本地集成 **Device-TLB**：

```mermaid
flowchart LR
    subgraph PCIe_Endpoint ["PCIe 外设 (集成 Device-TLB)"]
        Req_Gen["DMA 引擎准备发起 4KB 传输"]
        Dev_TLB{"本地 Device-TLB"}
        Req_Gen --> Dev_TLB
        Dev_TLB -->|Hit 命中| Fast_DMA["以 AT=1 (Translated) 标记直接发送带 PA 的 Memory Write TLP"]
    end

    subgraph Host_Root_Complex ["Host 侧 SMMUv3"]
        Dev_TLB -->|Miss 缺失| ATS_Req["发送 ATS Translation Request TLP (带 IOVA/VA)"]
        ATS_Req --> SMMU_Walk["SMMU 查表翻译"]
        SMMU_Walk --> ATS_Cpl["返回 ATS Translation Completion TLP (带 PA & 权限)"]
        ATS_Cpl --> Dev_TLB

        Fast_DMA --> Check_Attr["SMMU 仅校验安全属性, 零延迟放行至 DDR"]
    end
```

### ATS Invalidation 协议与失联死锁
- 当操作系统解除了某个页表映射时，必须向 PCIe 设备广播 **ATS Invalidation Request TLP**。
- 设备在清除本地 Device-TLB 后必须回复 **ATS Invalidation Completion TLP**。
- **关键陷阱与风险**：若 PCIe 设备由于固件跑飞未在规定超时时间（通常 $10\text{ms} \sim 1\text{s}$）内回复 Completion，SMMU 会触发关键 **ATS Timeout 异常**，拉死相关总线。

---

## 4. 共享虚拟寻址（SVA）与 PRI（Page Request Interface）缺页握手

在传统 DMA 中，用户空间指针必须先通过 `pin_user_pages()` 锁死在物理内存中并由驱动建立 IOVA 映射。**SVA（Shared Virtual Addressing）彻底打破了这道墙**：

```mermaid
sequenceDiagram
    participant App as 用户态应用程序
    participant Acc as 硬件加速器 (NPU / GPU)
    participant PRI as SMMUv3 PRI 队列
    participant OS as Linux 缺页处理 (handle_mm_fault)

    App->>Acc: 将用户态 malloc 指针直接写入加速器队列 (无需驱动介入)
    Acc->>Acc: 访问该 VA, 本地与 SMMU 查表均发现 PTE.Valid == 0
    Acc->>PRI: 发送 PCIe Page Request TLP (请求分配内存页)
    PRI->>OS: SMMU 触发 PRI 中断, 将请求推入 PRI Queue
    OS->>OS: 内核执行标准 do_page_fault(), 分配物理页并更新进程页表
    OS->>PRI: 向 SMMU CMDQ 写入 PRI_RESP 命令 (Response Code: SUCCESS)
    PRI->>Acc: 发送 PCIe Page Response TLP
    Acc->>Acc: 重新执行 DMA 访存, 成功读取数据!
```

---

## 5. SMMUv3 三大硬件环形队列管理与命令

SMMUv3 与驱动软件完全通过内存中的 3 个**环形缓冲区（Ring Buffers）**解耦通信：

```mermaid
flowchart TD
    subgraph SMMU_Queues ["SMMUv3 三大物理队列"]
        CMDQ["1. Command Queue (CMDQ: CPU写, SMMU读)\n下发配置同步与 TLB 失效命令\n(CMD_CFGI_STE, CMD_TLBI_NH_VA, CMD_SYNC)"]
        EVENTQ["2. Event Queue (EVENTQ: SMMU写, CPU读)\n硬件上报翻译错误、权限违例与安全阻断\n(F_TRANSLATION, F_PERMISSION, F_ADDR_SIZE)"]
        PRIQ["3. PRI Queue (PRIQ: SMMU写, CPU读)\n接收 PCIe 设备发来的缺页请求并在处理后应答"]
    end
```

---

## 6. 常见关键直通陷阱与排查手册

### 陷阱 1：VFIO 直通网卡触发 `F_PERMISSION` 导致网卡死锁
- **故障现象**：在 KVM 虚拟机中将物理网卡通过 VFIO 直通给虚拟机，驱动加载时网卡直接超时，宿主机 `dmesg` 疯狂报错：`arm-smmu-v3: event 0x07: F_PERMISSION for StreamID 0x1800, IOVA 0x82000000`。
- **微架构根因**：
  - Event `0x07` 为 **Permission Fault**。
  - KVM 在初始化该直通设备的 Stage-2 映射时，错误地将 DMA 描述符环形缓冲区所在的内存页映射为了 **只读（`IOMMU_READ`）**。
  - 网卡在接收到网络数据包后，DMA 试图将写回状态（Descriptor Status）写入该物理页，触发 SMMU 权限阻断，DMA 事务被丢弃。
- **排查法则**：检查 VFIO 分配映射时的标志位，确保包含 `IOMMU_WRITE` 读写双向权限。

### 陷阱 2：DMA 寻址超出硬件 DMA Mask
- **故障现象**：设备在某些 64GB 内存服务器上运行正常，在 512GB 内存服务器上随机触发 `F_ADDR_SIZE` 错误。
- **根因**：
  - 设备硬件只支持 32 位或 36 位 DMA 寻址能力，但驱动未调用 `dma_set_mask_and_coherent(dev, DMA_BIT_MASK(36))` 显式声明；
  - 操作系统给设备分配了超出 36 位物理边界（`> 64GB`）的高位物理页，STE 检测到地址越界直接抛出 `F_ADDR_SIZE` 严重异常事件。
