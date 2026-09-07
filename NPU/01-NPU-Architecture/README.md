# 01 NPU 总体架构与计算范式

本模块建立专用 AI 加速芯片（DSA / NPU）的全局微架构视图，对比控制流与数据流驱动模型，分析 Host-Device 交互拓扑、时钟电源域与流片 Bring-up 流程。

## 学习目标

- 深入理解专用领域架构（DSA）的设计哲学与能效比优势（Amdahl 定律扩展）。
- 掌握空间架构（Spatial Computing）与 2D 脉动阵列数据流拓扑。
- 掌握 Host-Device 异构交互边界：Task Queue、Descriptor Ring 与 Doorbell 机制。
- 掌握 Clock/Power 域划分与微秒级电源门控（Power Gating）策略。
- 掌握 Bit-Exact 黄金模型验证与 Bring-up 实验室七步点亮法。

## 章节导航

1. [DSA 专用领域架构设计哲学与 PPA](01-dsa-fundamentals.md)
2. [空间架构与数据流拓扑 (Spatial Architecture)](02-spatial-systolic-topology.md)
3. [Host-Device 异构交互边界与 PCIe/AXI 接口](03-host-device-interface.md)
4. [Clock、Reset 与 Power Domain 划分](04-clock-power-domain.md)
5. [NPU 流片与 Bring-up 工程方法论](05-tapeout-bringup-methodology.md)
6. [架构审阅清单与自测](06-review-debug-self-test.md)
7. [NPU Bring-up 故障与 Host 握手案例](07-cases-debug.md)
8. [脉动阵列算力密度与 PPA 定量推演](08-engineering-analysis.md)
