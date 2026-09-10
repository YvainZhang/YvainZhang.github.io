# 04 系统对比与选型

经过对 FreeRTOS 极简调度核与 Zephyr 现代全栈操作系统的微观源码级解剖，我们必须站在系统架构师的高维视角，从**设计哲学、调度确定性、驱动可移植性、内存安全、Flash/RAM Footprint 以及工业落地场景**进行严谨、客观、量化的多维横向对比。

```mermaid
graph LR
    subgraph Dimension["六大对比研判维度"]
        D1["01 设计哲学与架构范式"]
        D2["02 调度确定性与延迟实测"]
        D3["03 驱动可移植性与解耦度"]
        D4["04 内存保护与安全合规认证"]
        D5["05 资源开销 Footprint 极值"]
        D6["06 工业/车规/IoT 选型决策树"]
    end

    Dimension --> Decision["最终技术选型决策 (Go / No-Go)"]
```

## 篇章目录

1. [设计哲学与架构范式](01-philosophy-architectural-paradigm.md)
   - “纯净轻量调度库” vs “平台化全栈生态系统”
   - 代码组织、构建系统（Make/CMake vs West）与学习曲线权衡

2. [调度机制与实时确定性](02-scheduler-determinism-benchmark.md)
   - 调度算法复杂度深度对比（双向链表/位图 CLZ vs 多队列/红黑树）
   - 中断延迟、上下文切换延迟与抖动（Jitter）实测指标量化

3. [硬件抽象与驱动可移植性](03-hardware-abstraction-portability.md)
   - 原厂供应商 HAL 绑定 vs DeviceTree/Kconfig 驱动模型
   - 换主控芯片（Pin-to-Pin 或跨架构更换）时的重构成本差异

4. [内存保护与安全合规](04-security-memory-isolation.md)
   - 任务级内存隔离方案（FreeRTOS-MPU vs Zephyr Userspace/Memory Domains）
   - 车规与工控安全认证（SafeRTOS / IEC 61508 / ISO 26262 / PSA Certified）

5. [资源占用与测量](05-footprint-resource-tradeoffs.md)
   - 最小化配置（Minimal Configuration）Flash 与 RAM 极值占用
   - 中等功能（带网络、文件系统、外设驱动）下的真实资源膨胀曲线

6. [场景选型决策树与选型矩阵](06-selection-decision-tree.md)
   - 什么时候必须坚守 FreeRTOS？
   - 什么时候应当果断切换到 Zephyr？
   - 工业自动化、汽车电子、穿戴式 BLE 与智能家居设备选型评分矩阵
