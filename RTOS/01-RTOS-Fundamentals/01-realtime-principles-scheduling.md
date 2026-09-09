# 实时性与调度理论

## 1. 实时性的工程本质

在操作系统语境中，“实时”（Real-Time）常被误解为“计算速度快”。在硬件与控制工程视角下，**实时性的核心本质是时序确定性（Timing Determinism）**：

$$\text{正确性} = \text{逻辑结果正确} \land \text{在限定时限 (Deadline) 内完成}$$

如果一个电动机磁场定向控制（FOC）算法在 $50\,\mu\text{s}$ 内完成闭环能完美输出 PWM，但由于调度延迟或中断抖动拖到 $80\,\mu\text{s}$ 才输出，即使计算出的电流角度完全正确，系统也会引发逆变器过流击穿或电机失步。

```mermaid
flowchart TD
    subgraph HardRT["硬实时 (Hard Real-Time)"]
        H1["错过时限 (Deadline Miss)"] --> H2["灾难性后果 / 系统完全失效"]
        H3["示例: 汽车 ABS 制动、雷达导引、电机 FOC"]
    end
    subgraph FirmRT["固实时 (Firm Real-Time)"]
        F1["错过时限"] --> F2["结果价值归零，但不危及系统"]
        F3["示例: 音视频解码关键帧丢包"]
    end
    subgraph SoftRT["软实时 (Soft Real-Time)"]
        S1["错过时限"] --> S2["系统性能/服务质量 (QoS) 降级"]
        S3["示例: UI 触控刷新、网络数据包传输"]
    end
```

### 关键时序指标

| 指标名称 | 英文定义 | 物理意义 | 典型目标量级 |
| :--- | :--- | :--- | :--- |
| **响应时间** | Response Time | 从事件触发（如引脚跳变）到处理任务完成的整段时间 | 数微秒至数毫秒 |
| **中断延迟** | Interrupt Latency | 硬件中断触发到 CPU 执行 ISR 第一条指令的时间间隔 | $< 1\,\mu\text{s}$ |
| **调度延迟** | Scheduling Latency | 就绪任务产生到调度器切换至该任务开始执行的时间 | $1 \sim 10\,\mu\text{s}$ |
| **时钟抖动** | Jitter | 周期性任务实际执行周期的离散程度（$\Delta T = |T_{\text{act}} - T_{\text{exp}}|$） | $< 5\%$ 周期 |

---

## 2. 任务模型与经典调度理论

在周期性实时任务模型中，每个任务 $\tau_i$ 由四元组定义：

$$\tau_i = (C_i, T_i, D_i, P_i)$$

- $C_i$ (Computation Time)：最坏情况执行时间（WCET, Worst-Case Execution Time）。
- $T_i$ (Period)：任务释放周期。
- $D_i$ (Deadline)：相对截止时间（通常隐式等于周期 $D_i = T_i$）。
- $P_i$ (Priority)：分配给该任务的静态或动态优先级。

系统的处理器利用率 $U$ 定义为：

$$U = \sum_{i=1}^{n} \frac{C_i}{T_i}$$

### 2.1 单调速率调度算法（RMS, Rate-Monotonic Scheduling）

