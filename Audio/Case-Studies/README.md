# 跨模块工程案例

本目录收录芯片原厂与系统工程级的跨模块全链路端到端工程推演案例：

建议先读 [PCM 到扬声器：时钟、缓冲与证据链](06-pcm-clock-buffer-evidence.md)。以下案例没有附原始记录的部分按教学场景阅读，不作为客户实测或认证结果。

1. [TWS 降噪耳机端到端软硬件与声学系统设计](01-tws-noise-cancelling-earphone.md)：麦克风拾音、混合 ANC、双核 DSP、LC3 蓝牙传输与低功耗编排全链路复盘
2. [智能座舱多音区 A2B 与 DSP 音频引擎架构推演](02-automotive-multi-zone-cockpit.md)：四音区独立隔离、引擎声浪合成 (ESE)、道路降噪 (RANC) 与车规网络拓扑
3. [智能音箱 4 麦远场拾音、AEC 回声消除与语音唤醒全流程](03-smart-speaker-far-field-aec.md)：硬件环形阵列、全双工回声消除、非平稳降噪与端侧大模型协作打通
4. [RISC-V 极受限内存（<256KB RAM）智能音箱多媒体播放器落地实战](04-riscv-low-ram-audio-player.md)：流式解码、SRAM/PSRAM 异构调度、50KB 内存极限裁剪与 WiFi 协议栈并发保障
5. [Wi-Fi 投屏 Miracast (Wi-Fi Display) 音画同步与抗抖动实战](05-miracast-av-sync-jitter-buffer.md)：TS 解复用、PTS/PCR 时钟恢复、Lipsync 容限、弹性 Jitter Buffer 与过零采样微调
