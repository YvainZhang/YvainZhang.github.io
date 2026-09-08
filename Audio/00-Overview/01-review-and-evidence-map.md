# Audio 知识体系与复习图谱

音频专题不只是一张格式名词表。目标是能从一个采样点追到时钟、缓冲、驱动、算法和扬声器，并用日志、波形与测量结果区分故障原因。原有 13 个模块按以下能力链阅读，不要求先背完所有产品参数。

## 三个容易混淆的边界

1. **音频 Codec 芯片与软件 codec**：前者通常指 ADC/DAC、模拟增益与数字接口等硬件；后者指 AAC、Opus 等编解码算法。编码码率不等于 I2S 总线速率。
2. **有效精度、内存容器与总线槽宽**：24-bit 有效 PCM 可占 32-bit 内存单元，并通过 32-bit slot 传输。内存布局还涉及端序、对齐与交织，不能只传一个 `bits=24` 参数。
3. **信号链与控制链**：PCM 在数据通路中流动；DAPM、时钟配置、mute 与 PA 使能是控制依赖。把所有方框串起来不表示它们都依次处理 PCM。

## 掌握标准

| 能力 | 正文入口 | 可以独立回答的问题 |
| --- | --- | --- |
| 系统架构 | [总体架构](../01-Audio-Architecture/README.md) | 采集与播放各有哪些时钟域、缓冲和生产消费者？ |
| 串行接口 | [I2S/TDM/PDM](../02-Hardware-Interfaces-I2S-TDM-PDM/README.md) | 从采样率、slot 数和 slot 宽算 BCLK，判断一位错位 |
| 模拟链路 | [AFE/Codec](../03-Analog-Front-End-Codec/README.md) | 无声、底噪、削顶、失真分别在哪个测量点定位？ |
| DSP 与数值 | [Audio DSP](../04-Audio-DSP-Microarchitecture/README.md) | 累加器范围、饱和、舍入、block 尺寸如何影响质量与时延？ |
| 实时供数 | [DMA/FIFO](../05-Audio-DMA-FIFO-Buffer/README.md) | period、buffer、FIFO 与调度最坏延迟是否匹配？ |
| 时钟匹配 | [PLL/ASRC](../06-Clock-PLL-Jitter-ASRC/README.md) | 区分瞬时 jitter、长期频偏与系统调度抖动 |
| 电源顺序 | [低功耗与爆音](../07-Low-Power-Audio-Pop-Click/README.md) | mute、bias、时钟、PA 和 DMA 如何有序启停？ |
| 声学算法 | [AEC/ANC/阵列](../08-Acoustics-DSP-Algorithms/README.md) | 参考信号、对齐、双讲与非线性分别影响什么？ |
| Linux 驱动 | [ALSA/ASoC](../09-Linux-ALSA-ASoC-Software-Stack/README.md) | PCM 参数协商、DAI、路由与 XRUN 状态如何对应？ |
| 测量证据 | [调试与声学测量](../10-Debug-Profiling-Acoustic-Tuning/README.md) | dBFS、dBSPL、THD+N 的条件与参考分别是什么？ |
| 平台集成 | [端侧/车载](../11-Edge-Automotive-Wearable-Systems/README.md) | 无线抖动、传输缓存与声学链路预算怎样分开？ |
| RTOS | [播放器与内存](../12-RTOS-Audio-Software-Stack/README.md) | 队列背压、跨核所有权与停播回收如何避免 UAF？ |
| 文件与网络流 | [编解码与流媒体](../13-Audio-Codecs-Streaming-VoiceAI/README.md) | 容器、编码配置、时间戳、网络分片和 PCM 边界如何转换？ |

## 从 Wi-Fi 驱动经验切入

先读 DMA/FIFO → ALSA/RTOS → 时钟 → [PCM 端到端案例](../Case-Studies/06-pcm-clock-buffer-evidence.md)。与网络相同，需要处理队列、背压、DMA 可见性和复位；与普通吞吐业务不同，音频消费者按采样时钟持续消耗数据，瞬时错过 deadline 可能造成不可恢复的听感缺口。

网络 buffer 缓解包到达抖动，PCM ring 保障播放连续，两者用途不同。加大任一层都可能增加延迟；网络吞吐充裕也不说明播放线程总能在 deadline 前运行。

## 面试中的十个递进追问

1. **48 kHz 立体声的 frame 是几个 sample？** 每个 frame 包含同一采样时刻两个声道的 sample，读写 API 的 frame 数不能当字节数。
2. **24-bit 数据为什么 BCLK 可能按 32-bit 算？** 有效位宽与 slot 宽独立配置。
3. **I2S 延迟一位是否多一拍？** WS 提前一拍切换，不是为每个声道额外插入一个时钟周期。
4. **Period 更小一定更低延迟吗？** 看实际排队量、唤醒策略、硬件 FIFO 与算法块大小，同时计 CPU 开销。
5. **DMA 正在跑为什么无声？** 有可能路由断链、mute、PA 未使能或 PCM 本身全零，需逐点验证。
6. **如何区分调度欠载和时钟漂移？** 看水位的瞬时跌落与长期斜率，结合时间戳及实际采样速率。
7. **AEC 与 ANC 能否共用一套时延指标？** 两者信号参考和闭环目的不同，不能用软件通信 AEC 的块长要求代替 ANC 稳定性分析。
8. **Q31 乘法为什么仍会溢出？** 乘积、累加与缩放各有范围，饱和行为及 C 语言有符号溢出要分别检查。
9. **恢复 XRUN 就没有丢音吗？** 状态恢复不意味着已丢失的时间连续性恢复，需要记录 gap 与重启策略。
10. **如何证明“音质提升”？** 固定电平、负载、带宽、加权、设备和算法版本，同时有客观结果与适当听音验证。

## 素材整合与证据等级

Audio 原有章节已覆盖接口、Codec、DSP、Linux、RTOS 与网络播放；本次保留目录，增加贯穿阅读的案例与能力索引。已有博客音频文章继续保留原 URL，不搬移或覆盖。`记录/` 中的原始工作笔记不直接复制到公开站点。

每个案例标明它属于手算模型、软件模拟还是硬件实测。没有原始日志和实验条件，就不能写成真实客户验收或认证成绩。虚构寄存器地址和教学驱动片段不可直接在真机执行。现有所有旧文并未因此自动获得完整技术审计背书。

公开一手资料：用 [ALSA PCM 文档](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html) 固定单位、状态和 API 契约；用 [ASoC 总览](https://docs.kernel.org/sound/soc/overview.html) 理解组件边界；用 [DAPM 文档](https://docs.kernel.org/sound/soc/dapm.html) 检查路由与电源依赖。具体 Codec 时序、引脚和电气要求仍以目标芯片手册为准。
