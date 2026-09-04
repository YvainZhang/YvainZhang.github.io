# 11 PHY、RF 与 Calibration

Wi-Fi 芯片的数据路径不会在 Hardware MAC 结束。TXVECTOR 必须变成满足 EVM、频谱和功率要求的波形；RX 信号则要经过 AGC、同步、信道估计与译码才能形成 RXVECTOR 和 PSDU。

## 模块边界

```text
Hardware MAC
  ↔ TXVECTOR / RXVECTOR / PSDU
PHY Baseband
  ↔ I/Q samples / gain-control requests
RF / AFE / FEM
  ↔ analog waveform
Antenna / Air
```

PHY/RF 问题不能只用 RSSI 判断。至少联合观察 EVM、PER、CFO、AGC/gain index、noise floor、MCS/RU、TX power 与校准状态。

## 本章内容

- [PHY TX/RX 与 RXVECTOR](01-phy-tx-rx-vector.md)
- [RF 指标、校准与失效模式](02-rf-calibration-metrics.md)

## 本章检查点

- 能解释 Preamble/SIG/LTF/Data 在接收链路中的不同作用。
- 能区分 Packet Detect、SIG decode、FEC、FCS 和 decrypt 失败。
- 能从温度、频偏、EVM/PER 和 gain table 判断校准问题，而不是只看“能否连接”。
