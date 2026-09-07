# PHY TX/RX Pipeline 与 Vector

TXVECTOR/RXVECTOR 是 MAC 与 PHY 的工程契约。它们不是一个“速率字段”，而是一组足以唯一解释 PPDU 的参数与结果。

## TX Pipeline

```mermaid
flowchart LR
    PSDU --> SCR[Scramble]
    SCR --> FEC[BCC/LDPC]
    FEC --> INT[Interleave / parse]
    INT --> MAP[QAM mapping]
    MAP --> RU[RU/subcarrier + pilot]
    RU --> IFFT[IFFT + GI]
    IFFT --> DFE[Digital front end]
    DFE --> DAC[DAC / RF / PA]
```

TXVECTOR 应明确 PPDU type、bandwidth、MCS、NSS、GI/LTF、coding、STBC/DCM、beamforming、RU/user allocation、PSDU length或duration、TX power 与 puncturing。Hardware MAC 生成/选择参数，PHY 验证组合合法性；非法 Vector 要产生可定位 reason，而不是静默修正。

## RX Pipeline

RF/ADC 后先做 Packet Detect 与 AGC，再利用 Preamble/LTF 完成 timing、CFO/SFO 和 channel estimation。SIG 字段决定后续解调参数；其中 HE-SIG-B 是 HE MU 专属信令之一，不应把它写成所有 HE PPDU 的公共步骤。

```text
Energy/correlation detect
→ AGC convergence
→ coarse/fine timing + CFO
→ L-SIG / HE-SIG decode
→ RU/user selection
→ FFT/equalization/pilot tracking
→ soft demap + FEC decode
→ descramble → PSDU
```

PHY 输出 PSDU 给 MAC；MPDU/A-MPDU 的解析属于 MAC 语义。RXVECTOR 则报告 PPDU type、MCS/NSS/GI/LTF、RU、coding、RSSI/SNR/EVM、timestamp 和 PHY reason。

## 失败分层

| 最后成功点 | 可能问题 | 关键观测 |
|---|---|---|
| Energy detect | 灵敏度、干扰、门限 | noise floor、gain、false alarm |
| Preamble detect | AGC/CFO/相关 | AGC settle、CFO estimate |
| SIG decode | 格式/信道估计 | SIG CRC、LTF、unsupported vector |
| FEC decode | SNR/EVM/MCS | decoder iterations、codeword error |
| PSDU 输出 | MAC FCS/格式 | SIG 校验、译码状态与逐 MPDU FCS 边界 |

“RX FCS 高”不能直接推出 RF 差；错误可能来自干扰、CFO、channel estimation、过高 MCS，甚至 DMA/内存损坏。用 conducted reference、loopback 和已知 Vector 分层排除。

## HE TB 的特殊挑战

AP 同时接收多个 STA 的 RU，每个用户存在独立 CFO、timing 与到达功率。Trigger 的 target RSSI、UL length 和参数约束帮助接收机对齐；调试应按 user/RU 输出 detect、SIG/FEC/FCS 结果，而不是只给整包成功失败。

## Vector是跨层参数，不必等于某个C结构体

IEEE中的服务参数、Firmware命令、Hardware寄存器以及RX diagnostic metadata可以对应同一信息，但格式和有效时间不同。文章中的Vector指这一组契约，不能把所有RSSI/EVM字段都称作标准强制RXVECTOR字段。

在TX开始前验证format/BW/MCS/NSS/GI/LTF/coding/RU组合；PHY拒绝的原因要回传，避免Host仍将其计为air attempt。RX则应标明每个字段什么时候有效，例如SIG失败时MCS可能没有可信值。

## OFDM数值关系

HE常用有效symbol时长12.8 μs，对应子载波间隔78.125 kHz；加GI后才是数据symbol周期。采样率20 MHz、256-point FFT的模型也给出 `20 MHz/256=78.125 kHz`。

这不是说256个tone都传数据；DC、guard、pilot与RU分配减少有效承载。普通242-tone RU的数据tone数为234，具体可用 [wlanHEOFDMInfo](https://www.mathworks.com/help/wlan/ref/wlanheofdminfo.html) 检查配置。

数据率近似 `Ndata × bits_per_subcarrier × code_rate × NSS / Tsymbol`。DCM、STBC、FEC padding与format限制需另外处理。EHT不能不加核对直接沿用HE参数表。

## PHY流水线的两个反馈环

同步/AGC在前导码内尽快收敛；后续pilot tracking纠正随symbol积累的相位/采样偏差。信道估计决定equalizer，noise estimate影响soft demap的LLR尺度，LLR质量又影响FEC迭代与成功率。

因此“decoder failure”只是最后失败点，可能源自AGC clipping、CFO、timing或channel estimate。抓到错误率后应检查前级质量，而不是直接加大LDPC iteration。

## PHY和MAC校验边界

部分SIG字段有各自的校验/校验位；MAC MPDU有FCS。不能把整个PSDU想象成拥有统一的“PHY CRC”。当A-MPDU中某MPDU FCS失败，要保留其边界和RX状态，区分信道解码错误与后续内存损坏。

对于HE TB，多用户共用部分格式信息并按用户恢复数据，不能期待每个用户都独立携带HE-SIG-B。AP Trigger上下文也是解释接收参数的一部分。

## Golden Vector对照

固定payload、scrambler seed、format、RU/MCS/NSS/GI和channel impairment，比较各级bit/LLR/符号及最终MPDU。定点模型还需记录位宽、舍入、饱和、缩放，禁止仅凭两张星座图视觉相似验收。

参考：[MathWorks Packet Recovery](https://www.mathworks.com/help/wlan/gs/packet-recovery.html)。仿真调用演示算法阶段，不等同于真实芯片处理延迟或硬件模块划分。

## 复习追问与答案

**提高FFT点数必然增加数据率吗？** 不，采样率、子载波间隔、GI、有效tone和编码共同决定。

**为何SIG成功但数据失败？** 训练/信令与payload使用的调制编码、长度和接收裕量不同，后续跟踪也可能失效。

**看RXVECTOR先看什么？** 先看valid/error与format，再解释其余字段，避免使用无效MCS/RSSI。
