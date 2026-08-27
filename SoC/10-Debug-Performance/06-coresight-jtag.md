# ARM CoreSight 硬件调试组件、JTAG/DAP 协议与 ETM Trace 深度剖析

## 1. ARM CoreSight 调试体系架构（Debug & Trace Architecture）

CoreSight 是 ARM 架构定义的片上硬件调试与追踪规范，它在物理芯片内独立于 CPU 计算核心，构建了一套专用的调试互联子系统：

```mermaid
flowchart TD
    subgraph CoreSight_Architecture ["CoreSight 内部拓扑结构"]
        DAP["DAP (Debug Access Port)\n通过外部 2-wire SWD 或 5-wire JTAG 引脚接入"]

        DAP --> DP["Debug Port (DP: 协议转换与时钟同步)"]
        DP --> AP_Bus["Access Port (AP) 互联总线"]

        AP_Bus --> APB_AP["APB-AP (访问调试控制寄存器)"]
        AP_Bus --> AXI_AP["AXI-AP (系统总线主控: 直读物理 DDR/MMIO)"]

        APB_AP --> Core_Debug["CPU 核心调试单元 (EDBGRQ, DBGBCR, DBGWCR)"]
        APB_AP --> ETM_Ctrl["ETM / PTM 控制器 (Embedded Trace Macrocell)"]
        APB_AP --> CTI_Ctrl["CTI 交叉触发矩阵控制器"]
    end
```

---

## 2. JTAG 与 SWD 协议底层通信时序

```mermaid
sequenceDiagram
    participant Host as 外部调试器 (J-Link / Lauterbach)
    participant Target as SoC DAP 硬件引脚 (JTAG / SWD)

    Note over Host,Target: JTAG 模式 (5 物理引脚: TCK, TMS, TDI, TDO, nTRST)
    Host->>Target: TMS 控制 TAP 状态机在 16 种状态间跃迁 (Test-Logic-Reset -> Shift-DR -> Update-DR)
    Host->>Target: TDI 串行移入指令 (IR) 与数据 (DR), TDO 串行回传数据

    Note over Host,Target: SWD 模式 (仅需 2 物理引脚: SWCLK + SWDIO)
    Host->>Target: 发送 8-bit 请求头 (Start + AP/DP + RnW + Addr + Parity + Stop)
    Target-->>Host: 返回 3-bit 应答 (ACK = 001b 表示 OKAY)
    Host->>Target: 传输 32-bit 数据负载 + 1-bit 奇偶校验位
```

- **SWD 优势**：仅用 2 根引脚即可实现与 JTAG 相当的调试带宽（最高达 50MHz 时钟），极大节省了芯片封装引脚（Pin Count）与 PCB 走线面积。

---

## 3. ETM 非侵入式追踪（Instruction & Data Trace）与压缩编码

**ETM（Embedded Trace Macrocell）** 能够在 CPU 全速运行（如 3.0GHz）时，以**硬件零侵入（Zero Intrusion）** 的方式实时捕获每条指令的执行流：

### ETM 硬件流压缩算法机制
由于引脚带宽限制，ETM 不可能输出每条指令的完整 PC。它采用极高压缩比的 **分支追踪算法（Branch-only Compression）**：
1. **顺序执行**：对于顺序执行的指令，ETM **不输出任何追踪数据**（调试器利用离线 ELF 文件直接反汇编推进 PC）；
2. **条件分支**：仅输出 1 个比特：`1` 代表分支跳转成功（Taken），`0` 代表未跳转（Not-taken）；
3. **间接跳转（Indirect Jump / Function Call）**：输出目标函数的完整物理 PC 地址。
- **效果**：平均每条执行指令仅需消耗 **$1 \sim 2$ 个比特** 的 Trace 数据带宽，使得片内 32KB ETF 环形缓冲能够记录数十万条历史执行指令！
