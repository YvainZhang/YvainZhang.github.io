# 全链路案例 1：TWS 降噪耳机端到端软硬件与声学系统设计

## 1. 案例目标与系统指标体系

本案例复盘一款旗舰级真无线主动降噪耳机（TWS ANC Earbuds）的完整芯片与系统工程实现：
- **声学性能**：降噪深度达到 **$42\text{ dB}$**，降噪频宽覆盖 $50\text{ Hz} \sim 3.5\text{ kHz}$；
- **整机延迟**：端到端音频传输延迟控制在 **$< 35\text{ ms}$**（基于 BLE Audio LC3）；
- **电池续航**：单耳 $45\text{ mAh}$ 纽扣电池，在开启 ANC + 音乐连续播放下续航达到 **$7.5\text{ 小时}$**。

---

## 2. 全链路系统架构 Block Diagram

```mermaid
graph TB
    subgraph Acoustic_Chamber["物理声学与传感器腔体"]
        FF_MIC["前馈数字麦克风 (Feedforward PDM)"]
        FB_MIC["反馈数字麦克风 (Feedback PDM)"]
        TALK_MIC["骨传导/通话麦克风 (Voice Mic)"]
        SPEAKER["11mm 动圈扬声器单元 (16 欧姆)"]
    end

    subgraph Audio_SoC["高集成度 TWS 音频主控 SoC (22nm ULP)"]
        direction TB
        subgraph Power_Domain_AON["常开 AON 域"]
            PMU["电源管理单元 / 触摸入耳检测状态机"]
        end

        subgraph ANC_Hardware_Core["微秒级硬线 ANC 协处理器"]
            ANC_IIR["双通道前馈/反馈超低延迟 IIR 滤波引擎 (768kHz)"]
        end

        subgraph Audio_DSP_Core["算法 DSP 核心 (HiFi 4 @ 160MHz)"]
            ALG_ENC["通话降噪 ENC (三麦波束成形 + AI-NS)"]
            ALG_SPATIAL["双耳空间音频 3D 渲染器"]
            ALG_EQ["动态低音补偿与自适应 EQ"]
        end

        subgraph RF_Subsystem["低功耗蓝牙射频子系统"]
            BLE_MODEM["2.4GHz BLE 5.3 射频 + LC3 硬件编解码器"]
        end

        subgraph Audio_Codec_Block["片上高保真模拟 Codec"]
            DAC_HP["Class-G / True Ground 超低底噪耳放 (< 1.5uVrms)"]
        end
    end

    FF_MIC --> ANC_IIR
    FB_MIC --> ANC_IIR
    TALK_MIC --> ALG_ENC

    BLE_MODEM --> ALG_SPATIAL
    ALG_SPATIAL --> ALG_EQ

    ANC_IIR --> DAC_HP
    ALG_EQ --> DAC_HP
    DAC_HP --> SPEAKER
```

---

## 3. 核心技术攻坚点：下行音乐补偿与 ANC 叠加防削波

当耳机同时开启强力降噪并播放大音量重低音摇滚乐时：
- 反馈降噪回路会把音乐中的超低音也误当做耳道内的“低频噪声”进行反向相消！
- **解决方案**：在 DSP 内部建立**音乐自抵消补偿滤波器（Music Cancellation Filter）**，将音乐信号预先进行声学传递函数建模，从反馈麦克风采样中扣除，使得降噪环路“对音乐视而不见”。
- **防削波策略**：反相声波与大音量音乐在 DAC 端叠加可能突破 $0\text{ dBFS}$ 满量程。必须配备片上微秒级前瞻限幅器（Look-ahead Limiter），在不产生爆音的前提下平滑压低增益。
