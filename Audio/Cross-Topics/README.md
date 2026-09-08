# 芯片级横向专题

本目录汇集跨越硬件模拟、数字总线、声学算法与控制理论的系统级横向深度专题：

1. [模拟混合信号隔离与 PCB 布局法则](01-analog-mixed-signal-isolation.md)：数模混合系统地弹抑制、单点星型接地、内层夹心屏蔽微带线、时钟 3W 包地与原厂 PCB 布局十大铁律
2. [全链路极低音频延迟预算优化](02-end-to-end-latency-budget.md)：从声学传感器到人耳鼓膜的七级时延量化分解、Sub-5ms 极致低延迟声学系统逐级优化与回环脉冲测量法
3. [声学算法浮点转定点量化分析](03-floating-to-fixed-point-quantization.md)：Q31 定点数体系、截断直流偏置与舍入极限环、硬件饱和与 72-bit 累加器、自适应块浮点（BFP）与原厂七步验证法
4. [微型扬声器热保护与冲程保护](04-speaker-thermal-excursion-protection.md)：微型扬声器物理极限、IV-Sense 电压电流传感、音圈电声热二阶 RC 网络模型与自适应冲程非线性前馈限幅
5. [音频重采样高频衰减缺陷与多相滤波校正](05-resample-hf-rolloff-correction.md)：线性插值 Sinc 频响缺陷数学证明（$-7.84\text{ dB}$ 高频滚降）、有理数多相 FIR 滤波器设计与 APx555 客观指标达标实战
