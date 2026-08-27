# 01 SoC 总体架构

本模块建立 SoC 的全局视图。学习完成后，应当能够拿到一张芯片框图、一份地址表和若干启动日志，判断系统中“谁发起访问、经过哪里、到达哪里、由谁供时钟和复位、故障应该从哪一层开始查”。

## 学习目标

- 解释 SoC、CPU、MCU、MPU、ASIC、FPGA 等概念之间的区别。
- 从计算、存储、互联、I/O、控制、安全和调试七个维度拆解一颗 SoC。
- 阅读 Block Diagram，并识别数据、控制、中断、时钟、复位和电源关系。
- 阅读 Address Map，区分内存地址、MMIO 地址、CPU 物理地址、总线地址和设备 DMA 地址。
- 理解 Power Domain、Clock Domain、Reset Domain 的边界及正确启停顺序。
- 从软件的一次寄存器访问或一次 DMA 传输反推硬件完整路径。
- 使用统一清单审阅一个陌生 SoC 的总体设计或 BSP 初始资料。

## 章节导航

1. [SoC 的定义、组成与分类](01-soc-fundamentals.md)
2. [Block Diagram 阅读与系统分解](02-block-diagram.md)
3. [Address Map 与地址译码](03-address-map.md)
4. [Clock、Reset 与 Power Domain](04-clock-reset-power.md)
5. [地址流、数据流、控制流与中断流](05-system-flows.md)
6. [通用教学 SoC 端到端案例](06-generic-soc-case-study.md)
7. [架构审阅、调试清单与自测](07-review-debug-self-test.md)

## 建议学习方式

先快速通读 1～5 章，建立术语和连接关系；随后完整推演第 6 章；最后在不看正文的情况下完成第 7 章的问题。遇到 AXI、MMU、Cache、DMA 等尚未展开的概念时，当前阶段只需要知道它在系统中的位置和职责，细节由后续模块负责。

## 本模块边界

本模块负责总体关系，不重复后续模块的协议级细节。例如本模块说明 CPU 经 AXI/NoC 访问 DDR，但不会穷举 AXI 五通道握手；说明 MMIO 区域应使用 Device 属性，但页表描述符编码留到模块 04；说明非一致 DMA 需要 Cache 维护，但具体 API 和 Barrier 顺序留到模块 06。
