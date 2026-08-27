# AXI 突发地址计算、Outstanding 延迟隐藏与总线拥塞深度推演

## 1. AXI4 Burst 突发传输边界与字节使能（WSTRB）计算

AXI 协议支持三种突发模式：`FIXED`（FIFO 专用）、`INCR`（常规内存自增）和 `WRAP`（Cacheline 环绕回填）。

```mermaid
flowchart LR
    subgraph Burst_Calc ["INCR 突发地址递增数学模型"]
        Start["起始地址: Addr_0 = 0x1004\n突发大小: AxSIZE = 2 (4 字节/Beat)\n突发长度: AxLEN = 3 (共 4 个 Beat)"]

        B0["Beat 0 访问地址: 0x1004\n(对齐 64 位总线: Byte 4~7 有效, WSTRB = 0xF0)"]
        B1["Beat 1 访问地址: 0x1008\n(对齐 64 位总线: Byte 0~3 有效, WSTRB = 0x0F)"]
        B2["Beat 2 访问地址: 0x100C\n(对齐 64 位总线: Byte 4~7 有效, WSTRB = 0xF0)"]
        B3["Beat 3 访问地址: 0x1010\n(对齐 64 位总线: Byte 0~3 有效, WSTRB = 0x0F)"]
    end

    Start --> B0 --> B1 --> B2 --> B3
```

### 4KB 边界对齐规范（4KB Boundary Rule）
- **规范约束**：AXI 协议严格禁止一次突发（Burst）跨越 **4KB 物理地址边界**（例如从 `0x1FF0` 发起 64 字节传输）。
- **微架构动因**：SoC 内部的总线从机解码器与 MMU/SMMU 最小页管理粒度为 4KB。如果允许跨 4KB 边界，单次 AXI 突发可能同时跨越两个完全不同的物理外设或页表保护域，导致总线仲裁与权限校验无法处理。

---

## 2. Outstanding 传输如何隐藏总线延迟：数学模型推演

假设系统外部 DDR 访存平均往返延迟（Round-trip Latency）为 **$t_{\text{latency}} = 100\text{ns}$**，单次 AXI Burst 传输 64 字节有效数据。

```mermaid
flowchart TD
    subgraph No_Outstanding ["模式 A: 无 Outstanding (深度 = 1, 串行阻塞等待)"]
        A1["发出请求 1"] --> A2["等待 100ns"] --> A3["收到数据 64B"] --> A4["发出请求 2"] --> A5["等待 100ns"]
        A_BW["最大吞吐: 64B / 100ns = 640 MB/s (无法发挥总线带宽!)"]
    end

    subgraph With_Outstanding ["模式 B: 深度 = 16 的 Outstanding 流水线"]
        B1["连续发出 16 个读请求 (流水线打满)"]
        B2["100ns 后, 数据以每个周期 1 拍的速度连续不间断返回!"]
        B_BW["最大吞吐: 64B × 16 / 100ns = 10.24 GB/s (提升 16 倍, 彻底跑满总线!)"]
    end
```

- **推论**：在高性能 DMA 和 CPU 设计中，**仅增加总线位宽无法提升吞吐；必须匹配足够的 Outstanding 事务队列深度**，方能完全吸收和掩盖外部 DDR 的固有延迟。

---

## 3. 跨外设访问无序性与 I/O 屏障推演

假设 CPU 顺序执行以下两行代码：
```c
writel(0x1, CRU_RESET_RELEASE_REG); /* 1. 写复位控制器：释放外设 A 的复位 */
val = readl(PERIPH_A_ID_REG);        /* 2. 读外设 A 的 ID 寄存器 */
```

```mermaid
sequenceDiagram
    participant CPU as CPU 执行核心
    participant NoC as NoC 片上总线
    participant CRU as 复位控制器 (Slow APB Bridge)
    participant Periph as 外设 A (Fast APB Bridge)

    Note over CPU,Periph: 严重时序竞态: 两个外设位于不同分支总线!
    CPU->>NoC: 1. 发出写复位事务 (Target: CRU)
    CPU->>NoC: 2. 紧接着发出读 ID 事务 (Target: Periph)

    NoC->>Periph: 读事务经高速通路先一步到达外设 A!
    Note over Periph: 此时外设 A 内部复位尚未释放, 总线返回 0 或超时崩溃!
    NoC->>CRU: 随后写复位事务才到达 CRU...

    Note over CPU,Periph: 规范修复: 强制在写与读之间插入 I/O 屏障 (mb())
```

- **排查手段**：在访问不同外设寄存器存在因果依赖时，必须在中间显式插入 I/O 内存屏障（ARM 上为 `dsb sy` / Linux 内核 `mb()`），确保前序总线事务彻底生效并被对端接收后，方可发出后续请求。
