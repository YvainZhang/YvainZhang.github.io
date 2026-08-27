# Clock、Reset 与 Power Domain

## 1. 为什么必须一起理解

一个 IP 可以被访问或开始工作，通常需要同时满足：

1. 所在 Power Domain 已上电且电压稳定。
2. 与其他电源域之间的 Isolation 已按顺序解除。
3. 总线 Clock 和功能 Clock 已存在并稳定。
4. Reset 已同步释放。
5. 必要的 Pinmux、PHY、Memory 和 Firmware 已配置。

Clock、Reset 和 Power 是三个独立但互相约束的控制维度：

- Clock Gate 只停止时序逻辑翻转，寄存器内容通常仍保留。
- Reset 把状态机或寄存器置于定义状态，不必然降低静态功耗。
- Power Gate 切断供电，非保持寄存器通常丢失内容。

## 2. Clock Tree

### 2.1 时钟链路

典型时钟树：

```text
Crystal/Oscillator
    ↓
PLL
    ↓
Clock Mux
    ↓
Divider
    ↓
Clock Gate
    ↓
Consumer IP
```

同一条链中也可能先分频再选择，或包含多个级联 Gate。

### 2.2 时钟源

- 外部晶振：精度较高，是常见基准。
- 内部 RC：启动快、成本低，但频率误差较大。
- 外部输入 Clock：由其他芯片提供。
- PLL：将参考频率倍频并产生高频时钟。

Always-on 域常使用低频源维持 RTC、唤醒和电源状态机，主系统启动后才切换到高性能 PLL。

### 2.3 PLL

PLL 通过反馈使输出频率与参考时钟保持特定比例。概念性关系为：

```text
Fout ≈ Fref × M / (N × P)
```

实际 PLL 还受 VCO 工作范围、抖动、锁定时间、Fractional 模式、Spread Spectrum 和芯片规定的切换流程限制。

配置 PLL 的典型安全流程：

1. 临时把 Consumer 切到安全时钟源或降低分频。
2. 将 PLL 置于 Bypass/Reset，按手册写入参数。
3. 启动 PLL，等待 Lock 状态并处理超时。
4. 配置下游 Divider。
5. 将 Mux 切回 PLL。

不能在 CPU 正由某 PLL 驱动时随意重配该 PLL，否则可能立即失去执行时钟。

### 2.4 Clock Mux、Divider 与 Gate

- Mux：选择父时钟。动态切换应使用 Glitch-free Mux 或遵循停钟流程。
- Divider：降低频率。整数分频最常见，也可能有小数分频。
- Gate：停止无用模块的时钟，降低动态功耗。

一个 IP 常有多个 Clock：

- Bus/PCLK：保证寄存器接口工作。
- Core/Functional Clock：驱动功能状态机。
- Reference Clock：给 PHY 或协议定时。
- Sample Clock：采样外部输入。

只开 Bus Clock 时可能“寄存器可读，但功能不运行”。

### 2.5 Clock Domain Crossing（CDC）

不同 Clock Domain 的信号不能直接假定满足建立/保持时间。常用方法：

- 两级同步器：适合慢变化单比特电平，但不能保证短脉冲被捕获。
- Toggle/Handshake：可靠传递事件或配置。
- 异步 FIFO：传输连续多比特数据。
- Gray Code：常用于跨域指针或计数。
- Async Bus Bridge：在事务层完成请求/响应同步。

CDC 不仅是 RTL 问题。软件也要等待跨域配置生效，例如写 Divider 后轮询 Busy/Update Done。

## 3. Reset Architecture

### 3.1 Reset 来源

- POR：上电复位。
- Brown-out Reset：电压跌落。
- External Pin Reset：外部引脚。
- Watchdog Reset：软件失控或任务超时。
- Software Reset：软件请求系统或模块重启。
- Security Reset：安全违规触发。
- Thermal Reset：过温保护。
- Debug Reset：调试器请求。

### 3.2 Reset 作用范围

- Chip Reset：大部分芯片逻辑复位。
- System/Cluster Reset：某处理器或互联子系统。
- Core Reset：单个 CPU 核。
- Peripheral Reset：单个控制器。
- PHY Reset：高速物理层。
- Register Reset 与 Datapath Reset：有时可独立控制。

必须区分 Reset Source 和 Reset Scope。例如 Watchdog0 是来源，它可以被配置为只复位应用域或触发整芯片复位。

