# 04 片上存储工程问题排查与规避

## 1. 片上 SRAM 常见故障与工程规避

| 故障现象 | 根因诊断 | 规避与解决方案 |
| :--- | :--- | :--- |
| **计算结果出现历史旧数据（数据踩踏）** | DMA 尚未完成传输，脉动阵列提前开始读取 Ping-Pong Buffer | 检查硬件同步 Barrier 与 `DMA_Done` 事件触发条件 |
| **SRAM 读写时序违例 (Timing Violation)** | 高温下 SRAM 建立时间（Setup Time）不足 | 插入 SRAM Pipeline 寄存器阶段，或降低工作电压频率 |
