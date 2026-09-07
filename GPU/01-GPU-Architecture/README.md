# 01 GPU 总体架构

本模块建立现代高性能 GPGPU / 渲染 GPU 的芯片级宏观架构视图。学习完成后，读者应能够清晰剖析一颗顶级 GPU（如 Hopper/Blackwell 或 CDNA3 架构）的 Top-Level 框图、PCIe BAR 空间划分、时钟/电源拓扑、软硬件执行边界以及流片后的 Bring-up 流程。

## 学习目标

- 深入理解 GPU 算力密度、显存带宽与能效比（PPA）的权衡设计。
- 掌握 GPU Top-Level 层次化拓扑：GPC $\rightarrow$ TPC $\rightarrow$ SM/CU $\rightarrow$ NoC $\rightarrow$ L2/HBM。
- 熟练分析 PCIe BAR0/BAR1 空间映射、Doorbell 机制与 Resizable BAR (ReBAR) 优化。
- 掌握 Clock/Reset/Power 域的边界控制、上电时序与 CMOS 闩锁效应规避。
- 掌握芯片流片后 Bring-up 实验室七步点亮法与软硬件协同验证。

## 章节导航

1. [GPU 芯片定义与 PPA 权衡](01-gpu-fundamentals.md)
2. [Block Diagram 与 GPC/TPC/SM 层次拓扑](02-block-diagram-gpc-sm.md)
3. [PCIe BAR 空间与 MMIO 控制映射](03-memory-map-bar-space.md)
4. [Clock、Reset 与 Power Domain 划分](04-clock-power-domains.md)
5. [软硬件交互边界与执行模型](05-hardware-software-boundary.md)
6. [芯片流片与 Bring-up 工程方法论](06-tapeout-bringup-methodology.md)
7. [架构审阅清单与自测](07-review-debug-self-test.md)
8. [架构启动与 Bring-up 故障案例](08-cases-debug.md)
9. [芯片算力、面积与显存带宽定量推演](09-engineering-analysis.md)