### 3.3 异步置位、同步释放

常见设计允许 Reset 异步 Assert，使 Clock 异常时也能迅速进入安全状态；Deassert 则同步到目标 Clock Domain，避免不同触发器在不同时刻离开复位导致亚稳态或非法状态。

如果目标 Clock 未运行，同步 Reset 可能无法释放。因此软件顺序一般是先准备 Clock，再 Deassert Reset。

### 3.4 Reset Cause

Always-on 域通常保存 Reset Cause。启动软件应尽早读取并保存，因为后续写寄存器或再次复位可能清除它。需要区分：

- Sticky 位是否 W1C。
- 多个原因能否同时记录。
- POR 是否清除所有历史。
- Watchdog 是否还保存超时通道和计数值。

### 3.5 Reset 值不等于可用配置

寄存器的 Reset Value 仅表示复位后的初值，不保证功能已启用或值适合当前板级设计。比如 UART Divider 复位值可能不对应当前输入频率，DDR PHY 更不可能靠默认值完成训练。

## 4. Power Architecture

### 4.1 Voltage Domain 与 Power Domain

Voltage Domain 表示使用同一电压电平的区域；Power Domain 表示能够被独立上电或下电的逻辑区域。两者可能重合，也可能一个电压域内包含多个可独立 Gate 的电源域。

常见划分：

- Always-on：PMU、RTC、Wakeup、部分 SRAM。
- CPU Cluster。
- GPU/NPU。
- DDR/Memory。
- High-speed I/O/PHY。
- Peripheral。

### 4.2 Power Gate

由 Header/Footer Switch 切断电源。上电瞬间可能产生较大 Inrush Current，复杂系统会分级打开开关并等待 Power Good。

### 4.3 Isolation

源 Power Domain 关闭后，输出可能成为不确定值。Isolation Cell 将跨域输出钳位到 0 或 1。一般原则是：下电前先隔离，上电稳定后再解除隔离。

### 4.4 Retention

Retention Register 或 Retention SRAM 使用保留电源，在主域掉电后保存少量上下文。软件或硬件需要明确：

- 哪些寄存器自动保持。
- 哪些状态必须由软件保存到 SRAM/DDR。
- 恢复后哪些配置仍需重写。
- 保留数据是否有版本和完整性校验。

### 4.5 Level Shifter

不同电压域之间需要电平转换。电压变化期间必须满足芯片定义的顺序，否则接收端可能过压、漏电或采样错误。

## 5. 一个推荐的模块上电顺序

具体芯片顺序必须以手册为准，概念性流程如下：

```text
确认父电源/父时钟可用
→ 请求 Power Domain 上电
→ 等待 Power Good/Acknowledge
→ 配置并打开总线 Clock、功能 Clock
→ 保持 Reset Assert 若硬件未自动保持
→ 解除 Isolation
→ 按要求等待若干周期
→ Deassert Bus/Logic/PHY Reset
→ 恢复寄存器或执行模块初始化
→ 清除旧中断状态
→ 允许业务请求
```

某些芯片要求在解除 Isolation 前先解除 Reset，不能机械套用上述模板。

## 6. 一个推荐的模块下电顺序

```text
阻止新请求进入
→ 等待设备 Idle、DMA 和总线事务完成
→ 屏蔽并清除中断
→ 保存非保持上下文
→ Assert Reset（若手册要求）
→ 打开 Isolation
→ Gate 功能/总线 Clock
→ 请求 Power Domain 下电
→ 等待 Acknowledge
```

最大风险是仍有 Outstanding Transaction 时下电，导致上游永远等不到响应。

## 7. DVFS 与 OPP

动态电压频率调整利用低负载时降低电压和频率来节能。OPP（Operating Performance Point）把允许的频率与最低安全电压绑定。

基本规则：

- 升频：通常先升电压，等待稳定，再提高频率。
- 降频：通常先降低频率，再降电压。

DVFS 还需协调 Regulator、PLL、Clock Divider、内存时序、互联 QoS 和 Thermal Controller。频率改变后，依赖该 Clock 的波特率、Timer 或性能计数换算也可能需要更新。

## 8. 软件框架中的表现

Linux Device Tree 常通过以下属性描述依赖：

