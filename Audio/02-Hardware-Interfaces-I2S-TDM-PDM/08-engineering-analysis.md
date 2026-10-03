# 08 TDM 时钟抖动与带宽极限推演

## 1. 硬件解决什么问题：多通道物理传输的建立保持时序容限模型

在车载音频总线和高端多通道音频处理器设计中，多路 TDM 声道集中在单根物理线上传输。随着通道数激增（如 16 或 32 声道）与高采样率普及，位时钟 BCLK 的频率持续推高。

当总线速率达到数十兆赫兹时，**时钟抖动（Clock Jitter）、PCB 走线延时及发送端时钟到输出延迟**会减少接收端的建立/保持裕量。下面用一组参数计算时序预算。

---

## 2. 建立时间与保持时间数学模型

```mermaid
graph LR
    subgraph Master_TX["发送端 (Master TX)"]
        CLK_OUT["时钟输出 (BCLK)"]
        DATA_OUT["数据输出 (SDATA)"]
    end

    subgraph Delay_Model["PCB 物理传输延迟"]
        T_prop_clk["时钟走线延时 t_flight_clk"]
        T_prop_data["数据走线延时 t_flight_data"]
    end

    subgraph Slave_RX["接收端 (Slave RX)"]
        FF["接收触发器锁存 (Flip-Flop)"]
    end

    CLK_OUT --> T_prop_clk --> FF
    DATA_OUT --> T_prop_data --> FF
```

### 关键时序参数定义
- $T_{\text{BCLK}}$：位时钟完整周期；
- $t_{\text{co, max}}$：发送芯片时钟有效沿到数据稳定输出的最大延迟；
- $t_{\text{co, min}}$：发送芯片时钟有效沿到数据开始变化的最早保持时间；
- $t_{\text{setup}}$：接收芯片触发器所需的最小建立时间；
- $t_{\text{hold}}$：接收芯片触发器所需的最小保持时间；
- $t_{\text{skew}}$：数据线与时钟线由于 PCB 长度不均导致的飞行时间偏差：$t_{\text{skew}} = |t_{\text{flight, data}} - t_{\text{flight, clk}}|$；
- $t_{\text{jitter}}$：时钟信号峰峰值周期抖动（Peak-to-Peak Jitter）。

---

## 3. 建立保持时间边界方程式

以下按数据发出到采样之间有一个完整 BCLK 周期的模型列出建立/保持约束。若器件在相反边沿发出与采样数据，应按对应边沿间隔和占空比重新计算。满足预算也不代表亚稳态风险为零，还需覆盖器件、电压、温度与测得的抖动范围。

### 1. 建立时间裕量不等式（Setup Margin）
$$T_{\text{BCLK}} \ge t_{\text{co, max}} + t_{\text{setup}} + t_{\text{skew}} + t_{\text{jitter}} + M_{\text{setup}}$$
其中 $M_{\text{setup}}$ 为工程设计安全裕量，本例取目标 $M_{\text{setup}} \ge 2.0\text{ ns}$。

### 2. 保持时间裕量不等式（Hold Margin）
$$t_{\text{co, min}} - t_{\text{skew}} - t_{\text{jitter}} \ge t_{\text{hold}} + M_{\text{hold}}$$

---

## 4. 极限工况参数代入推演

考虑一个严苛的车载 TDM-16 系统（16 声道、96kHz 采样率、单槽位 32-bit）：
$$f_{\text{BCLK}} = 16 \times 32 \times 96000 = 49.152\text{ MHz}$$
位时钟周期为：
$$T_{\text{BCLK}} = \frac{1}{49.152\text{ MHz}} \approx 20.345\text{ ns}$$
取以下示例参数；实际设计应从目标 Codec 数据手册获取相应边沿和工况的时序限值：
- $t_{\text{co, max}} = 11.5\text{ ns}$；$t_{\text{co, min}} = 3.0\text{ ns}$；
- $t_{\text{setup}} = 4.0\text{ ns}$；$t_{\text{hold}} = 2.0\text{ ns}$；
- 设 PCB 严格等长，走线偏差 $< 5\text{ mm}$，故 $t_{\text{skew}} \approx 0.03\text{ ns}$；
- 设时钟源抖动 $t_{\text{jitter}} = 1.2\text{ ns}$。

### 求解建立时间裕量：
$$M_{\text{setup}} = 20.345 - (11.5 + 4.0 + 0.03 + 1.2) = 20.345 - 16.73 = \mathbf{3.615\text{ ns}}$$
**结论**：建立时间裕量为 $3.615\text{ ns} > 2.0\text{ ns}$，满足本例的建立时间目标。但按同一组参数，保持时间余量为 $3.0-0.03-1.2-2.0=-0.23\text{ ns}$，尚未满足保持约束，不能据此判定整个接口时序收敛。

### 求解系统支持的最高物理极限通道数：
当保持 $M_{\text{setup}} = 2.0\text{ ns}$ 时，所允许的最小 $T_{\text{BCLK}}$ 为：
$$T_{\text{BCLK, min}} = 16.73 + 2.0 = 18.73\text{ ns} \implies f_{\text{BCLK, max}} \approx 53.39\text{ MHz}$$
若试图在 96kHz 下扩展到 32 通道，其理论时钟将需要：
$$f_{\text{BCLK}} = 32 \times 32 \times 96000 = 98.304\text{ MHz} \implies T_{\text{BCLK}} = 10.17\text{ ns}$$
由于 $10.17\text{ ns} < 18.73\text{ ns}$，建立时间发生极其严重的 **-8.56 ns 负裕量时序违规**。

---

## 5. 架构指导准则

推论：**在本例的时序参数与完整周期模型下，16 声道 @ 96kHz 满足建立时间预算，32 声道 @ 96kHz 超出该预算**。这不是所有单端 TDM 接口的统一通道上限，保持时间问题也仍需处理。
若目标器件与板级时序不能支持所需通道数，可评估：
1. 采用**多数据线 TDM 并行（Multi-line TDM / TDM-x4）**；
2. 升级为差分高速网络总线（如 **ADI A2B 汽车音频总线** 或以太网 **AVB/TSN**）。
