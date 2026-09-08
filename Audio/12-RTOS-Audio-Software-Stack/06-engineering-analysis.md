# 06 工程推演与量化模型 (RTOS Audio Engineering Analysis)

## 1. 资源受限 RTOS 嵌入式内存预算数学推导

在无虚拟内存的嵌入式系统（SRAM 容量 $M_{\text{total}} = 384\text{ KB}$）中，系统稳定运行的充分必要条件为：所有并发任务的峰值静态栈、动态堆、DMA 硬件独占区与系统协议栈总和严格小于物理上限，且预留安全防护边限（Margin $\ge 15\%$）：

$$M_{\text{total}} \ge \sum_{i=1}^{N} \text{Stack}_i + M_{\text{WiFi\_Stack}} + M_{\text{DMA\_Ring}} + M_{\text{Audio\_Heap}} + M_{\text{OS\_Kernel}} + M_{\text{Margin}}$$

### 1.1 音频任务栈深度安全推导（Watermark Analysis）
音频解码（如 MP3 / AAC）通常包含深层次函数嵌套与递归反量化。
* 若任务栈深度配置为 $S_{\text{task}}$，函数调用栈深为 $D_{\text{call}}$，中断嵌套开销为 $S_{\text{ISR}}$：
  $$S_{\text{task}} \ge \max(D_{\text{call}}) + S_{\text{ISR}} + S_{\text{local\_arrays}}$$
* 在 RISC-V 32 位系统（32 个 GPR，中断压栈 16 个寄存器 = 64 字节）中，若解码器使用栈上大数组（如 `int32_t work_buf[1024]` = 4KB），极易导致栈溢出（Stack Overflow）。
* **工程设计法则**：严禁在音频解码函数栈上声明大于 128 字节的局部数组，所有临时运算暂存区必须分配在片内静态 `.sram.bss` 中，将音频任务栈从 16KB 稳定压减到 **4KB**。

---

## 2. DMA 周期尺寸（Period Size）与中断开销推演

设音频采样率为 $f_s = 48000\text{ Hz}$，声道数为 $C = 2$，采样位深为 $B = 16\text{ bits} = 2\text{ Bytes}$。
每秒产生的数据字节率为：
$$R_{\text{byte}} = f_s \times C \times B = 48000 \times 2 \times 2 = 192,000\text{ B/s} = 187.5\text{ KB/s}$$

若底层 DMA 的一个传输周期尺寸设置为 $P_{\text{size}}$（单位：Frames），则每秒产生的硬件中断频率为：
$$f_{\text{irq}} = \frac{f_s}{P_{\text{size}}}$$

每次中断服务程序（ISR）触发，伴随现场保存（Context Save）、清中断标志、释放信号量（`xSemaphoreGiveFromISR`）和 RTOS 任务上下文切换（Task Context Switch），平均耗费时钟周期 $T_{\text{ctx}} \approx 1200\text{ Cycles}$。在 CPU 主频 $f_{\text{cpu}} = 160\text{ MHz}$ 下：
$$\text{CPU Overhead} = \frac{f_{\text{irq}} \times T_{\text{ctx}}}{f_{\text{cpu}}} \times 100\%$$

### 周期尺寸与系统性能权衡曲线

| 周期配置 $P_{\text{size}}$ (Frames) | 单周期时间 $T_{\text{period}}$ (ms) | 中断频率 $f_{\text{irq}}$ (Hz) | 单周期数据量 (Bytes) | 纯中断 CPU 开销 | 硬件抖动容限 (Jitter Tolerance) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **64** | $1.33\text{ ms}$ | $750\text{ Hz}$ | $256\text{ B}$ | $0.56\%$ | 极低（易受 WiFi 突发打断） |
| **128** | $2.67\text{ ms}$ | $375\text{ Hz}$ | $512\text{ B}$ | $0.28\%$ | 较低 |
| **256** | $5.33\text{ ms}$ | $187.5\text{ Hz}$ | $1024\text{ B}$ | $0.14\%$ | **工业推荐最佳平衡点** |
| **512** | $10.67\text{ ms}$ | $93.75\text{ Hz}$ | $2048\text{ B}$ | $0.07\%$ | 极高（但端到端时延增加） |

---

## 3. PSRAM 突发访问延迟与 Cache Miss 惩罚推导

在搭载片外 SPI/QSPI PSRAM 的芯片中，若将关键音频解码表置于 PSRAM，需评估 Cache 命中率对解码实时性的影响。

* 片内 SRAM 读取延迟：$T_{\text{SRAM}} = 1\text{ cycle} \approx 6.25\text{ ns}$（以 160MHz 计）。
* 片外 QSPI PSRAM（80MHz 4-bit 模式）：
  * 发送读命令与 24-bit 地址：32 cycles = $400\text{ ns}$；
  * 等待 Dummy Cycles：6 cycles = $75\text{ ns}$；
  * 传输 32 字节 Cache Line：64 cycles = $800\text{ ns}$；
  * 单次 Cache Miss 总惩罚时间：$T_{\text{miss}} \approx 1275\text{ ns} \approx 204\text{ CPU Cycles}$。

### 实时性约束条件
若一个 MP3 帧（1152 采样点，对应播放时间 $T_{\text{frame}} = 26.12\text{ ms}$）包含 $K = 5000$ 次离散查表操作：
* **全 SRAM 模式（100% 命中）**：
  $$T_{\text{lookup}} = 5000 \times 6.25\text{ ns} = 0.031\text{ ms}$$
* **全 PSRAM 模式（假设 Cache 命中率仅 80%，产生 1000 次 Miss）**：
  $$T_{\text{lookup}} = 4000 \times 6.25\text{ ns} + 1000 \times 1275\text{ ns} = 1.30\text{ ms}$$
查表耗时飙升 **41 倍**。一旦 Cache 频繁失效，解码单帧耗时将突破 $26.12\text{ ms}$ 上限，直接导致扬声器输出断流爆音。这从数学上证明了：**将解码高频热点表强制锁定在片内 SRAM 是保障实时性的绝对刚性要求**。