```dts
uart0: serial@11000000 {
    compatible = "vendor,soc-uart";
    reg = <0x0 0x11000000 0x0 0x1000>;
    interrupts = <...>;
    clocks = <&cru BUS_UART0>, <&cru CORE_UART0>;
    clock-names = "bus", "core";
    resets = <&cru RESET_UART0>;
    power-domains = <&pmu PD_PERIPH>;
    status = "okay";
};
```

这段描述表达依赖关系，但不保证每项都由驱动直接管理；某些依赖由总线、Power Domain Provider 或固件代理处理。

## 9. 故障现象与优先检查项

| 现象 | 优先检查 |
| --- | --- |
| MMIO 访问总线超时 | Power、Bus Clock、Reset、地址译码 |
| 寄存器正常，模块无动作 | Functional Clock、PHY Clock、Pinmux、Enable 位 |
| 偶发错误且与频率有关 | PLL Lock、Divider、CDC、供电电压、时序裕量 |
| Suspend 后无法恢复 | Retention、Isolation 顺序、Clock Parent、上下文恢复 |
| 只在冷启动失败 | POR 顺序、晶振启动、PLL Lock、未初始化的保留状态 |
| 只在热复位失败 | Reset Scope 不完整、旧中断/DMA/PHY 状态未清 |
| 一个域下电导致全系统卡死 | 未排空事务、跨域请求、共享 Clock/Reset 依赖 |

## 10. 如何证明时钟、复位和电源状态正确

“驱动已经调用 enable”不是证据。软件框架的引用计数、控制器寄存器和硬件实际输出可能处于三种不同状态，验证时要把它们分开。

检查 Clock 时，先沿树读取 Parent、Mux、Divider 和 Gate，再根据寄存器值计算理论频率。若芯片提供 Clock Monitor 或 Test-out Pin，应测量实际输出。UART 可以用 TX 波形反推 Baud Clock，Timer 可以用外部时间基准校验，PLL 则要同时看 Lock、失锁 Sticky 位和供电状态。一个静态的 Lock=1 不能证明运行期间没有短暂失锁。

每路 Clock 的用途要单列。Bus Clock 决定寄存器接口是否能完成事务，Core Clock 推动功能状态机，Reference Clock 决定协议或 PHY 的时间基准。若 MMIO 正常而模块不产生输出，读取三者的 Gate 和频率，比反复改业务寄存器更有效。DVFS 后还应复核依赖旧频率计算的 UART Divider、Watchdog Timeout 和性能计数换算。

检查 Reset 时，要读取 Assert 状态和模块内部复位完成状态，并确认控制位的极性。还要弄清 Reset Scope：只复位寄存器接口、只复位核心逻辑，还是连 DMA、FIFO、Interrupt Status 和 PHY 一起复位。热复位后出现旧包、旧中断或 Link 状态异常，往往说明软件假定的 Reset Scope 大于硬件实际范围。

同步释放的 Reset 依赖目标 Clock。若 Gate 仍关闭，软件写下 Deassert 命令后，Reset Controller 的请求位可能已经变化，但模块端同步器尚未看到释放沿。可靠流程会先打开对应 Clock，等待稳定，再释放 Reset，并在可能的情况下读取模块 ID 或 Idle 状态作为完成确认。

检查 Power Domain 时，至少读取请求、Acknowledge、Power Good 和 Isolation 四类状态。它们的先后关系比最终的 `on/off` 更有诊断价值。上电停在 Power Good 之前，问题多在电源开关或供电；Power Good 已成立而 MMIO 超时，则转查 Isolation、Clock、Reset 和互联。

下电正确性的证明来自事务计数，而不是固定延时。驱动先阻止新请求，再等待设备 Idle、DMA Queue Empty 和 NoC Outstanding 归零；随后才能隔离并断电。如果硬件没有可读的排空状态，架构本身就缺少可靠低功耗控制所需的可观测性。

Retention 也需要实测。选取文档声称会保持的寄存器写入特征值，执行完整掉电/上电周期，再比较恢复值；对不保持的寄存器则验证驱动确实重写。不同芯片 Revision 可能改变保持集合，因此保存恢复表必须带版本条件。

最后确认异常路径：启动代码应在任何可能清除 Sticky 位的初始化之前保存 Reset Cause；调试器访问关电域时，互联应返回可诊断错误或由 Timeout Monitor 终止事务。若一次调试读操作能无限阻塞系统，总线错误处理设计仍不完整。
