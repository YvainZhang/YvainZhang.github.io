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
