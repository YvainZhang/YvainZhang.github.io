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

## 一条需求拆成Stimulus、Checker与Coverage

以“有效Peer的合法Trigger在允许条件下得到及时响应”为教学需求。Stimulus选择RU/MCS/长度与Context；Checker验证实际Vector、发射起点、PPDU结果和错误原因；Coverage覆盖参数和边界状态。

非法RU、不匹配AID、无Buffer、切信道和旧generation是不同测试，不应只增加随机包量。允许不响应的条件也要有明确checker，避免所有缺响应都被判同一种失败。

## Golden Model与RTL差异怎么定位

逐级比较scrambler、FEC、mapper、频域tone、IFFT、定点缩放和输出样本。发现差异时先确认同一seed、参数和位宽，再看舍入/饱和。

教学例：模型32-bit中间结果直接截断，而RTL四舍五入，平均误差可能很小但bit-true测试持续失败。需要先定义规格允许的量化方式，再判断设计是否错误；不能修改测试容差到“刚好通过”。

## FPGA与Silicon分别证明什么

FPGA/emulation适合长序列、Host/FW交互、状态机和资源管理，但时钟频率、内存延迟、模拟前端与真实芯片不同。FPGA连接通过不能证明Silicon SIFS、PVT和RF指标通过。

Silicon bring-up先确认电源/clock/reset、寄存器和内存，再验证HIF/中断/DMA、数字loopback、conducted、真实协议。每一步保存进入条件、输入向量、输出与停止条件，失败时只增加有限未知因素。

## 覆盖率的危险误读

Code coverage表示结构执行；functional coverage表示目标场景命中；assertion检查不变量；cross coverage检查组合。全部模块单独通过，不证明 `rekey × reorder × reset` 交错正确。

随机种子、build ID、硬件revision和配置应可回放。一次失败重跑成功仍要记录flaky原因；不能只保留最后一次通过结果。

## 复习追问与答案

**为什么优先数字loopback？** 隔离模拟和对端因素，验证已有数字路径后再扩大测试范围。

**如何选择cross coverage？** 依据共享资源和生命周期风险，而非把所有参数做无界笛卡尔积。

**修复现场问题后需要什么？** 将最小触发序列回灌到最早能复现的模型/RTL/FW/Host测试层，并保留系统级回归。

深入：[Coverage与追溯](03-coverage-traceability-regression.md)。
