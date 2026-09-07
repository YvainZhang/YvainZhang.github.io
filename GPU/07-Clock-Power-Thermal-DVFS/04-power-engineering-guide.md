# 04 电源功耗工程问题排查与规避

## 1. 常见电源与功耗故障排查

| 故障现象 | 根因诊断 | 排查手段与解决方案 |
| :--- | :--- | :--- |
| **GPU 算力性能周期性突降 50%** | 触发 Thermal Throttling 或 Power Capping 频繁降频 | 使用 `nvidia-smi -q -d PERFORMANCE` 查看降频标志位 |
| **服务器突然掉电关机 (Power Surge)** | 瞬态负载跳变产生超高 $di/dt$ 浪涌电流，触发主板 OCP（过流保护） | 在固件中开启 Clock Ramping 渐进升频缓冲策略 |
| **高负载计算出现数值随机 Mismatch** | VRM 供电在极高电流下发生电压跌落（Voltage Droop），引起时序违例 | 提升供电电容冗余，或通过固件对最低电压施加安全 Offset |