RMS 是针对静态优先级抢占式调度的经典最优算法（[Liu & Layland, 1973](https://www.cs.ru.nl/~hooman/DES/liu-layland.pdf)）。
* **规则**：任务周期 $T_i$ 越短（即请求速率越高），静态分配的优先级 $P_i$ 越高。
* **可调度性充分性判据（Liu & Layland Utilization Bound）**：
  若满足下列假设，且系统总利用率满足不等式：

  $$U = \sum_{i=1}^{n} \frac{C_i}{T_i} \le n(2^{1/n} - 1)$$

  则 RMS **保证该任务集是可调度的（Sufficient Condition，充分非必要条件）**。

  当任务数 $n \to \infty$ 时，该界限下确界收敛为：

  $$\lim_{n \to \infty} n(2^{1/n} - 1) = \ln 2 \approx 0.693$$

> [!WARNING]
> **定理成立的严苛前提假设（Assumptions）**：
> 1. **独立任务（Independent）**：任务之间不存在 IPC 互斥锁阻塞、前序同步或共享资源竞态（Blocking Time $B_i = 0$）。
> 2. **隐式时限（Implicit Deadline）**：每个任务的相对截止时间严格等于其周期（$D_i = T_i$）。
> 3. **理想零开销（Zero Overhead）**：忽略上下文切换时间、时钟中断处理和调度器决算耗时。
> 4. **完全可抢占（Fully Preemptive）**：不存在长时间关中断或关调度的不可抢占临界区。

> [!NOTE]
> **工程判据修正与谐波周期例外**：
> * **充分而非必要**：若利用率 $U > n(2^{1/n} - 1)$，**并不代表系统不可调度**！该界限是最坏情况下的悲观下界。
> * **谐波周期（Harmonic / Simply Periodic）**：若系统中所有任务的周期彼此成整数倍（例如 $10\,\text{ms}, 20\,\text{ms}, 40\,\text{ms}$），RMS 的可调度利用率上限可达 **$100\%$ ($U \le 1.0$)**。
> * **实际工程中的响应时间分析（RTA）**：实际工程中存在关中断、信号量阻塞和切换开销，通常需使用精确的响应时间递归分析方程（Response Time Analysis）逐一验证：$R_i = C_i + B_i + \sum_{j \in hp(i)} \lceil R_i / T_j \rceil C_j \le D_i$。

### 2.2 最早截止时间优先（EDF, Earliest Deadline First）

EDF 是动态优先级调度的理论最优算法。
* **规则**：在任意调度决策点，截止时间 $d_i$ 离当前时间最近的任务获得最高执行权。
* **可调度性界限**：在单核抢占式系统下，EDF 的利用率理论上限可达 **$100\%$ ($U \le 1.0$)**。
* **工程落地代价**：EDF 必须在每次调度或任务释放时，根据绝对 Deadline 动态重构就绪队列（维护最小堆或红黑树），运算开销随任务数增加显著上升，且在瞬时过载（Overload）时可能引发多个任务接连超时（Domino Effect）。因此绝大多数工业级微内核（如 FreeRTOS）选择实现开销为 $O(1)$ 的静态优先级抢占。

---

## 3. 常见调度范式与对比

```mermaid
sequenceDiagram
    participant Low as 低优先级任务 (Low)
    participant High as 高优先级任务 (High)
    participant ISR as 硬件中断 (ISR)

    Note over Low: 正在执行低优先级工作
    ISR->>Low: 硬件中断触发
    Note over ISR: 执行顶半部中断服务程序
    ISR->>High: 产生高优先级事件 (唤醒 High)
    Note over High: 抢占式调度: 发生上下文切换
    High->>High: 优先执行高优先级任务
    High->>Low: High 进入阻塞/完成，切换回 Low
```

### 3.1 抢占式调度（Preemptive Scheduling）
* 当更高优先级的任务就绪时，内核**立即暂停**当前正在运行的低优先级任务，保存其寄存器上下文，并切入高优先级任务。
* **优点**：极低且确定性的响应时间，高优先级任务无需等待低优先级任务主动交出 CPU。
* **缺点**：上下文切换频繁，临界资源共享需要严格使用互斥锁或临界区。

### 3.2 协作式调度（Cooperative Scheduling）
* 任务一旦获得 CPU，将持续占用，直到其显式调用 `task_yield()`、进入延时或因等待资源自愿放弃控制权。
* **优点**：无非预期的线程交织，重入问题大幅降低，几乎不需要考虑微秒级并发锁竞争，RAM 占用极低。
* **缺点**：实时确定性脆弱，任何一个任务的死循环或长时间计算将直接造成全系统挂起。

### 3.3 时间片轮转（Time-Slicing Round-Robin）
* 多个具有**相同优先级**的就绪任务，各自被分配固定的时间配额（通常为 1 个 SysTick Tick）。
* 当 Tick 中断发生且当前任务时间片耗尽，调度器顺位切入同优先级的下一个任务。
