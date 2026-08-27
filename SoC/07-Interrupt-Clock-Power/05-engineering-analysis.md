# 中断状态跃迁、优先级反转与低功耗竞争状态深度推演

## 1. 电平中断为何在 EOI 后反复重入：微架构推演

对于电平敏感型中断（Level-sensitive Interrupt），GIC 控制器采样的是**物理信号线上的实时电压电平**：

```mermaid
sequenceDiagram
    participant Dev as 外设 (如 UART FIFO 满)
    participant Line as 物理中断线 (IRQ Line)
    participant GIC as GIC 中断控制器
    participant CPU as CPU 核心 (ISR 执行流)

    Dev->>Line: FIFO 满, 硬件将 IRQ Line 拉高为高电平 (1b)
    Line->>GIC: GIC 采样到高电平, 状态变更为 Pending
    GIC->>CPU: 投递物理异常, CPU 读取 ICC_IAR1_EL1 响应
    Note over GIC: 中断状态变更为 Active

    Note over CPU: 错误处理: 仅写了 ICC_EOIR1_EL1, 未读空 UART FIFO!
    CPU->>GIC: 写 ICC_EOIR1_EL1 结束中断 (Deactivate)
    Note over GIC: 中断状态复位为 Inactive

    Note over Line,GIC: 但此时物理 IRQ Line 依然被外设维持在高电平 (1b)!
    GIC->>GIC: GIC 硬件再次采样到高电平, 瞬间重新生成 Pending 状态!
    GIC->>CPU: CPU 刚退出 ISR 汇编, 瞬间再次被同一个中断打断 -> 中断死循环!
```

- **正确处理原则**：
  1. 在 ISR 中首先读取外设数据寄存器将 FIFO 排空，或者向中断状态寄存器写入清除位（W1C）；
  2. 确认外设状态寄存器的原始中断标志已归零（引脚电平已恢复为低电平）；
  3. 最后向 GIC 写入 `ICC_EOIR1_EL1` / `ICC_DIR_EL1`。

---

## 2. 中断优先级反转（Priority Inversion）与死锁风险

中断控制器内部的优先级硬件仲裁（Priority Preemption）仅决定哪个中断能够抢占 CPU 执行流，**它完全脱离于操作系统内核的互斥锁（Mutex / Spinlock）体系**：

```mermaid
flowchart TD
    subgraph Danger_Scenario ["中断与线程的死锁场景"]
        Thread["低优先级用户/内核线程: 获取自旋锁 spin_lock(&my_lock)"]
        IRQ["高优先级硬中断 ISR: 发生抢占, 在本核进入中断上下文"]
        Deadlock["ISR 内部尝试获取同一把锁: spin_lock(&my_lock)\n• ISR 陷入无限死循环自旋等待锁释放\n• 但持有锁的线程被 ISR 永久打断, 永远无法继续执行并释放锁!\n• 结果: CPU 陷入不可恢复的自旋死锁 (Lockup)"]
    end

    Thread --> IRQ --> Deadlock
```

- **规避规范**：当共享自旋锁可能被**当前 CPU 上的硬中断处理程序（ISR）抢占获取**时，线程上下文必须使用 **`spin_lock_irqsave(&lock, flags)`**（在获取锁的同时关闭本地中断），防止当前核心在持锁期间被本地 ISR 抢占陷入死锁；若该锁仅在跨核线程之间竞争且明确不在中断上下文中获取，使用普通 `spin_lock` 即可。

---

## 3. 定时器漂移与系统时间累积误差推算

假设某嵌入式平台系统计数器（System Counter）名义频率为 $24\text{MHz}$，但由于外部晶振老化或电容温漂，实际输出频率为 $23.976\text{MHz}$（误差 $\Delta f = -24\text{kHz}$，即 $-1000\text{ppm}$）：

$$\text{PPM 误差} = \frac{23.976\text{MHz} - 24.000\text{MHz}}{24.000\text{MHz}} \times 10^6 = \mathbf{-1000 \text{ ppm}}$$

### 误差的时间累积效应：
- 每秒钟系统时间偏慢：$1\text{s} \times 1000 \times 10^{-6} = \mathbf{1 \text{ ms}}$；
- 运行 1 小时后累积误差：$3600\text{s} \times 1\text{ms/s} = \mathbf{3.6 \text{ 秒}}$；
- 运行 1 天后累积误差：$3.6 \times 24 \approx \mathbf{86.4 \text{ 秒}}$。
- **工程诊断准则**：若系统内所有依赖 `nanosleep()`、`timerfd` 的超时时间均按严格相同的比例偏长或偏短，应直接测量外部时钟源晶振频率，严禁通过逐个修改各个驱动的分频系数来“打补丁”。

---

## 4. Runtime PM 动态下电与外设 MMIO 访问的竞态条件

```mermaid
sequenceDiagram
    participant CPU_A as CPU Core A (正在执行业务驱动)
    participant RPM as Linux Runtime PM 框架
    participant Power as 电源域硬件控制器
    participant CPU_B as CPU Core B (准备访问该外设)

    CPU_A->>RPM: pm_runtime_put_autosuspend(dev) (引用计数归零)
    RPM->>Power: 启动下电工作队列, 开始关断外设电源域

    Note over CPU_B,Power: 竞态发生: CPU B 未先获取引用即发起访问!
    CPU_B->>Power: 直接执行 readl(dev_reg)
    Note over Power: 此时电源域已断电或隔离已开启, 总线无法响应!
    Power-->>CPU_B: 触发 Synchronous External Abort 崩溃!

    Note over CPU_B,Power: 正确模式: 先增引用, 确认上电后再读写
    CPU_B->>RPM: pm_runtime_get_sync(dev) (同步阻塞等待上电完成)
    RPM->>Power: 恢复电源域供电与时钟
    CPU_B->>Power: 安全执行 readl(dev_reg)
    CPU_B->>RPM: pm_runtime_put(dev)
```
