# RF 指标、校准与失效模式

RF/Analog 把数字 I/Q 转为受法规约束的射频信号，也把微弱且受干扰的信号送入 ADC。芯片“能收发”只是 Bring-up 起点，量产一致性取决于校准、温度补偿和 Board Data。

## 关键模块

- TX：DAC、mixer、PLL/VCO、driver、PA、filter/FEM。
- RX：filter/switch、LNA、mixer、VGA、ADC 与 AGC loop。
- 公共：reference crystal、供电、天线、band switch 和 coexistence path。

## 指标的因果关系

| 指标 | 说明 | 常见根因方向 |
|---|---|---|
| TX power | 输出功率与精度 | PA/gain table、供电、温补 |
| EVM | 星座误差 | IQ、phase noise、PA 非线性、CFO |
| Frequency error | 载波频偏 | crystal/PLL/温度 |
| Spectral mask/spur | 带外能量 | PA、PLL、时钟耦合、滤波 |
| Sensitivity/PER | 指定条件下接收能力 | NF、AGC、同步、PHY decode |
| RSSI accuracy | 报告功率误差 | RX gain calibration、温补 |

RSSI、SNR 与 EVM 不能盲目跨芯片比较，先确认参考点、单位、per-chain/combined 方式和是否经过校准。

## 校准闭环

```mermaid
flowchart LR
    REF[Known stimulus / loopback] --> MEAS[Measure error]
    MEAS --> SOLVE[Estimate correction]
    SOLVE --> APPLY[Gain/IQ/DC/LO/crystal table]
    APPLY --> VERIFY[Independent verification]
    VERIFY --> STORE[OTP/eFuse/flash/board data]
```

常见项目包括 TX power、RX gain、DC offset、IQ imbalance、LO leakage、crystal trim 和 temperature compensation。必须定义校准条件、算法版本、数据格式、CRC、fallback 和失效策略。

## OTP/eFuse 安全性

OTP 是不可逆资源。写入流程应校验 device identity、board/SKU、目标地址、未烧写状态、电压温度条件与结果 readback；重要字段使用冗余/CRC 和版本。生产工具不得允许任意地址裸写。

## 分层定位

- Conducted 测试正常、OTA 差：优先检查 FEM、天线、Layout 与整机干扰。
- 低 MCS 正常、高 MCS EVM/PER 差：检查 phase noise、IQ、PA linearity 与电源噪声。
- 高低温频偏或功率漂移：检查 crystal/gain 温补表及传感器路径。
- 近距离反而丢包：检查 AGC saturation、LNA bypass 和动态范围。
- 仅特定信道出现 spur/EVM：检查 PLL、时钟谐波、band-edge power 与校准插值。

每个结论都应保存 instrument 配置、cable loss/reference plane、Vector、温度、电压、board revision 和 calibration version，才能复现。

## EVM的可复核计算

用已对齐的理想符号s和测得符号r、按平均参考信号功率归一化：

```text
EVM_rms = sqrt( Σ|r-s|² / Σ|s|² )
EVM_percent = 100 × EVM_rms
EVM_dB = 20 log10(EVM_rms)
```

教学例：RMS EVM=0.03，即3%，约−30.46 dB。不能对3直接取20log而忘记百分比转换。不同仪表的频偏/相位补偿、均衡、symbol选择与归一化会改变结果，比较前需统一设置。

参考：[MathWorks EVM定义与归一化](https://www.mathworks.com/help/comm/ref/comm.evm-system-object.html)。仅在受限的噪声主导模型中，EVM与SNR可建立简单关系；不能把任何实测EVM直接转换成真实链路SNR。

## 接收灵敏度预算

室温热噪声常用近似 `−174 dBm/Hz`，20 MHz带宽积分约−101 dBm。若教学假设NF=5 dB、目标解调所需SNR=10 dB，再留2 dB实现裕量，则估计接收功率门槛约−84 dBm。

这是链路预算，不是某MCS的标准灵敏度限值。实际验收还要限定PSDU长度、PER阈值、bandwidth、coding、温度、输入参考面和干扰条件。

## PA功率与EVM的权衡

提高TX gain可提升输出功率，但接近PA压缩区会放大AM-AM/AM-PM非线性与频谱再生。高阶QAM可能需要更多backoff，因此“所有MCS统一最大功率”未必可行。

校准需把目标power、EVM、spectral mask、温度与FEM路径一起评估；闭环选取有效工作点，而不是只校正一个RSSI或gain offset。

## Conducted/OTA与线损

教学例：仪表设定−60 dBm，经3 dB线缆和2 dB路径衰减，到DUT参考面为−65 dBm。若软件又把已补偿仪表结果重复扣5 dB，会人为制造灵敏度偏差。

Conducted较好而OTA变差可提示天线/布局/整机干扰，但也要确认两测试路径包含的FEM/connector不同。结论应基于实际reference plane，不能一概归因“天线不好”。

## 校准数据生命周期

启动时验证board/SKU、频段、版本、CRC和适用温压；运行时按温度索引或插值；异常时选择已定义fallback或拒绝相关能力。CRC只能发现某类损坏，不能证明数据属于正确板型。

OTP/eFuse不可逆，量产流程应在外部保存预期数据和readback结果，区分测量、求解、验证、烧写。本文不提供任意地址写入操作。

## 复习追问与答案

**近距离反而更差可能是什么？** RX饱和、AGC切换、TX失真或强自干扰；高RSSI不是全链路质量证明。

**怎样区分PLL与PA问题？** 结合功率回退、频偏/相噪、EVM/频谱随信道和功率变化的受控试验，不靠单张星座图唯一归因。

**校准通过为何换板就失败？** FEM、天线、参考面、晶体和供电可能改变，需检查board data是否匹配。
