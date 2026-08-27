# 地址流、数据流、控制流与中断流

## 1. 为什么要按“流”分析

只看静态模块列表无法解释系统行为。同一个外设通常有独立的配置路径、数据路径和中断路径，并共享 Clock/Reset/Power 依赖。故障定位的核心是判断哪一条流断了。

本章用六种流描述系统：

1. 指令流。
2. 地址/事务流。
3. 数据流。
4. 控制流。
5. 中断流。
6. 时钟、复位和电源依赖流。

## 2. CPU 读取 DDR 变量

假设程序执行 `value = *ptr`，且 `ptr` 指向普通可缓存内存。

### 2.1 指令流

CPU 首先要取得执行这条 Load 指令本身：

```text
PC/VA
→ Instruction TLB
→ L1 I-Cache
→ L2/System Cache（若 Miss）
→ NoC
→ DDR Controller/PHY（若继续 Miss）
```

### 2.2 数据地址流

Load 指令计算出 VA，MMU/TLB 将其转换为 PA，并检查权限和内存属性。TLB Miss 时还会由硬件或软件执行 Page Table Walk，而页表项本身也保存在内存层次中。

### 2.3 数据流

数据若命中 L1 D-Cache，访问很快结束；若 Miss，则请求向 L2、System Cache、NoC 和 DDR 传播，返回的 Cache Line 被填充后，CPU 取出所需字节。

### 2.4 可能的停顿点

- TLB Miss 或 Page Fault。
- Cache Miss、MSHR/Fill Buffer 已满。
- NoC 仲裁或 Backpressure。
- DDR Bank 冲突、Refresh 或低功耗退出。
- ECC 错误。

“Load 很慢”不等同于“DDR 很慢”，必须沿全路径测量。

## 3. CPU 写 MMIO 寄存器

假设 CPU 启动 DMA：

```text
CPU Store 指令
→ MMU 将 VA 转为设备寄存器 PA
→ Store Buffer/内存顺序约束
→ AXI/NoC
→ Peripheral Bridge
→ DMA Register Bank
→ 写入 Doorbell/Start 位
→ DMA 状态机启动
```

关键差异：

- MMIO 必须使用适合设备的内存属性。
- 写入可能在 CPU 指令退休后才真正到达设备。
- Start/Doorbell 之前写入内存中的 Descriptor 必须先对设备可见。
- 某些寄存器写入后需读回或轮询状态，确保跨 Bridge 生效。

## 4. DMA 从外设接收数据

以 Ethernet RX 为例：

### 4.1 配置流

```text
CPU
→ 配置 Clock/Reset/Pinmux/PHY
→ 分配 RX Buffer 和 Descriptor Ring
→ 将 Buffer 的 DMA 地址写入 Descriptor
→ 同步 Descriptor/Buffer 所有权
→ 配置 DMA Ring Base
→ 使能 MAC、DMA 和中断
```

### 4.2 数据流

```text
外部信号
→ PHY
→ MAC
→ RX FIFO
→ 设备 DMA Initiator
→ IOMMU/SMMU（若存在）
→ NoC
→ DDR Controller
→ DDR Buffer
```

### 4.3 完成与中断流

```text
DMA 更新 Descriptor 状态
→ 设备置 Interrupt Status
→ 中断控制器记录 Pending
→ 路由到某 CPU
→ CPU 进入异常向量
→ 驱动读取状态并处理完成项
→ 同步 Buffer 所有权
→ 协议栈消费数据
→ 驱动补充 Buffer
```

### 4.4 三种常见“半通”状态

- 寄存器可配置但没有数据：配置流通，PHY/数据/DMA 流可能断。
- DDR 中有数据但没有 ISR：数据流通，中断状态、Mask、路由或 CPU 侧可能断。
- ISR 到达但 CPU 看见旧数据：中断流通，Cache 一致性或内存顺序可能错误。

## 5. UART 接收字符

UART 不使用 DMA 时：

```text
Pad → Pinmux → UART RX Sampler → RX FIFO
→ IRQ Line → Interrupt Controller → CPU
→ ISR 读取 UART_DATA → 软件 Ring Buffer
```

依赖流：

```text
Power Domain
→ Bus/Core Clock
→ Reset Release
→ Pinmux/Pad 电气属性
→ Baud Divider
```

如果 RX 状态位变化但 CPU 无中断，应优先检查 UART Interrupt Mask、原始/屏蔽状态、中断触发类型、控制器路由及 CPU 屏蔽位；如果 RX 状态完全不变，则优先检查 Pinmux、输入 Pad、Clock 和波特率。

## 6. CPU 异常流

CPU 访问非法地址时可能发生：

```text
Load/Store
→ MMU 权限或翻译检查
→ 若通过则发往 NoC
→ NoC/Target 返回错误
→ CPU 将错误转换为同步异常
→ 保存异常返回地址和状态
→ 跳转异常向量
→ OS 记录 Fault Address/Status
→ 修复、终止进程或 Panic
```

要区分异常发生在 MMU 翻译阶段还是外部总线阶段。前者多检查页表，后者多检查 Address Map、Clock/Reset/Power 和 Firewall。

## 7. Boot 控制流

一个简化启动链：

