# 多核启动超时、同步异常定位与 IPC 骤降诊断完全指南

## 1. 多核启动（SMP Secondary Boot）超时诊断决策树

在 Linux 多核启动阶段，若主核（CPU 0）打印 `CPU1: failed to come online` 并触发 5 秒超时：

```mermaid
flowchart TD
    Timeout["次核启动超时: CPU1 failed to come online"] --> Step1

    subgraph Triage_Flow ["次核状态四级排查链路"]
        Step1["1. 读取 PMU 电源域与复位状态 (Power & Reset Status)\n• 次核电源域 (Core Power Domain) 是否已上电 (PWR_ACK == 1)?\n• 次核逻辑复位 (CPU_RESET) 是否已释放?"]

        Step1 -->|已上电且复位已解冻| Step2["2. 通过 JTAG / CoreSight 读取次核当前 PC 指针"]

        Step2 -->|PC 停留在 BootROM WFE/WFI 等待循环| Cause_A["根因 A: 唤醒中断或入口未到达\n• 主核写启动入口后未执行 SEV 指令或未发送 SGI 中断\n• 启动入口地址寄存器填入了虚拟地址而非物理地址 (PA)"]

        Step2 -->|PC 停留在 VBAR_EL1 异常向量表中| Cause_B["根因 B: 早期汇编发生同步中止\n• 读取次核独立的 ESR_EL1 / FAR_EL1\n• 次核早期临时栈未对齐或页表映射超出寻址范围"]

        Step2 -->|PC 停留在 secondary_startup 但共享 Flag 不变| Cause_C["根因 C: 缓存一致性或内存屏障缺失\n• 主核与次核未正确使能 SMP / DSU 一致性互联通道\n• 次核将上线标志写在本地 Cache, 主核未观察到"]
    end
```

---

## 2. MMIO 同步异常（Data Abort）结合 NoC 错误日志定位

- **现象**：驱动执行 `readl(uart_base)` 时，CPU 触发 `Data Abort`（`ESR = 0x96000010: Synchronous External Abort`）。
- **定位推演**：
  1. 检查页表：虚拟地址已正确建立映射，属性为 `Device-nGnRE`，排除 Translation Fault；
  2. 查阅 NoC 互联错误记录器（Fault Logger）：发现目标地址落在 UART 控制器窗口，但响应为 **`Target Timeout`**；
  3. 查阅时钟控制器（CCU）：发现外设的 APB 总线时钟（PCLK）被电源管理系统（Runtime PM）意外关闭（Gate Off）；
  4. **结论**：外部总线无时钟响应导致事务挂死，桥接器超时向 CPU 回复 External Abort。

---

## 3. 循环 IPC 从 2.1 跌至 0.5 的微架构归因案例

```mermaid
flowchart LR
    IPC_Drop["应用循环 IPC 骤降: 2.1 -> 0.5\n(CPU 利用率仍为 100%)"] --> PMU_Measure["读取 ARM PMU 硬件事件"]

    PMU_Measure --> Event1["BR_MIS_PRED (分支失准): 0.2% (正常)"]
    PMU_Measure --> Event2["L1D_CACHE_REFILL: 激增 800% (严重)"]
    PMU_Measure --> Event3["LL_CACHE_MISS_RD: 激增 500% (严重)"]
    PMU_Measure --> Event4["DDR Controller Bandwidth: 95% 饱和 (瓶颈!)"]

    Event2 & Event3 & Event4 --> Conclusion["定位结论: 数据集体积超出了 L2/L3 缓存容量\n且后台 DMA 占用了内存总线带宽 -> 陷入严重的 Memory-Bound 停顿!"]
```

- **针对性优化策略**：
  - 实施数据分块（Cache Blocking / Tiling），限制单次遍历的数据量在 L1/L2 缓存容量以内；
  - 调整结构体成员布局，提高 Spatial Locality（空间局部性）。
