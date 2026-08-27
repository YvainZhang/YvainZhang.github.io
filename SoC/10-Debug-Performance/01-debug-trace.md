# 调试方法论、CoreSight 硬件架构与非侵入式 Trace 完全指南

## 1. ARM CoreSight 硬件调试与 Trace 数据流全景拓扑

在复杂的多核 SoC 中，依靠打日志（`printk`）不仅会引入巨大的时间开销（Heisenbug 效应），而且在死锁或异常挂死时往往无法输出。ARM 体系结构采用专用的 **CoreSight 硬件调试与追踪子系统**：

```mermaid
flowchart TD
    subgraph CPU_Cluster ["多核 CPU 复合体 (Core 0 ~ Core N)"]
        Core0["Core 0 (CPU Logic)"] --- ETM0["ETM 0 (指令/分支追踪)"]
        Core1["Core 1 (CPU Logic)"] --- ETM1["ETM 1 (指令/分支追踪)"]
        STM["STM (系统跟踪微单元: 记录软件打点事件)"]
    end

    subgraph CoreSight_Interconnect ["CoreSight 聚合与路由网络"]
        ETM0 --> Funnel["CoreSight Funnel (多路追踪流时分复用聚合器)"]
        ETM1 --> Funnel
        STM --> Funnel

        Funnel --> ETF["ETF (Embedded Trace FIFO: 内部紧耦合 SRAM 缓冲)"]
        ETF --> ETR["ETR (Embedded Trace Router: 经 AXI 主机总线将 Trace 流直接写入 DDR)"]
        ETF --> TPIU["TPIU (Trace 物理引脚: 输出至外部 Lauterbach 硬件仿真器)"]
    end

    subgraph DAP_Control ["调试访问端口 (DAP: Debug Access Port)"]
        JTAG_SWD["外部 JTAG / SWD 物理接口"] --> DAP["DAP (Debug Access Port)"]
        DAP --> APB_AP["APB-AP: 访问 CoreSight 控制寄存器"]
        DAP --> AXI_AP["AXI-AP: 绕过 CPU 核心直接读写全局物理内存 (System Memory)"]
    end
```

---

## 2. 交叉触发矩阵（CTI / CTM）与全核同步冻结机制

在多核对称多处理（SMP）系统中，若某个 CPU 核心陷入死锁或触发断点，如果仅将该核心 Halt，**其余 CPU 核心、片上 DMA 以及硬件看门狗仍在继续运行，会迅速覆写内存破坏现场**。

```mermaid
sequenceDiagram
    participant Core0 as Core 0 (触发内核 Panic / 断点)
    participant CTI0 as Core 0 绑定的 CTI (Cross Trigger Interface)
    participant CTM as 片上 CTM (Cross Trigger Matrix 广播总线)
    participant CTI1 as Core 1 绑定的 CTI
    participant Core1 as Core 1 (正常运行中)
    participant WDT as SoC 硬件看门狗

    Note over Core0: 1. Core 0 发生未捕获异常或命中断点
    Core0->>CTI0: 输出触发信号 (Halt Event)
    CTI0->>CTM: 将事件映射到 Channel 0 并全芯片广播

    par 同步挂起其他核心
        CTM->>CTI1: 接收 Channel 0 事件
        CTI1->>Core1: 硬件强制拉高 EDBGRQ (Debug Request), 瞬间挂起 Core 1!
    and 冻结硬件看门狗
        CTM->>WDT: 触发 Watchdog Pause 输入, 冻结看门狗倒计时 (防止复位重启!)
    and 锁定 Trace 缓冲区
        CTM->>ETF: 停止 Trace 写入, 永久保留崩溃前最后 32KB 真实指令历史!
    end
```

---

## 3. 硬件断点、软件断点与观察点（Watchpoint）微架构对比

| 调试原语 | 实现机制与微架构原理 | 适用场景与限制 |
| :--- | :--- | :--- |
| **硬件断点 (Hardware Breakpoint)** | 由 CPU 内部专用的硬件比较器寄存器（`DBGBVR` / `DBGBCR`）监视当前取指 PC，地址匹配时触发 Debug 异常 | **唯一可用于 ROM / Flash 只读代码段的断点方式**；数量有限（ARM 核心通常仅提供 4~8 个硬件断点） |
| **软件断点 (Software Breakpoint)** | GDB 调试器将目标内存处的原始机器码读取保存，并原地替换为一条 `BRK #0`（ARM）或 `EBREAK`（RISC-V）指令 | 数量不受限制；**只能在 RAM 内存中生效**；自修改代码必须配合 D-Cache 刷回与 I-Cache 失效 |
| **数据观察点 (Watchpoint)** | 由专用数据地址比较器（`DBGWVR` / `DBGWCR`）监视 LSU 访存地址，匹配指定变量的 Load（读）或 Store（写） | 用于**精确定位内存踩踏（Memory Corruption）的罪魁祸首**；数量极少（通常 2~4 个） |

---

## 4. 复杂外设数据流“二分定界法（Bisection Path Method）”

当高速外设（如 NVMe、PCIe 网卡）出现数据丢失或错乱时，建立结构化观测矩阵，寻找**最后一个正常状态点**与**第一个异常状态点**：

```mermaid
flowchart LR
    P1["1. 外设内部 FIFO\n(读取 FIFO 计数器)"] -->|正常| P2["2. DMA 描述符\n(检查 Ownership 与 Addr)"]
    P2 -->|正常| P3["3. NoC 总线监控\n(抓取 AXI 写事务握手)"]
    P3 -->|异常! 发生在此处| P4["4. DDR 物理缓冲区\n(检查数据是否到达)"]
    P4 --> P5["5. CPU 驱动 ISR / NAPI\n(检查中断响应)"]
    P5 --> P6["6. 用户空间 Buffer\n(检查应用收到内容)"]
```
- **定界结论**：若步骤 3（NoC AXI 写事务已成功握手）正常，但步骤 4（DDR 缓冲区内容未更新），直接排查 **Cacheline 脏行逐出（Dirty Eviction）覆写** 或 **DDR 控制器交织映射配置错误**。
