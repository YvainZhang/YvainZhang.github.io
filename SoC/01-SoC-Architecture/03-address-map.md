# Address Map 与地址译码

## 1. Address Map 解决什么问题

Address Map 定义某个地址空间中，每段地址由哪个硬件 Target 响应。CPU 执行 Load/Store，DMA 读取 Descriptor，调试器查看寄存器，本质上都会形成带地址的总线事务。互联根据地址和事务属性选择路径，最终由目标内存或外设完成访问。

地址表至少应描述：

- Base Address 和 Size/End Address。
- 对应 Target 或用途。
- 读、写、执行权限。
- 安全与特权属性。
- 推荐的内存类型和 Cache 属性。
- 哪些 Initiator 可见。
- 是否存在 Alias、Remap、窗口或保留洞。

## 2. 常见地址类型

### 2.1 Virtual Address（VA）

CPU 指令直接使用的地址。启用 MMU 后，VA 经页表转换为物理地址。不同进程可以用相同 VA 映射不同物理页。

### 2.2 Intermediate Physical Address（IPA）

虚拟化环境中，Guest 的 Stage-1 页表将 VA 转为 IPA，再由 Hypervisor 控制的 Stage-2 页表转为最终 PA。

### 2.3 Physical Address（PA）

处理器体系结构所定义的物理地址。PA 宽度不一定等于指针宽度，例如 64 位 CPU 可能只实现较少的物理地址位。

### 2.4 Bus Address

互联或设备端实际使用的地址视图。某些简单 SoC 中它等于 CPU PA；在存在别名、地址偏移、窗口或桥接时可能不同。

### 2.5 DMA/I/O Virtual Address（IOVA）

设备 DMA 使用的地址。若设备位于 IOMMU/SMMU 后，IOVA 通过 I/O 页表转换为 PA；若没有 IOMMU，还可能受设备地址位宽和总线映射影响。驱动不得默认虚拟地址、CPU PA 和 DMA 地址数值相同。

## 3. 一份教学用地址表

以下地址完全是示例：

| 起始地址 | 结束地址 | 大小 | 区域 | 建议类型 | 备注 |
| --- | --- | ---: | --- | --- | --- |
| `0x0000_0000` | `0x0003_FFFF` | 256 KiB | BootROM | Normal, RO | 复位取指或映射别名 |
| `0x0010_0000` | `0x001F_FFFF` | 1 MiB | SRAM | Normal, Cacheable | 启动及共享内存 |
| `0x1000_0000` | `0x1000_FFFF` | 64 KiB | System Control | Device | Clock/Reset/Pinmux |
| `0x1100_0000` | `0x110F_FFFF` | 1 MiB | APB Peripherals | Device | UART/SPI/I2C/GPIO |
| `0x2000_0000` | `0x2FFF_FFFF` | 256 MiB | PCIe MMIO Window | Device | 映射 Endpoint BAR |
| `0x4000_0000` | `0xBFFF_FFFF` | 2 GiB | DDR Low Window | Normal, Cacheable | CPU/多数 DMA 可见 |
| `0x1_0000_0000` | `0x1_7FFF_FFFF` | 2 GiB | DDR High Window | Normal, Cacheable | 仅支持 64 位地址的主设备可见 |

计算区域大小时使用：

```text
Size = End - Start + 1
```

地址区间通常按 2 的幂和窗口边界对齐，以简化译码，但这不是绝对要求。

## 4. 地址译码

互联可用高位匹配选择 Target。例如：

```text
if address in 0x1000_0000..0x1000_FFFF → System Controller
if address in 0x1100_0000..0x110F_FFFF → APB Bridge
if address in 0x4000_0000..0xBFFF_FFFF → DDR Controller
otherwise                              → Default Error Target
```

进入 APB Bridge 后还会进行第二级译码：

```text
0x1100_0000..0x1100_0FFF → UART0
0x1100_1000..0x1100_1FFF → UART1
0x1100_2000..0x1100_2FFF → SPI0
```

因此，访问 `0x1100_1024` 可被拆成：

- 顶层窗口：APB Peripheral 区域。
- 子模块：UART1。
- 寄存器偏移：`0x24`。

