# 全链路案例 3：智能音箱 4 麦远场拾音、AEC 回声消除与语音唤醒全流程

## 1. 案例目标与工程背景

复盘一款支持全双工语音交互的智能家居中控音箱：
- 在自身以 $85\text{ dB SPL}$ 大音量播放音乐的同时，能够灵敏响应 5 米外轻声发出的唤醒词；
- 支持随时插话打断（Barge-in）；
- 硬件物料成本（BOM）控制在极低水平。

---

## 2. 硬件拓扑与全流程时序图

```mermaid
sequenceDiagram
    autonumber
    participant SPK as 扬声器单元 (85dB 音乐)
    participant Loopback as 硬件直连参考信号 (Echo Ref)
    participant MicArray as 环形 4 麦克风阵列
    participant DSP as Audio DSP 前处理核心
    participant NPU as 端侧 NPU 唤醒模型

    SPK->>MicArray: 强音乐声波充斥房间，通过空气直接窜入麦克风
    SPK->>Loopback: DAC 模拟输出同步镜像输入至参考通道
    MicArray->>DSP: 4 通道采集混杂信号: 强回声(85dB) + 环境噪声(60dB) + 微弱人声(50dB)
    Loopback->>DSP: 送入无失真纯净参考信号 x(n)

    Note over DSP: 阶段 1: PBFDAF 多通道频域自适应滤波消除线性回声 (压制 30dB)
    Note over DSP: 阶段 2: MVDR 自适应波束成形对准人声来向 (抬升信噪比 12dB)
    Note over DSP: 阶段 3: 非线性残余回声消除 (NLP) 与深度学习降噪 (AI-NS)

    DSP->>NPU: 提取出纯净的人声音频帧送入 NPU
    NPU->>NPU: 神经网络计算，命准确唤醒词
    NPU-->>SPK: 触发主控瞬间淡出音乐，并播报“在的，请吩咐”
```

---

## 3. 关键自测实操技巧

- **消音室基准测试**：先在全消音室测量扬声器到麦克风的物理脉冲响应，确认回声路径线性度（THD 是否满足要求）；
- **动态延迟校准**：通过在播放音乐前打入一个不可闻的微弱单脉冲（Diracs Pulse），自动测量并锁定整机声学群延迟。
