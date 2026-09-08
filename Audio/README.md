---
title: Audio 芯片与系统全栈知识体系
hide:
  - toc
---

<section class="audio-home-hero">
  <p class="audio-home-kicker"><span></span> Silicon Architecture / Audio System Atlas</p>
  <h1>Audio System Atlas</h1>
  <p class="audio-home-lead">从芯片原厂与系统工程视角出发，系统梳理音频从物理声波、模拟前端 AFE、Sigma-Delta ADC/DAC，到 I2S/TDM/PDM/SoundWire 高速音频接口、Audio DSP 微架构、低功耗常开监听 (VAD/AON)、DMA 环形缓冲、Linux ALSA/ASoC 驱动栈、RTOS 嵌入式软件框架、软件编解码与端侧前沿声学算法的全栈工程地图。</p>
  <div class="audio-home-stats">
    <span><strong>13</strong>核心模块</span>
    <span><strong>127</strong>篇文档</span>
    <span><strong>125</strong>张图表</span>
    <span><strong>3</strong>个实验</span>
  </div>
</section>

<section class="audio-home-section">
  <div class="audio-home-section-head">
    <p>Hardware Flow / 01</p>
    <h2>看一个音频采样点如何流过整颗芯片与系统链路。</h2>
  </div>
  <div class="audio-home-flow" aria-label="音频系统全硬件路径">
    <a href="03-Analog-Front-End-Codec/">AFE/MIC</a><i>→</i>
    <a href="03-Analog-Front-End-Codec/">ΣΔ ADC</a><i>→</i>
    <a href="02-Hardware-Interfaces-I2S-TDM-PDM/">PDM/I2S</a><i>→</i>
    <a href="04-Audio-DSP-Microarchitecture/">Audio DSP</a><i>→</i>
    <a href="05-Audio-DMA-FIFO-Buffer/">DMA Ring</a><i>→</i>
    <a href="12-RTOS-Audio-Software-Stack/">minialsa/RTOS</a><i>→</i>
    <a href="09-Linux-ALSA-ASoC-Software-Stack/">ALSA/DAPM</a><i>→</i>
    <a href="03-Analog-Front-End-Codec/">ΣΔ DAC</a><i>→</i>
    <a href="03-Analog-Front-End-Codec/">Class-D PA</a>
  </div>
  <p class="audio-home-flow-note">麦克风模拟信号经 AFE PGA 与 Sigma-Delta 调制器数字化，由 I2S/TDM/SoundWire 或 PDM CIC 抽取送入 Audio DSP；硬件 VAD/AEC/ANC 加速器实时处理，Scatter-Gather DMA 将 PCM 搬入系统 DDR/SRAM 环形缓冲区；Linux ALSA ASoC 或 RTOS minialsa 驱动编排流水线，下行经 DAC 与 Class-D 放大器驱动扬声器，IV-Sense 闭环实时保护音圈。</p>
</section>

<section class="audio-home-section">
  <div class="audio-home-section-head">
    <p>Reading Routes / 02</p>
    <h2>按工程角色与研发场景，选择最适合的学习路线。</h2>
  </div>
  <div class="audio-route-grid">
    <a class="audio-route-card" href="00-Overview/">
      <span>Route 01</span>
      <h3>底层驱动与系统软件</h3>
      <p>I2S/TDM 时序 → DMA 环形缓冲 → minialsa/ALSA → DAPM 路由 → XRUN 爆音诊断</p>
    </a>
    <a class="audio-route-card" href="00-Overview/">
      <span>Route 02</span>
      <h3>芯片架构与微架构设计</h3>
      <p>AFE/Codec → Audio DSP/TCM → 双音频 PLL/Jitter → ASRC 采样率转换 → 模拟混合隔离</p>
    </a>
    <a class="audio-route-card" href="00-Overview/">
      <span>Route 03</span>
      <h3>声学算法与音频调优</h3>
      <p>AEC 回声消除 → 麦克风阵列 Beamforming → ANC 主动降噪 → AP 仪器测试 → 空间音频</p>
    </a>
  </div>
</section>

