# 认证、法规与量产测试

认证验证互操作与功能，法规限制设备允许怎样发射，量产测试保证每颗芯片和每块板都落在设计窗口内。三者目标不同，不能用一次“综测仪通过”互相替代。

## 三类要求

| 类别 | 关注点 | 典型输出 |
|---|---|---|
| Wi-Fi 互操作认证 | WPA3、PMF、WMM、Wi-Fi 6 等功能行为 | feature/test case 结果 |
| 地区法规 | 信道、功率、DFS、频谱、杂散、SAR | 区域合规报告 |
| 生产测试 | 个体差异、校准、坏件筛选、追溯 | ATE record、calibration/OTP |

具体计划和限值会随产品类别、频段、地区和认证版本变化，文章应记录适用版本和日期，不把实验室/认证机构名称当成法规本身。

## Non-signaling 与 Signaling

Non-signaling 模式直接配置 channel、BW、MCS/NSS、RU、power 和连续/分包 TX，速度快，适合 ATE 和校准；Signaling 模式建立真实链路，覆盖协议与互操作但耗时更长。量产通常用前者筛选，抽样或系统测试用后者补充。

## TX/RX 项目

- TX：power、EVM、frequency error、spectral mask、flatness、spur。
- RX：sensitivity/PER、RSSI accuracy、blocking、adjacent-channel rejection。
- 系统：boot time、Firmware download、HIF、MAC address、OTP/Board ID、低功耗。

测试限值不能等于规范极限，需要预留仪表误差、cable loss、PVT 和量产分布 guard band。

## Calibration 与追溯

每份数据关联 die/lot、board/SKU、tool/algorithm/Firmware version、station、时间、温度、电压和结果 CRC。MAC address、region/SKU、power table、crystal trim 等写入前后都要校验；不可逆 eFuse 操作使用权限、白名单和两阶段确认。

## 从量产返回研发

观察 yield 分布而不是只有 pass/fail。某信道 EVM 缓慢靠近限值、某温度下 crystal trim 双峰、某 board revision RX gain 偏移，都可能是下一批失效的前兆。异常样本应能回到实验室复测，并反向更新设计、校准算法或 guard band。

## 发布前核对

- Capability/feature bitmap 与认证声明一致；
- Regulatory database、Firmware power limit 与 Board Data 不互相覆盖；
- Factory Firmware/command 不进入普通产品攻击面；
- 生产日志不包含密钥或内部访问凭据；
- 不同地区 SKU 不会因错误 country code 解锁非法信道/功率。

## DFS与功率限制在系统中的落点

涉及DFS的产品需将检测、信道状态、CAC/不可用期、运行中事件和切信道策略连接起来。能力声明、Host regulatory、Firmware限制和RF实际输出必须一致。检测后只记录日志而继续调度原信道属于状态闭环缺失。

不同地区、频段、设备类别和测试版本的数值不同；本文讲实现追溯，不提供统一法规限值。项目应把适用规范及版本、测试条件和验收记录纳入证据包，再据此配置产品。

## 量产限值与测量不确定度

教学规格假设某测量值要求不大于−30 dB，扩展测量不确定度取1 dB；若采用简单保守单边guard band策略，内部判定可能设为不大于−31 dB。此处数字仅说明方向，不是Wi-Fi认证限值，也不意味着所有实验室必须采用同一决策规则。

设限要共同考虑仪表、线损、重复性、PVT和产品风险。将测量误差、过程波动和规范裕量混为一个“留1 dB”会失去可追溯性。

## 校准与筛选的区别

校准估计并补偿偏差；筛选判断补偿后的设备是否满足条件。不能让拟合所用的同一组数据独立地证明校准有效，应使用额外信道/功率/温度点验证泛化。

Factory mode直接发测试包有利于效率，但绕过真实关联、加密、BA和功耗路径；抽样signaling与系统测试用于覆盖被绕过的部分。

## 零失败不代表零风险

在独立、同分布Bernoulli试验假设下，n次零失败，对失败概率的95%单边上界为：

```text
p_upper = 1 - 0.05^(1/n)
n=100:  p_upper ≈ 2.95%
n=1000: p_upper ≈ 0.30%
```

这解释了为什么“跑100次没出错”不能证明极低失效率。若测试高度相关、未覆盖触发条件，上界的假设本身也不成立。参考 [NIST exact binomial limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm)。

## 工站相关性与追溯

同一golden unit在不同工站反复测量，先估计station偏移与重复性，再解释批次差异。异常可能来自线缆老化、仪表校准、夹具接触或不同Firmware，而不全是die质量。

记录lot/board、station、工具/算法/limit版本、原始指标、校准结果与最终判定；公开文章仅保留通用字段和匿名化示例。

## 复习追问与答案

**校准后还能用更宽松限值提高良率吗？** 必须先分析测量和失效机制，不能用调整判定掩盖不符合要求。

**为什么认证通过不等于量产稳定？** 认证覆盖特定样品和条件，量产还面对过程分布、工站偏差与版本变化。

**零失败报告还应提供什么？** 样本量、抽样方式、触发场景、相关性、版本和置信假设。
