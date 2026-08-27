# GIC-ITS（中断翻译服务）与 PCIe MSI/MSI-X 硬件注入全流程深度解析

## 1. PCIe MSI-X 消息中断的硬件本质

在 PCIe 体系中，**MSI（Message Signaled Interrupt）与 MSI-X 本质上不是专用的物理中断引脚，而是一次由 PCIe 设备发起的标准 Memory Write TLP 内存写事务**。

```mermaid
flowchart TD
    subgraph PCIe_Endpoint ["PCIe 外设 (网卡 / NVMe SSD)"]
        Event["事件触发: 如数据包接收完成 (Queue #3)"] --> MSIX_Table["查本地 MSI-X Table (位于 BAR 空间)"]
        MSIX_Table --> Gen_TLP["生成 Memory Write TLP\n• 目标地址: GITS_TRANSLATER (如 0x2C01_0040)\n• 写入数据: EventID = 3"]
    end

    subgraph PCIe_Root_Complex ["PCIe RC 与系统互联"]
        Gen_TLP --> AXI_Bridge["RC 总线桥: 自动在 AXI 侧带信号中附加 AXI-User(31:0) = DeviceID BDF"]
    end

    subgraph GIC_ITS ["GIC-ITS 硬件翻译引擎 (Interrupt Translation Service)"]
        AXI_Bridge --> ITS_Reg["接收写事务: GITS_TRANSLATER (带 DeviceID + EventID)"]
    end
```

---

## 2. ITS 核心翻译三级查表流水线（Device Table → ITT → Collection Table）

当 ITS 的 `GITS_TRANSLATER` 寄存器被写入时，硬件状态机在 **4~8 个时钟周期** 内自动执行三级查表，完成从逻辑事件到物理 CPU 核心的路由：

```mermaid
flowchart LR
    DevID["输入: DeviceID (来自 AXI 侧带)"] --> DT_Lookup["1. 查 Device Table (DT)"]
    DT_Lookup --> ITT_Base["获取该外设专属的 ITT (Interrupt Translation Table) 物理基地址"]

    EventID["输入: EventID (来自写入 Data)"] --> ITT_Lookup["2. 查外设专属 ITT 表"]
    ITT_Base --> ITT_Lookup
    ITT_Lookup --> ITT_Entry["获取映射结果:\n• 物理中断号: LPI (如 INTID 8195)\n• 目标集合: Collection ID (ICID 2)"]

    ITT_Entry --> CT_Lookup["3. 查 Collection Table (CT)"]
    CT_Lookup --> Target_RD["解析出目标 CPU 核心的 Redistributor 物理基地址 (RDbase)"]

    Target_RD --> Inject["4. 向目标 CPU 的 Redistributor 注入该 LPI 中断!"]
```

---

## 3. ITS 软件配置与命令队列（Command Queue）标准交互时序

操作系统在为 PCIe 设备分配 MSI-X 中断时，必须通过内存中的 **ITS Command Queue** 下发硬件配置命令：

```mermaid
sequenceDiagram
    participant OS as Linux 内核 (PCI/MSI 子系统)
    participant CmdQ as 内存中的 ITS Command Queue
    participant ITS as GIC-ITS 硬件控制器
    participant RD as 目标 CPU Redistributor

    Note over OS,ITS: 1. 映射设备 (Map Device)
    OS->>CmdQ: 写入 MAPD 命令 (DeviceID, ITT_Base_PA, Size, Valid=1)

    Note over OS,ITS: 2. 映射集合 (Map Collection)
    OS->>CmdQ: 写入 MAPC 命令 (ICID 2, Target_Redistributor_PA, Valid=1)

    Note over OS,ITS: 3. 映射事件到 LPI (Map Translation Interrupt)
    OS->>CmdQ: 写入 MAPTI 命令 (DeviceID, EventID=3, LPI=8195, ICID=2)

    Note over OS,ITS: 4. 同步栅栏 (Command Synchronization)
    OS->>CmdQ: 写入 SYNC 命令 (Target_Redistributor_PA)
    OS->>ITS: 写 GITS_CWRITER 寄存器 (推动写指针, 触发 ITS 硬件执行)

    ITS->>ITS: 硬件依次取出命令并配置内部缓存表
    ITS-->>OS: GITS_CREADR 追平 GITS_CWRITER (确认所有映射已硬件生效)
```

---

## 4. PCIe MSI-X Table 与 Pending Bit Array (PBA) 结构

MSI-X 相比传统 MSI 的核心优势在于支持多达 **2048 个独立中断向量**，且每个向量在 BAR 空间拥有独立的 16 字节条目：

| 偏移量 | 字段名称 | 位宽与作用 |
| :--- | :--- | :--- |
| `+0x00` | **Message Address** | 32 位低地址，填入 `GITS_TRANSLATER` 的物理基地址 |
| `+0x04` | **Message Upper Address** | 32 位高地址（支持 64 位物理地址） |
| `+0x08` | **Message Data** | 32 位数据，填入内核分配给该队列的 **EventID** |
| `+0x0C` | **Vector Control** | `Bit[0]` 为 **Mask bit**（置 1 时该向量被硬件屏蔽，中断被记录至 PBA） |

---

## 5. GICv4 直通虚拟化中断（Direct Virtual LPI Injection）

在 GICv3 虚拟化中，PCIe 设备的 MSI 必须先陷入 Host Hypervisor（EL2），由 KVM 构造虚拟中断后再注入 Guest OS，单次中断延迟高达 **$1\sim 3\mu\text{s}$**。

**GICv4 硬件直通方案**：
- ITS 新增 **`vPE（Virtual Processing Element）`** 映射表。
- 当处于运行态的虚拟机收到外设 MSI 时，ITS 配合 GICv4 Redistributor **直接将 Virtual LPI 投递进虚拟机的虚拟 CPU Interface（`ICV_*_EL1`）**，**显著降低了 VM-Exit 上下文切换开销（延迟降至 100ns 级）**！

---

## 6. 常见关键 ITS 故障与排查手册

### 陷阱 1：PCIe Bridge 丢失 DeviceID 导致 ITS 静默丢弃
- **故障现象**：PCIe 网卡驱动加载成功且 MSI-X 配置完成，网卡收发包正常，但 CPU **永远收不到任何中断**。
- **微架构根因**：
  - PCIe 控制器将 TLP 转换为 AXI 写事务时，SoC 互联设计缺陷未将 PCIe BDF（Bus/Device/Function）打入 AXI 的 `AWUSER[15:0]` 侧带信号；
  - ITS 收到的写请求其 `DeviceID` 为全零（非法设备）；
  - ITS 查 Device Table 失败，静默丢弃该中断（Silent Drop），并不产生总线错误。
- **排查手段**：读取 ITS 的 `GITS_CREADR` 与错误状态寄存器，查看是否有未定义设备违例计数。

### 陷阱 2：ITS 内存表属性未配置为 Shareable Cacheable 导致数据不同步
- **故障现象**：系统冷启动时 MSI-X 正常，但进行 CPU 热插拔（Hotplug）或执行 `MOVI` 迁移中断后，中断随机丢失。
- **根因**：
  - ITS 访问内存中的 ITT 和 CT 表时，基地址寄存器 `GITS_BASER<n>` 中的 Cacheability 与 Shareability 属性被配成了 Non-cacheable；
  - CPU 修改了内存中的 ITT 表项并写回 Cache，但 ITS 从 DDR 中读出了未同步的旧表项。
- **规避**：必须在 BSP 初始化中将所有 `GITS_BASER<n>` 配置为 **`Inner-Shareable Write-Back Read/Write-Allocate`**。