<section class="audio-home-section">
  <div class="audio-home-section-head">
    <p>Core Modules / 03</p>
    <h2>十三个模块，拼合现代高性能音频芯片的完整硅片画像。</h2>
  </div>
  <div class="audio-module-grid">
    <a href="01-Audio-Architecture/"><span>01</span><strong>音频子系统总体架构</strong><em>AFE · Digital Chain · Bring-up</em></a>
    <a href="02-Hardware-Interfaces-I2S-TDM-PDM/"><span>02</span><strong>硬件接口与时序协议</strong><em>I2S · TDM · PDM · SoundWire</em></a>
    <a href="03-Analog-Front-End-Codec/"><span>03</span><strong>模拟前端与 Codec 架构</strong><em>$\Sigma\Delta$ · Class-D · Jack · SNR</em></a>
    <a href="04-Audio-DSP-Microarchitecture/"><span>04</span><strong>音频 DSP 微架构</strong><em>HiFi · SIMD · TCM · HW VAD</em></a>
    <a href="05-Audio-DMA-FIFO-Buffer/"><span>05</span><strong>音频 DMA 与缓冲管理</strong><em>RingBuffer · Watermark · QoS</em></a>
    <a href="06-Clock-PLL-Jitter-ASRC/"><span>06</span><strong>时钟系统、PLL 与 ASRC</strong><em>Dual-PLL · Jitter · ASRC · CDC</em></a>
    <a href="07-Low-Power-Audio-Pop-Click/"><span>07</span><strong>低功耗与防爆音技术</strong><em>AON · POP/Click · Zero-cross · IV-Sense</em></a>
    <a href="08-Acoustics-DSP-Algorithms/"><span>08</span><strong>声学前处理与核心算法</strong><em>AEC · Beamforming · AI-NS · ANC</em></a>
    <a href="09-Linux-ALSA-ASoC-Software-Stack/"><span>09</span><strong>Linux ALSA/ASoC 驱动栈</strong><em>Machine · Platform · Codec · DAPM</em></a>
    <a href="10-Debug-Profiling-Acoustic-Tuning/"><span>10</span><strong>调试测量与调音声学</strong><em>Oscilloscope · AP 测量 · XRUN · Hiss</em></a>
    <a href="11-Edge-Automotive-Wearable-Systems/"><span>11</span><strong>端侧、车载与可穿戴系统</strong><em>A2B · BLE Audio/LC3 · 车载多音区</em></a>
    <a href="12-RTOS-Audio-Software-Stack/"><span>12</span><strong>RTOS 嵌入式音频软件栈</strong><em>minialsa · Pipeline · SRAM/PSRAM · RV32P</em></a>
    <a href="13-Audio-Codecs-Streaming-VoiceAI/"><span>13</span><strong>软件编解码与大模型语音</strong><em>MP3/AAC/Opus · M4A/HLS · ChatGPT · AVS</em></a>
  </div>
</section>

<section class="audio-home-section audio-home-practice">
  <div class="audio-home-section-head">
    <p>Practice / 04</p>
    <h2>把微架构理论放回全链路端到端案例与可复现源码实验。</h2>
  </div>
  <div class="audio-practice-grid">
    <a href="Case-Studies/"><span>Case Studies</span><strong>跨模块工程案例</strong><p>TWS 降噪耳机端到端链路、智能座舱 A2B 多音区与智能音箱远场语音拾音。</p></a>
    <a href="Labs/"><span>Labs</span><strong>可复现代码实验</strong><p>I2S 协议时序波形仿真、ALSA 虚拟声卡驱动跟踪与定点 DSP LMS 回声消除算子。</p></a>
    <a href="Glossary/"><span>Glossary</span><strong>专业术语与缩写</strong><p>涵盖 I2S、TDM、PDM、SoundWire、ASRC、DAPM、THD+N、A2B 等 90+ 词条。</p></a>
  </div>
</section>

## 文档约定与原厂工程“七问”

先阅读 [知识体系与面试复习](00-Overview/01-review-and-evidence-map.md)，再用 [PCM、时钟与缓冲证据链](Case-Studies/06-pcm-clock-buffer-evidence.md) 串起正文。文档计数包含索引和实验说明，不表示每篇都已完成深度审计；上方为阅读路线，Linux 与 RTOS 是不同实现路径，不必串行经过。

以下 7 个问题是持续完善标准，不是所有现有笔记都已经完成的验证承诺：

1. **硬件解决什么问题**：该模块在信号保真度（Fidelity）、动态范围（DNR）、极低时延（Latency）或超低功耗（uW）中的根本职责。
2. **硬件微架构与组成**：模拟前端、数字滤波器、专用加速引擎与片上总线/FIFO 的内部电路拓扑。
3. **软件可见接口**：驱动工程师/DSP 固件工程师可见的控制寄存器、DMA 描述符、中断字与状态寄存器。
4. **四流全链路分析**：地址流、数据流、控制流、事件/中断/DMA 流如何在硬件管道中流转。
5. **软硬件设计约束**：面积（PPA）、时序建立保持时间、时钟抖动（Jitter）、模拟底噪（Hiss）与爆音（POP-Click）抑制。
6. **现场排错与调试清单**：面对无声、断音（Underrun）、爆音杂音、直流偏置或 AEC 漏回声时的系统化排查步骤。
7. **实验与验证推演**：如何通过逻辑分析仪、AP 音频测试仪、C-Model 仿真或实板验证指标。

!!! note "阅读说明与免责声明"
    文档中的地址、寄存器偏移和微架构参数若无特别说明，均用于解释工业界通用音频 SoC/Codec 架构机制，不对应特定商业芯片私密设计。实际工程项目应以目标音频芯片的 TRM、官方数据手册、架构白皮书和勘误表（Errata）为准。

主站入口：[Audio 专题发布导读](/2026/09/08/audio-system-atlas/)。
