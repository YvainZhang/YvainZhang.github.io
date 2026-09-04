# 12 验证、认证与量产

Wi-Fi 芯片从 RTL 到客户设备，要跨越算法模型、仿真、FPGA/Emulation、Silicon Bring-up、协议互操作、法规认证和量产校准。任何阶段只验证“能连、能跑流”都不足以覆盖真实风险。

## 生命周期

```text
Algorithm/Golden Model
→ RTL/UVM
→ FPGA/Emulation
→ First Silicon Bring-up
→ Characterization/Interop
→ Certification/Regulatory
→ Production Test/Calibration
→ Field Feedback
```

后一个阶段发现的问题，应转化为前一阶段可自动复现的测试或断言，形成闭环。

## 本章内容

- [从模型到 First Silicon 的验证与 Bring-up](01-validation-bringup.md)
- [认证、法规与量产测试](02-certification-production.md)

## 本章检查点

- 能把一个空口失败映射到 model、RTL、Firmware、MAC/PHY/RF 或板级证据。
- 认证能力、法规限制和产品 feature bitmap 使用同一能力源。
- 量产数据可追溯到算法、工具、板型和版本，OTP 写入有不可逆保护。
