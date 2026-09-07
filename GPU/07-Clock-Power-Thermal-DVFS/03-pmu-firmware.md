# 03 PMU 独立微控制器架构与 Power Capping

## 1. PMU (Power Management Unit) 硬件架构

- **微架构**：PMU 通常是一颗片内独立的安全 RISC-V / Falcon 微控制器，运行隔离的受信任固件（Firmware）。
- **职责**：
  - 监控板级 VRM 供电芯片的电流与电压遥测数据（通过 I2C/PMBus）。
  - 执行毫秒级闭环 PID 算法控制 Boost 频率。
  - **Power Capping（动态功耗封顶）**：严格限制芯片总功耗不超过系统管理员配置的上限（如限制在 300W），防止数据中心供电配电单元（PDU）过载跳闸。
