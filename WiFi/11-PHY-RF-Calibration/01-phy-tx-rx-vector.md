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
| PSDU 输出 | MAC FCS/格式 | PHY CRC 与 MAC FCS 边界 |

“RX FCS 高”不能直接推出 RF 差；错误可能来自干扰、CFO、channel estimation、过高 MCS，甚至 DMA/内存损坏。用 conducted reference、loopback 和已知 Vector 分层排除。

## HE TB 的特殊挑战

AP 同时接收多个 STA 的 RU，每个用户存在独立 CFO、timing 与到达功率。Trigger 的 target RSSI、UL length 和参数约束帮助接收机对齐；调试应按 user/RU 输出 detect、SIG/FEC/FCS 结果，而不是只给整包成功失败。