## 5. Register Map 与 Address Map 的关系

Address Map 把一个窗口分配给 IP；Register Map 定义窗口内部每个偏移的含义：

```text
UART0 Base = 0x1100_0000
UART_DATA Offset = 0x00
UART_STATUS Offset = 0x18

UART_STATUS Address = Base + Offset = 0x1100_0018
```

寄存器字段还需要说明：

- `RO`、`WO`、`RW`。
- `W1C`：写 1 清零。
- `W1S`：写 1 置位。
- Read-to-Clear。
- Self-clearing。
- Reserved 位必须写入什么值。
- Reset Value 以及属于哪个 Reset Domain。

错误地对 W1C 寄存器执行普通“读-改-写”，可能意外清除其他状态位。

## 6. Memory 与 MMIO 的根本区别

DDR/SRAM 用于保存普通数据，适合 Cache、合并和推测访问；MMIO 寄存器代表设备状态或命令，读写可能有副作用，不能按普通内存随意优化。

MMIO 映射通常应具有 Device/Non-cacheable 等合适属性，以限制：

- 推测读取。
- 写合并或长时间滞留在 Cache。
- 不允许的访问重排。
- 不符合设备要求的访问宽度。

仅使用 C 语言 `volatile` 不能完整解决 CPU 内存属性、硬件重排和跨核同步问题。操作系统驱动应使用平台提供的 I/O 映射与访问 API。

## 7. Alignment、Access Width 与 Byte Lane

外设可能只允许 8、16、32 或 64 位访问；也可能要求地址自然对齐。例如 32 位访问的地址通常应满足低两位为 0。

不对齐访问的结果取决于体系结构和目标：

- CPU 自动拆成多个总线访问。
- 触发 Alignment Fault。
- 互联或外设返回错误。
- 对带副作用寄存器产生不可接受的多次操作。

写寄存器时还需关注 Byte Enable/Write Strobe。对只支持 32 位整字写的寄存器进行字节写，可能被拒绝或产生不同结果。

## 8. Alias 与 Remap

### 8.1 Alias

同一物理资源在地址空间中出现多个入口。例如 SRAM 同时映射到低地址启动窗口和正常高地址窗口。它有利于启动，但也可能带来 Cache Alias 或软件混淆。

### 8.2 Boot Remap

复位时地址 0 可能指向 BootROM，BootROM 执行后通过 Remap 寄存器把地址 0 切换到 SRAM 或 DDR。切换前要确保当前执行流和异常向量不会因映射改变而失效，并按架构要求同步流水线和缓存。

### 8.3 Window/Aperture

当目标空间大于本地可分配窗口时，软件可通过窗口寄存器选择远端高位地址，再通过固定 Aperture 访问。例如 PCIe、调试和片上 SRAM Bank 常用这种方式。窗口切换需要锁或其他并发保护。

## 9. DDR 容量、地址位宽与空洞

DDR 物理容量不保证在 CPU PA 中形成一段连续区间，原因包括：

- 32 位低地址空间需要为 MMIO 保留窗口。
- 多通道 Interleave。
- 安全内存或固件保留区。
- 芯片仅实现部分地址线。
- 某些 Initiator 的 DMA Address Width 较小。

例如系统具有 4 GiB DDR，但低地址窗口只有 2 GiB，其余容量放在 4 GiB 以上。一个只有 32 位 DMA 地址能力的设备无法直接访问高端内存，需要 IOMMU、Bounce Buffer 或受限内存池。

## 10. 地址访问中的安全与权限

地址命中 Target 并不表示一定允许访问。事务还可能包含：

- Secure/Non-secure。
- Privileged/Unprivileged。
- Read/Write/Execute。
- Initiator ID、Stream ID。
- VMID/PASID 或保护域信息。

Firewall 可按地址范围和事务属性进行过滤。权限失败可能表现为同步异常、总线错误响应、设备 IOMMU Fault 或安全控制器告警。

## 11. 常见故障模式

### 11.1 DECERR 或 Decode Error

常见原因：地址没有映射、窗口配置错误、目标在当前产品中不存在，或高地址位被截断。

