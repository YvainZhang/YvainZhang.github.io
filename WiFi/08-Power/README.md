# 08 低功耗

Wi-Fi 低功耗跨越空口协议、Firmware 状态机、Host 总线和系统 suspend。任何一层对“是否可以睡”的认识不一致，都可能造成额外耗电或唤醒后断流。

## 四层状态

- **802.11 Power Save**：STA 用 PM bit、TIM/DTIM、PS-Poll 或 Trigger 获取缓存数据。
- **能力增强**：U-APSD、SMPS/OMN、TWT 等减少唤醒或射频链路成本。
- **设备电源**：Firmware sleep、clock gate、radio off、chip power state。
- **Host 系统**：Runtime PM、autosuspend、system suspend/resume 与 wake source。

继续阅读：[空口与系统电源状态机](01-power-state-machine.md)。

## 本章检查点

- 能区分协议省电、总线省电和系统休眠。
- 每次睡眠都有进入条件、wake source、超时与回退。
- 功耗测试同时验证建链、吞吐和长期稳定性。
