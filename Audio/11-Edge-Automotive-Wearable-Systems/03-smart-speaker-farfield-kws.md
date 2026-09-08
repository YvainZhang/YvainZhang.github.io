# 03 智能音箱远场拾音与端侧大模型

## 1. 硬件解决什么问题：在 5 米嘈杂客厅中听清主人微弱指令

智能音箱或语音助手面临最恶劣的声学拾音挑战：
1. **自身声学自激（Self-Sound Interference）**：音箱自己正在以 80dB SPL 的巨大音量播放摇滚乐，扬声器距离自带的麦克风仅有几厘米；
2. **远场微弱人声（Far-Field Attenuation）**：用户在 5 米开外的沙发上轻声说话，到达音箱麦克风处的声压级仅有 50dB SPL；
3. **房间复杂混响（Reverberation）**：声波在墙壁、地板之间经过数百次回弹反射。

此时自身播放的音乐强度是人声的 **1000 倍以上（信噪比 SNR 低至 -30dB）**！

---

## 2. 硬件微架构与组成：远场全双工声学交互拓扑

```mermaid
graph TD
    subgraph Acoustic_Hardware["多麦克风物理拾音阵列"]
        MIC_RING["环形 4 麦 / 6 麦数字阵列"] --> PDM_IF["PDM 高速多通道采集接口"]
        SPK_LOOPBACK["扬声器硬件直连回采通道 (Hardware Loopback)"] --> PDM_IF
    end

    subgraph Audio_DSP_Pipeline["专有音频 DSP (前处理加速引擎)"]
        PDM_IF --> MULTI_AEC["多通道超深回声消除器 (AEC: 压制自身音乐 > 45dB)"]
        MULTI_AEC --> BSS_BF["盲源分离与自适应波束成形 (BSS / MVDR)"]
        BSS_BF --> DEREVERB["声学去混响算法 (WPE / Dereverberation)"]
        DEREVERB --> CLEAN_OUT["提取出的纯净定向语音流"]
    end

    subgraph Edge_NPU_Engine["端侧 NPU / 大模型推理引擎"]
        CLEAN_OUT --> KWS_LOCAL["本地离线关键词唤醒 (Local KWS)"]
        KWS_LOCAL --> SLM["端侧轻量化语音大模型 (0.5B~2B Audio LLM)"]
        SLM --> CLOUD["云端全功能大模型 (Cloud ASR/LLM)"]
    end
```

---

## 3. 全双工随时打断（Barge-in）的核心技术挑战

- 所谓 **Barge-in（随时打断）**，是指音箱正在滔滔不绝播报新闻时，用户可以随时随地插话打断它，音箱必须在 200ms 内灵敏中止播放并倾听新指令。
- **硬件核心要求**：扬声器回采参考信号的失真度 THD 必须 $< 0.01\%$。若功放产生削波非线性失真，AEC 的线性自适应滤波器将无法在数学上预测这些失真分量，导致回声无法扣干净，从而使得唤醒引擎把音箱自己的声音当做人声误唤醒。