### 11.2 SLVERR 或 Slave Error

地址已到达目标附近，但 Target 拒绝或无法完成，例如非法访问宽度、模块仍在 Reset、访问了未实现寄存器或内部状态异常。不同互联实现对错误类型的映射可能不同。

### 11.3 总线超时

目标没有返回响应。常见原因包括 Clock 被 Gate、Power Domain 已关闭、Reset 未释放、CDC/Bridge 卡死或硬件缺陷。

### 11.4 读回全 0 或全 1

可能是真实复位值，也可能是默认错误 Target、未供电域的钳位值、读了保留地址或调试工具掩盖了错误响应。不能仅凭数值下结论。

### 11.5 CPU 正常但 DMA 失败

检查：DMA 地址是否经过正确转换、设备地址位宽、SMMU 映射、Firewall 的 Initiator 权限、Cache 一致性和保留内存位置。

## 12. 怎样审阅一份 Address Map

地址表审阅不是目测 Base Address 是否整齐，而是验证区间数学、硬件实现和软件描述三者一致。

先做区间检查。每个闭区间的大小按 `End - Start + 1` 计算，再按起始地址排序。若相邻两项满足 `previous_end >= next_start`，两段地址已经重叠。重叠不一定错误，Boot Alias 和 Overlay 可能是有意设计，但文档必须说明选择条件；没有说明的重叠通常意味着地址表合并时出了问题。窗口 Base 还应满足互联译码掩码要求。例如一个用高 16 位译码的 64 KiB 窗口，Base 的低 16 位应为零。

随后比较不同访问者的地址视图。CPU、DMA 和 Debug Port 可能通过不同入口接入 NoC。最直接的验证方法，是为同一块 SRAM 或 DDR 分别写出 CPU PA、设备 DMA Address 和调试器地址，再说明中间是否经过 Offset、Remap 或 IOMMU。如果文档只给出“系统物理地址”，却没有说明设备端口看到什么，这份地址表对驱动开发仍然不完整。

地址位宽必须逐个 Initiator 核对，而不是只看 CPU。假设 DDR 高端窗口从 `0x1_0000_0000` 开始，它至少需要 33 位地址。一个 `dma-mask = 32` 的设备不能产生该地址；把高地址截成低 32 位后，它可能静默破坏另一块内存。软件应通过 DMA Mask 约束分配，或使用 SMMU、低端内存池和 Bounce Buffer。

接着审阅内存属性。RAM 应在所有别名上保持兼容的 Normal Memory 属性；设备寄存器应映射为架构规定的 Device 类型。同一物理页若一个映射是 Write-back Cacheable，另一个是 Non-cacheable，CPU 可能通过两个映射观察到不同数据。属性问题通常不会在每次访问中稳定报错，因此比单纯的地址错误更难发现。

权限表要同时覆盖 Secure/Non-secure、读写执行和 Initiator 身份。对于 BootROM，“只读”还不够：还要说明非安全世界能否读、能否执行，以及生命周期进入量产状态后调试端口是否仍可见。安全控制器的复位默认值也应写入软件初始化约定，否则一个 Warm Reset 后可能沿用旧权限。

Alias 和 Remap 要写清生效时间。若复位时地址 0 指向 ROM，稍后切到 SRAM，应说明切换动作由谁完成、正在执行的代码位于哪里、异常向量何时迁移，以及切换后旧 Alias 是否继续存在。对于可缓存 Alias，还要说明如何避免同一物理 Cache Line 以不兼容属性出现。

最后做跨软件栈比对：RTL/集成地址表、Bootloader Header、Device Tree 的 `reg`、操作系统资源表和调试脚本应来自同一芯片版本。保留内存还要逐项核对安全固件、远端核、DMA Pool、Crash Dump 和 Trace Buffer；只在 Device Tree 中写一个 `reserved-memory` 节点，并不能阻止更早阶段的 Bootloader 覆盖它。

一份合格的审阅结果应包含三样东西：无歧义的区间表、按 Initiator 划分的地址视图，以及硬件与各阶段软件的差异报告。
