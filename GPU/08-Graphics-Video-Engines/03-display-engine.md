# 03 Display Engine 显示控制器与扫描流水线

## 1. Display Engine 硬件组成

- **Display Pipe**：包含硬件色彩空间转换（CSC）、HDR 色调映射（Tone Mapping）与硬件光标图层叠加（Hardware Cursor Overlay）。
- **Display Stream Compression (DSC)**：硬件实时无损压缩协议，支撑单根 DisplayPort 2.1 / HDMI 2.1 线缆输出 4K 240Hz / 8K 60Hz 画面。
