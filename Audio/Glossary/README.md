# 音频芯片与系统专业术语表

| 缩写 / 术语 | 英文全称 | 核心释义 |
| :--- | :--- | :--- |
| **I2S** | Inter-IC Sound | 飞利浦制定的芯片间数字立体声音频点对点三线总线（BCLK, LRCK, SDATA） |
| **TDM** | Time Division Multiplexing | 时分复用协议，在单根物理数据线上划分多达 32 个时隙传输多声道音频 |
| **PDM** | Pulse Density Modulation | 脉冲密度调制，微型 MEMS 麦克风直接输出的 1-bit 高频过采样数字流 |
| **SoundWire** | MIPI SoundWire | MIPI 联盟制定的双线制（时钟+数据）统一控制与多通道音频级联总线 |
| **A2B** | Automotive Audio Bus | ADI 专有汽车音频总线，单非屏蔽双绞线菊花链串联 32 通道与远程供电 |
| **ASRC** | Asynchronous Sample Rate Converter | 硬件异步采样率转换器，全数字域消除独立晶振频偏并无损重采样 |
| **AFE** | Analog Front-End | 模拟前端，包含麦克风偏置、低噪声前置放大器（PGA/LNA）与抗混叠滤波 |
| **PGA** | Programmable Gain Amplifier | 可编程增益放大器，软件动态微调模拟音频输入幅值防失真 |
| **Codec** | Coder-Decoder | 音频编解码芯片，集成 ADC、DAC、混合信号调理与功放驱动的专用集成电路 |
| **Sigma-Delta** | Sigma-Delta ($\Sigma\Delta$) Modulation | 过采样与高阶噪声整形模数/数模转换架构，以高采样率换取极致高分辨率 |
| **OSR** | Oversampling Ratio | 过采样率，调制器实际采样时钟频率与音频最高有效奈奎斯特频率的比值 |
| **DEM** | Dynamic Element Matching | 动态元件匹配，打乱 DAC 内部电流源使用顺序消除工艺失配误差的算法 |
| **BCLK** | Bit Clock / Serial Clock | 音频位时钟，串行数据线上每个有效 bit 的同步节拍脉冲 |
| **LRCK / WS** | Left-Right Clock / Word Select | 左右声道帧时钟，指示当前传输的数据属于左声道还是右声道，频率等于 $f_s$ |
| **MCLK** | Master Clock | 音频主系统时钟，通常为采样率的 256 倍或 512 倍（如 12.288MHz/24.576MHz） |
| **THD+N** | Total Harmonic Distortion + Noise | 总谐波失真加噪声，系统输出中所有非线性谐波与底噪能量占纯基波的百分比 |
| **DNR** | Dynamic Range | 动态范围，系统最大无失真输出信号与本底最小残留噪声的比值（dB） |
| **SNR** | Signal-to-Noise Ratio | 信噪比，满量程有用信号与带内总噪声功率的比值（dB） |
| **CMRR** | Common-Mode Rejection Ratio | 共模抑制比，差分放大器抑制两输入端同相共模电磁干扰的能力 |
| **Class-D** | Class-D Audio Amplifier | 开关型高效率功放，功率管工作在饱和导通与截止态，能效可达 90% 以上 |
| **Class-AB** | Class-AB Audio Amplifier | 线性推挽功放，交替导通且具有微小偏置电流，失真极低但发热较大 |
| **Class-H** | Class-H Audio Amplifier | 动态多供电轨功放，实时追踪音频包络动态升压，兼顾音量与极低功耗 |
| **IV-Sense** | Current-Voltage Sensing | 智能功放内置的实时音圈电流电压高频采样，用于实时闭环阻抗与热保护 |
| **POP / Click** | Turn-on/off Transient Noise | 开关机或音频流切换时，由于输出端直流电平突变引发的刺耳爆音 |
| **Zero-Crossing** | Zero-Crossing Detection | 零交叉检测，仅在模拟交流音频电压正好穿过 0V 地电平时允许增益切换 |
| **Soft-Ramp** | Soft Ramp-up/down | 软启动爬坡，使偏置电压沿 S 型曲线极其缓慢平滑建立，规避可闻爆音 |
| **AON** | Always-On Domain | 超低功耗常开电源域，在主芯片休眠时仅以微瓦级电流维持待机监听 |
| **VAD** | Voice Activity Detection | 语音活动检测，实时分析声音能量与频谱，精准识别人声开口瞬间 |
| **KWS** | Keyword Spotting | 关键词唤醒，在本地运行轻量神经网络模型识别“唤醒词” |
| **Pre-roll** | Pre-roll Audio Buffer | 前置预录环形缓冲，保存唤醒词被断定之前的辅音，防止语音识别丢首字 |
| **AEC** | Acoustic Echo Cancellation | 声学回声消除，实时自适应滤波消除扬声器发声回窜入本地麦克风的自激声音 |
| **DTD** | Double-Talk Detector | 双讲检测器，在两端同时说话时冻结自适应滤波器更新，防止算法发散 |
| **ERLE** | Echo Return Loss Enhancement | 回声回损增益，衡量 AEC 自适应滤波器对回声能量的绝对衰减深度（dB） |
| **NLP** | Non-Linear Processor | 非线性后处理器，用于强力切除线性自适应滤波器未滤干净的残余微弱回声 |
| **Beamforming**| Microphone Array Beamforming | 麦克风阵列波束成形，利用空间相位差形成具有方向选择性的定向拾音波束 |
| **MVDR** | Minimum Variance Distortionless Response| 最小方差无畸变响应自适应波束成形算法，在强干扰来向自适应产生深零陷 |
| **ANS** | Acoustic Noise Suppression | 声学噪声抑制，通过频域谱减、维纳滤波或神经网络滤除环境背景杂音 |
| **AI-NS** | Deep Learning Noise Suppression | 基于深度神经网络（如 RNNoise / CRN）的声学降噪，可消除突发非平稳噪音 |
| **ANC** | Active Noise Cancellation | 主动降噪技术，通过麦克风采集外界噪音并驱动扬声器发出反向声波物理抵消 |
| **Feedforward**| Feedforward ANC | 前馈式降噪，麦克风朝向耳机外部拾取环境噪音，降噪频带宽 |
| **Feedback** | Feedback ANC | 反馈式降噪，麦克风朝向耳道内部耳膜处监视残余噪声，自适应抗佩戴漏气 |
| **Hybrid ANC** | Hybrid Active Noise Cancellation | 混合式主动降噪，同时集成前馈麦克风与反馈麦克风，兼顾频宽与降噪深度 |
| **HRTF** | Head-Related Transfer Function | 头部相关传输函数，描述声波从空间特定坐标传播至人耳耳膜的完整声学滤波 |
| **ITD** | Interaural Time Difference | 双耳时间差，声波到达左耳与右耳之间的传播微秒级物理延迟偏差 |
| **ILD** | Interaural Level Difference | 双耳声级差，声波由于头部阴影遮挡在两耳产生的幅度衰减差异 |
| **Spatial Audio**| Binaural Spatial Audio | 空间音频，结合 HRTF 卷积与 6 轴 IMU 姿态追踪还原真实三维环绕声场 |
| **TCM** | Tightly-Coupled Memory | 紧耦合内存，与 DSP 核心点对点直接相连的片上 SRAM，单周期零等待绝对无抖动 |
| **VLIW** | Very Long Instruction Word | 超长指令字，单个时钟周期同时并行发射多个独立计算槽位的指令集架构 |
| **SIMD** | Single Instruction Multiple Data | 单指令多数据流，一条指令同时操作多个音频采样点的向量并行架构 |
| **Guard Bits** | Accumulator Guard Bits | 累加器扩展保护位，在 DSP 累加器顶端额外设置的 8 位整型防止多级乘加溢出 |
| **Saturating Math**| Saturating Arithmetic | 硬件饱和截断算术，溢出时强制钳位在最大正数或负数，杜绝回绕爆音 |
| **Zero-Overhead**| Zero-Overhead Loop | 硬件零开销循环，由专用硬件计数器与地址寄存器维护循环，无需跳转指令 |
| **Bit-Reversal**| Bit-Reverse Addressing | 硬件位反转寻址，按二进制倒序镜像生成内存地址，极速加速 FFT 蝶形运算 |
| **ALSA** | Advanced Linux Sound Architecture | Linux 官方高级声音架构，统一内核音频设备节点与标准驱动接口规范 |
| **ASoC** | ALSA System on Chip | ALSA 专为嵌入式片上系统设计的框架，严格解耦 Machine、Platform 与 Codec |
| **DAPM** | Dynamic Audio Power Management | 动态音频电源管理，将芯片内部模拟部件抽象为有向图按需供电与编排 |
| **DPCM** | Dynamic PCM | 动态 PCM，将虚拟声卡前端（FE）与物理硬件接口后端（BE）解耦的拓扑框架 |
| **hw_ptr** | Hardware Pointer | 硬件播放指针，指示当前底层 DMA 控制器正在搬运的物理采样位置 |
| **appl_ptr** | Application Pointer | 应用写入指针，指示用户态进程已将 PCM 数据填充到的最新缓冲区位置 |
| **Period Size** | ALSA Period Size | 周期大小，音频 DMA 每搬运完成该数量的采样点，触发一次硬件中断通知 CPU |
| **Buffer Size** | ALSA Buffer Size | 环形缓冲区总容量，通常等于整数个 Period Size（如 2~8 个 Periods） |
| **XRUN** | Underrun / Overrun | 缓冲区异常事件；Underrun 为放音欠载饥饿断音，Overrun 为录音溢出丢点 |
| **TinyALSA** | Lightweight ALSA Userspace Library | 专为嵌入式系统设计的极简轻量级 ALSA 用户态操作库，体积 $< 30\text{ KB}$ |
| **PipeWire** | PipeWire Multimedia Engine | 现代 Linux 下一代基于处理图（Graph）的实时多媒体引擎，时延 $< 5\text{ ms}$ |
| **LC3** | Low Complexity Communication Codec | 低复杂度通信编解码器，蓝牙 LE Audio 官方标准，极低延迟高压缩比 |
| **BLE Audio** | Bluetooth Low Energy Audio | 低功耗蓝牙音频规范，支持原生双耳多重流（Multi-stream）与广播分享 |
| **Jack Detect** | Audio Jack Detection | 耳机插孔机械与电气检测，感知插入/拔出并测量耳麦阻抗识别按键 |
| **MICBIAS** | Microphone Bias Voltage | 麦克风偏置供电引脚，专为微型麦克风内部场效应管供电的超洁净低噪声电源 |
| **Ground Loop**| Ground Loop Noise | 地回路噪声，设备间多个接地路径电位不一致引起的 50Hz/60Hz 交流蜂鸣干扰 |
| **Kelvin Sense**| Ground Sense / Kelvin Connection | 开尔文地感测走线，耳放负端直接引出细线至插座焊盘根部消除地回流压降 |
| **Hiss** | Residual Noise Floor | 嘶嘶声底噪，放大器内部晶体管热噪声放大的白噪声听觉体现 |
| **Clipping** | Audio Waveform Clipping | 削波失真，音频振幅超过供电轨或数字 0dBFS 上限被强制切平引发的严重破音 |
| **Coherent Sampling**| Coherent Sampling Condition | 相干采样，信号发生器频率与 FFT 采样率满足特定互质倍数消灭频谱泄漏 |
| **minialsa** | Lightweight ALSA-like HAL | RTOS 上的极简 PCM 硬件抽象层，接口语义对齐 Linux ALSA/TinyALSA，核心体积 $< 10\text{ KB}$ |
| **SPSC** | Single-Producer Single-Consumer | 单生产者单消费者无锁环形缓冲，读写指针分离仅靠内存屏障同步，天然无死锁 |
| **PSRAM** | Pseudo-Static RAM | 经 QSPI/OPI 总线外挂的伪静态 RAM，容量大成本低，但随机访问延迟高需与片内 SRAM 异构调度 |
| **RV32P** | RISC-V Packed DSP Extension | RISC-V 打包 SIMD DSP 指令扩展，单周期完成双 16 位饱和乘加等定点音频算子 |
| **SBR** | Spectral Band Replication | 频带复制，HE-AAC 仅编码低频核心、高频由包络参数复制重构的带宽扩展技术 |
| **PS** | Parametric Stereo | 参数立体声，HE-AAC v2 将双声道下混单声道并以 IID/ITD/ICC 空间参数恢复的极致压缩 |
| **ADTS** | Audio Data Transport Stream | AAC 裸流帧头格式，7 字节头声明 profile、声道与帧长，无需容器即可流式传输 |
| **PLC** | Packet Loss Concealment | 丢包补偿，解码器基于历史谐波参数平滑预测丢失帧，消除断流金属机械音 |
| **Barge-in** | Voice Interruption | 语音打断，用户在设备播报中插话时瞬时清空缓冲并静音、无缝切换至聆听态 |
| **TTFA** | Time-to-First-Audio | 首声时延，从用户停止说话到扬声器发出回复第一个声波的全链路总耗时 |
| **Jitter Buffer** | Adaptive Jitter Buffer | 自适应抗抖动缓冲，按网络时延统计特征动态调整蓄水深度，平滑丢包重传尖峰 |
| **moov / FastStart** | Movie Atom Relocation | MP4 元数据索引原子；moov 后置导致无法流式播放，faststart 将其重排至文件头部 |
| **esds** | Elementary Stream Descriptor | MP4 音频解码配置描述符，ASN.1 变长编码存放 AudioSpecificConfig 等初始化参数 |
| **ICY** | Shoutcast / Icecast Metadata | 网络电台元数据协议，每 metaint 字节音频后插入标题文本，须精确剥离防止爆音 |
| **HLS** | HTTP Live Streaming | 基于 M3U8 切片清单的 HTTP 自适应流媒体协议，客户端定时轮询切换码率切片 |
| **PCR / PTS** | Program Clock Reference / Presentation Time Stamp | 传输流时钟标记，27MHz 参考用于恢复系统主时钟，90kHz 时间戳调度音画同步渲染 |
