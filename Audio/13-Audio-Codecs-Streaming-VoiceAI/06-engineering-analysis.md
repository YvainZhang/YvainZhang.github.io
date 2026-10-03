# 06 工程推演与量化模型 (Voice AI Engineering Analysis)

## 1. 全双工大模型流式语音全链路时延数学模型

**首声时延（Time-to-First-Audio, TTFA）**可以定义为用户停止说话的时刻 $t_0$，到扬声器输出回复首声的时刻 $t_1$。下面用 ASR → LLM → TTS 级联列出预算项；流式阶段可能重叠，实际总时延需要按关键路径测量：

$$T_{\text{TTFA}} = T_{\text{VAD\_hangover}} + T_{\text{enc}} + T_{\text{net\_up}} + T_{\text{cloud\_ASR}} + T_{\text{cloud\_LLM\_TTFT}} + T_{\text{cloud\_TTS\_chunk}} + T_{\text{net\_down}} + T_{\text{jitter\_buf}} + T_{\text{dec}} + T_{\text{dma\_render}}$$

### 各链路阶段耗时量化预算表（目标：$T_{\text{TTFA}} < 800\text{ ms}$）

| 链路阶段 | 物理过程与控制实体 | 典型取值 (ms) | 极致优化极限 (ms) | 工程优化策略 |
| :--- | :--- | :--- | :--- | :--- |
| $T_{\text{VAD\_hangover}}$ | 端侧判定说话结束的停顿门限 | 300 ~ 500 | 200 | 引入端侧微型语义判决模型，缩短纯能量静音观察窗 |
| $T_{\text{enc}}$ | 最后一帧 Opus 定点压缩耗时 | 20 | 5 | 开启 RISC-V 汇编加速，采用 20ms 帧长模式 |
| $T_{\text{net\_up}}$ | WiFi + 互联网到云端 RTT / 2 | 20 ~ 50 | 15 | 保持 TLS/TCP 连接常开，消除握手 RTT |
| $T_{\text{cloud\_ASR}}$ | 云端实时流式语音转写确认 | 50 ~ 100 | 30 | 边说边推，用户讲完瞬间文本转写已完成 90% |
| $T_{\text{cloud\_LLM\_TTFT}}$ | 大模型首字生成时间 (TTFT) | 150 ~ 300 | 100 | 采用推测解码 (Speculative Decoding) 与权重量化 |
| $T_{\text{cloud\_TTS\_chunk}}$ | 首个文本切片合成首帧 Opus 耗时 | 80 ~ 120 | 50 | 流式流转：首个标点符号生成前即按 4 个字切片触发 TTS |
| $T_{\text{net\_down}}$ | 云端下推首帧音频至端侧网络延迟 | 20 ~ 50 | 15 | 走内网专线 CDN 或直连近场边缘节点 |
| $T_{\text{jitter\_buf}}$ | 端侧抗网络抖动安全缓冲深度 | 60 ~ 100 | 40 | 自适应动态门限：根据网络丢包率动态调整蓄水池深度 |
| $T_{\text{dec}}$ | 端侧首帧 Opus 解码并写入 DMA | 5 | 2 | 解码后 PCM 直接投喂 DMA 描述符，免中间拷贝 |
| $T_{\text{dma\_render}}$ | DMA 缓冲吐到扬声器物理发声 | 20 | 10 | 将 Period 尺寸从 512 压缩到 256 采样点 |
| **全链路总和** | **串行预算总和** | **725 ~ 1265 ms** | **467 ms** | 这组配置下的预算，需测量实际阶段重叠与首声时间 |

---

## 2. 自适应 Jitter Buffer 深度与丢包补偿数学推演

设端侧网络接收时间间隔服从期望为 $\mu_{\text{pkt}} = 20\text{ ms}$，方差为 $\sigma^2$ 的高斯分布，即网络时延抖动 $J \sim \mathcal{N}(0, \sigma^2)$。

若端侧 Jitter Buffer 的预置深度时间为 $T_{\text{jb}}$，则一个音频切片发生欠载（Underrun / 下溢导致扬声器无声）的统计概率为时延超过缓冲深度的尾部积分：

$$P_{\text{underrun}} = P(t_{\text{arrival}} > T_{\text{jb}}) = \int_{T_{\text{jb}}}^{\infty} \frac{1}{\sqrt{2\pi}\sigma} e^{-\frac{(t - \mu_{\text{pkt}})^2}{2\sigma^2}} dt = Q\left(\frac{T_{\text{jb}} - \mu_{\text{pkt}}}{\sigma}\right)$$

### 抖动缓冲深度动态调整自适应算法
为了兼顾超低交互时延与极低破音率，系统引入双因子滑动窗口自适应调整：

$$T_{\text{jb}}(k) = \max \left( T_{\text{min}}, \mu_{\text{jitter}}(k) + \alpha \times \sigma_{\text{jitter}}(k) \right)$$

* 其中 $\alpha = 3$，可参考正态分布 99.7% 的区间覆盖；$P < 0.3\%$ 只对应这里的统计假设，不能直接作为设备破音率保证；
* 当网络平稳（$\sigma \to 0$）时，$T_{\text{jb}}$ 自动收缩至 $T_{\text{min}} = 40\text{ ms}$（仅需缓存 2 帧）；
* 当 $\sigma > 30\text{ ms}$ 时，可以评估在 3 帧内将缓冲目标扩张至 $120\text{ ms}$。调整仍需考虑可用数据量、增加的交互等待和 PLC 的适用范围；网络时延的长尾与相关性可能不符合高斯假设。
