# 从 Golden Model 到 First Silicon

## 分层验证

| 阶段 | 主要目标 | 典型证据 |
|---|---|---|
| Bit-true model | 算法与定点精度 | vector、bit-exact diff、PER curve |
| RTL/UVM | 协议、边界与并发 | assertion、functional/code coverage |
| FPGA/Emulation | Firmware/Host 联调与长序列 | boot、ring、loopback、trace |
| First Silicon | 时钟电源、总线、MAC/PHY/RF | register、scope、instrument、sniffer |
| Characterization | PVT 与性能边界 | power/EVM/PER/sensitivity matrix |

Coverage 数字不是目标本身。必须把 BA wrap、Ring full、Trigger deadline、Key 重装、Reset inflight、低功耗竞态等系统场景写进 functional coverage。

## Bring-up 梯子

```text
Power/clock/reset/JTAG
→ BootROM + memory
→ Firmware download/heartbeat
→ Host Interface register/interrupt
→ DMA/Ring loopback
→ MAC internal loopback
→ PHY digital loopback
→ RF conducted TX
→ RF conducted RX
→ OTA association/data
```

每一级只引入一个新的不确定域。若直接从上电跳到 OTA 连接失败，Host、Firmware、MAC、PHY、RF、Board 和对端都会成为嫌疑人。

## Golden Vector 对齐

固定 Scrambler seed、FEC、MCS、RU、GI/LTF 和 PSDU，逐级比较 encoder、mapper、FFT/IFFT、SIG、TXVECTOR/RXVECTOR。允许的舍入/饱和必须写入模型规范；“波形看起来差不多”不能作为通过标准。

## Fault Injection

- Descriptor 长度/版本错误、Ring wrap 和 completion loss；
- Firmware task starvation、重复/迟到 event；
- BA hole、Sequence wrap、reorder timeout；
- Key install/reset/suspend 竞态；
- Trigger buffer empty、deadline miss、错误 RU；
- AGC saturation、CFO、低 SNR 和干扰。

注入后的验收包括正确 reason、有限时间恢复、无资源泄漏、Trace 足以定位，而不只是“系统没有崩”。

## 闭环

Silicon 或现场问题修复后，应向前回灌：Firmware 单测、Driver fault injection、UVM sequence、model vector 或生产筛选项。否则知识只停留在一次性报告里。
