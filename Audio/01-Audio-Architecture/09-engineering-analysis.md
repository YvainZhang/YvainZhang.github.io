# 09 全链路时延与总线开销推演

## 1. 硬件解决什么问题：微秒级声学系统延迟精准分解

在专业录音返听（Live Monitoring）、主动降噪（ANC）以及云游戏/空间交互系统中，系统端到端**声学时延（Acoustic Latency）**是核心竞争指标。

当人说话时，如果自己的耳机返听声音延迟超过 $15\text{ ms}$，大脑就会产生强烈的回音错觉和言语交谈障碍；而在 ANC 主动降噪中，环路总时延甚至必须压低至 **$10\mu\text{s}$ 以内**。

---

## 2. 全链路时延逐级数学推导

```mermaid
graph LR
    P_IN["声波入麦"] -->|t_air1| MIC["MEMS 麦克风"]
    MIC -->|t_analog| AFE["模拟低通/PGA"]
    AFE -->|t_mod| ADC["Sigma-Delta 调制器"]
    ADC -->|t_dec| CIC["数字抽取滤波 (CIC)"]
    CIC -->|t_fifo| FIFO_RX["RX FIFO 缓冲"]
    FIFO_RX -->|t_dma| RAM["系统内存 / DSP TCM"]
    RAM -->|t_dsp| DSP["DSP 声学前处理算法"]
    DSP -->|t_fifo_tx| FIFO_TX["TX FIFO 缓冲"]
    FIFO_TX -->|t_int| DAC_INT["数字内插插值滤波"]
    DAC_INT -->|t_dac| DAC["Sigma-Delta DAC"]
    DAC -->|t_pa| PA["Class-D 放大器"]
    PA -->|t_air2| EAR["扬声器出声入耳"]
```

### 1. 模拟前端与换能器时延 ($t_{\text{transducer}}$)
- 模拟声波在空气中传播时延：$t_{\text{air}} = \frac{d}{c} = \frac{0.02\text{ m}}{343\text{ m/s}} \approx 58.3\mu\text{s}$（距离 $2\text{cm}$ 时）。
- MEMS 振膜机械响应与模拟放大器群延迟通常 $< 5\mu\text{s}$，在毫秒级系统中可忽略不计。

### 2. 数字抽取与插值滤波器群延迟 ($t_{\text{filter}}$)
线性相位 FIR 数字滤波器的群延迟（Group Delay）严格等于滤波器抽头数（Taps）的一半：
$$\tau_g = \frac{N - 1}{2 \cdot f_{\text{in}}}$$
对于典型的 5 阶 CIC 抽取滤波器加两级半带滤波器（Half-Band Filter）：
- 设过采样率 $\text{OSR} = 64$，输入调制时钟 $f_{\text{mod}} = 3.072\text{ MHz}$，输出采样率 $f_s = 48\text{ kHz}$。
- 硬件抽取滤波器典型总群延迟为 **$28 \sim 36$ 个输出样点周期**：
$$t_{\text{decimation}} = \frac{32}{48000\text{ Hz}} \approx 666.7\mu\text{s}$$
同理，DAC 端的升采样插值滤波器群延迟约为：
$$t_{\text{interpolation}} \approx 666.7\mu\text{s}$$

### 3. DSP 算法处理帧时延 ($t_{\text{dsp}}$)
现代音频算法（如频域 AEC、波束成形）通常基于短时傅里叶变换（STFT），需要攒够一帧（Frame）数据才能启动 FFT：
- 设帧长 $N_{\text{frame}} = 128$ 样点，步长（Hop Size）为 64 样点（$50\%$ 重叠）：
$$t_{\text{frame}} = \frac{128}{48000} \approx 2.67\text{ ms}$$
- DSP 计算流水线（计算完成消耗时间）约为半个帧长：$1.33\text{ ms}$。

### 4. DMA 环形缓冲区时延 ($t_{\text{buffer}}$)
ALSA 系统中的缓冲区时延由 Period Size 决定。若设置 `period_size = 128`：
$$t_{\text{dma}} = \frac{\text{period\_size}}{f_s} = \frac{128}{48000} \approx 2.67\text{ ms}$$

---

## 3. 全链路延迟汇总推演表

| 信号处理环节 | 时延产生物理机理 | 48kHz 标准配置延迟 | 96kHz 超低延迟优化配置 |
| :--- | :--- | :--- | :--- |
| **ADC 抽取滤波** | 数字 CIC + 半带滤波器群延迟 | $0.67\text{ ms}$ | $0.33\text{ ms}$ |
| **RX DMA 缓冲** | 硬件等待装满一个 Period | $2.67\text{ ms}$ (128点) | $0.67\text{ ms}$ (64点) |
| **DSP 声学算法** | STFT 帧长与 FFT 运算窗口 | $2.67\text{ ms}$ (时域直通可降至0) | $0.50\text{ ms}$ (时域自适应) |
| **TX DMA 缓冲** | 下行防饥饿最小安全缓冲 | $2.67\text{ ms}$ | $0.67\text{ ms}$ |
| **DAC 插值滤波** | 数字升采样滤波群延迟 | $0.67\text{ ms}$ | $0.33\text{ ms}$ |
| **模拟功放与扬声器**| LC 滤波与机械振动响应 | $0.05\text{ ms}$ | $0.05\text{ ms}$ |
| **系统总延迟汇总** | $\sum t_i$ | **9.40 ms** | **2.55 ms** |

---

## 4. 工程结论与设计折中

从推导可知：
1. **采样率翻倍是压低滤波器群延迟最直接的硬件手段**：将基带采样率由 48kHz 提升至 96kHz，数字滤波器的绝对群延迟直接减半。
2. **时域算法优于频域算法**：在极低延迟场景（如游戏耳机或返听耳机），应尽可能采用时域 LMS/IIR 滤波器替代 STFT 频域计算，将算法等待时延降为 0。
