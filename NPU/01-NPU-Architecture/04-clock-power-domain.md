# 04 Clock、Reset 与 Power Domain 划分

## 1. NPU 时钟与电源域拓扑

- **NPU Core Clock (1.0GHz ~ 1.8GHz)**：驱动脉动阵列与 VPU 向量流水线。
- **SRAM Clock**：片上 Scratchpad SRAM 时钟（通常与 Core Clock 同频或 1/2 降频降压运行）。
- **AXI / NoC Clock (800MHz ~ 1.2GHz)**：负责跨 Tile 通信与系统总线对接。
- **细粒度电源门控 (Power Gating)**：当模型处于非计算间隙（如等待摄像头帧输入）时，硬件自动在 100ns 内切断脉动阵列供电，仅保留 SRAM Retention 供电。