```text
POR/Reset
→ CPU 从规定地址取指
→ BootROM 读取 Strap/Fuse
→ 选择启动介质并验证第一阶段镜像
→ SPL 在片上 SRAM 运行
→ 配置 Clock/Pinmux/DDR
→ 将下一阶段加载到 DDR
→ 安全固件配置异常级和安全边界
→ Bootloader 加载 Kernel/DTB
→ Kernel 建立 MMU、内存和驱动模型
→ 启动用户空间
```

启动早期 DDR 尚不可用，代码、栈和数据必须位于 BootROM、SRAM 或处理器特殊存储中。DDR 初始化成功是系统从“芯片”走向“复杂软件平台”的关键边界。

## 8. 怎样把“设备不工作”缩小到一段路径

有效的故障树从最靠近 CPU 的已知点向外推进。每一步都要找一个能把路径分成前后两半的观察点，而不是一次读取几十个寄存器。

### 8.1 先证明配置通路可达

从模块的只读 ID、Version 或具有稳定复位值的寄存器开始。若访问直接触发 CPU Abort，应读取 Fault Address 和 Fault Status：翻译或权限 Fault 发生在 MMU 一侧，External Abort 则说明请求已经越过 MMU，问题更接近互联或 Target。若访问不异常却超时，按顺序检查 Address Map、Firewall、Power Good、Bus Clock 和 Reset。

只读回零并不能证明可达。默认错误 Target、掉电域的隔离钳位和真正的复位值都可能是零。更可靠的方法是读取两个具有不同固定值的寄存器，或对一个无副作用的 RW 字段写入特征值并读回。

### 8.2 再证明模块具备运行条件

MMIO 可达之后，核对 Power、功能 Clock、Reset、Pinmux 和 PHY。这里要利用现象区分层次：核心 Clock 未开时，Enable 位可能可以写入，但 Busy/FIFO 指针永远不动；Pinmux 错误时，内部 FIFO 和状态机会工作，封装引脚却没有波形；PHY 未锁定时，Controller 往往会给出独立的 Link/PLL 错误。

### 8.3 找到数据停止移动的位置

数据路径上的 FIFO Level、Descriptor Consumer Index、DMA Active、NoC Transaction Counter 和 DDR Write Counter 是一系列观察点。以接收路径为例：外设 RX Counter 增长而 FIFO 不变，问题在协议接收或过滤；FIFO 增长而 DMA Index 不动，问题在 DMA 配置；DMA Index 前进而 DDR Counter 不变，检查 SMMU、Firewall 和 NoC；DDR 已被写入而上层没有数据，则转向一致性、Descriptor 和软件队列。

这种定位方法的价值在于，每个计数器都给出一个边界。计数器本身不能说明根因，但能排除边界之前已经正常的环节。

### 8.4 把中断路径单独验证

先读设备 Raw Interrupt Status。Raw 位未置位，说明设备尚未满足中断条件；Raw 已置位而 Masked Status 未置位，说明设备内部 Mask 或 Enable 配错；设备 Masked Status 有效而 GIC/PLIC 不 Pending，问题位于中断连线、触发类型或控制器配置；控制器已 Pending 而目标 CPU 不进 ISR，则检查路由、优先级、CPU 屏蔽位和当前异常级。

对于电平中断，设备状态在服务完成前通常必须保持有效。ISR 若只在控制器执行 EOI，却没有清除设备源，中断会立刻重新触发，形成中断风暴。边沿中断的风险相反：在控制器尚未启用时出现的短脉冲，若中间没有锁存，可能永久丢失。

### 8.5 最后检查软件是否正确消费结果

ISR 到达只证明通知路径工作。驱动还要按协议读取完成状态、转换 Descriptor 所有权、执行 DMA 同步，并将数据交给上层。若硬件 Producer Index 增长而软件 Consumer Index 不动，查看驱动循环退出条件；若两者都增长而业务仍无数据，检查上层队列和过滤逻辑。对于共享内存，再验证 Barrier 是否把“先写数据、后发布状态”的顺序传递到了观察者。

最终的故障记录应写成结论，例如“DMA 已消费 Descriptor，但 SMMU 在 IOVA `0x...` 报 Translation Fault”，而不是“检查过 DMA、SMMU 和内存”。前一种记录给出了故障边界，后一种没有。

## 9. 一张实用的系统路径记录表

| 维度 | 内容示例 |
| --- | --- |
| Initiator | Ethernet DMA，Stream ID 0x21 |
| 地址 | IOVA `0x8200_0000`，转换至 PA `0x4A00_0000` |
| 路径 | MAC → SMMU → NoC → DDRC0 |
| 属性 | Non-secure、Write、Outer Shareable |
| 一致性 | 非一致，需要 DMA API 同步 |
| Clock | MAC 250 MHz、AXI 400 MHz、PHY Ref 125 MHz |
| Reset | MAC、DMA、PHY 三路 Reset |
| Power | PD_NET，可独立关断 |
| 中断 | SPI 96，Level-high，Affinity CPU2 |
| 观察点 | DMA Status、SMMU Fault、NoC Counter、IRQ Pending |

对复杂问题填完这张表，往往就能暴露缺失的配置或错误假设。
