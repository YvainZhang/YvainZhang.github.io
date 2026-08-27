# 复位架构、电源域管理、DVFS 调压调频与系统休眠完全指南

## 1. 电源域（Power Domain）分层与上下电标准硬件时序

在多核 SoC 中，为降低静态漏电功耗（Static Leakage），芯片被划分为多个物理隔离的电源域：

```mermaid
flowchart TD
    subgraph Power_Domains ["SoC 物理电源域划分"]
        AON["1. AON 域 (Always-On Domain: 永远供电)\n• 电源管理单元 (PMU)\n• 实时时钟 (RTC)\n• 唤醒引脚控制器 (Wakeup Controller)\n• AON 静态保持 SRAM"]

        CPU_PD["2. CPU Cluster 域 (支持独立关断与 DVFS)"]
        GPU_PD["3. GPU / NPU 算力域 (大功率独立可关断域)"]
        PERIPH_PD["4. 外设与多媒体域 (随外设空闲动态关断)"]
    end

    AON -->|输出电源门控使能 PwrEn & 隔离控制 IsoEn| CPU_PD & GPU_PD & PERIPH_PD
```

### 电源域标准下电（Power-Down）与上电（Power-Up）七步硬件时序

```mermaid
sequenceDiagram
    participant OS as Linux 内核 / PMU 驱动
    participant PMU as SoC 片上电源管理单元
    participant Iso as 边界隔离单元 (Isolation Cells)
    participant Sw as 功率开关晶体管 (Power Switches)
    participant IP as 目标 IP 核心 (如 GPU 域)

    Note over OS,IP: 1. 严格标准的下电时序 (Power-Down)
    OS->>IP: 1. 软件排空 DMA 事务与总线挂起请求 (Quiesce)
    OS->>IP: 2. 关闭模块时钟 (Clock Gating)
    OS->>IP: 3. 拉低复位信号 (Assert Reset)
    PMU->>Iso: 4. 使能边界隔离信号 (Enable Isolation: 将输出信号钳位在固定 0/1, 防止浮空漏电)
    PMU->>Sw: 5. 断开供电开关 (Disable Power Switches: 域彻底断电)

    Note over OS,IP: 2. 严格标准的上电时序 (Power-Up)
    PMU->>Sw: 1. 闭合供电开关 (Enable Power Switches)
    PMU->>PMU: 2. 等待供电稳定 (Wait for Power-Good / Slew-Rate Delay)
    PMU->>Iso: 3. 解除边界隔离 (Disable Isolation: 恢复数字信号通路)
    OS->>IP: 4. 开启模块时钟 (Enable Clock)
    OS->>IP: 5. 解除复位信号 (Deassert Reset)
    OS->>IP: 6. 恢复寄存器上下文配置 (Restore Context)
```

---

## 2. 动态电压频率缩放（DVFS）升降调节时序法则

为实现性能与能效的最佳匹配，CPU 核心支持在不同 **OPP（Operating Performance Points: 电压-频率元组）** 之间动态切换：

```mermaid
flowchart TD
    subgraph DVFS_Up ["1. 升频升压时序 (必须: 先升压, 后升频)"]
        direction TB
        Up1["第一步: 通知 PMIC 升高电压 (如 0.8V -> 1.0V)"] --> Up2["第二步: 硬件延时等待电压稳定 (Regulator Settling Time: 约 20~50μs)"]
        Up2 --> Up3["第三步: 配置 PLL 升高工作主频 (如 1.2GHz -> 2.0GHz)"]
    end

    subgraph DVFS_Down ["2. 降频降压时序 (必须: 先降频, 后降压)"]
        direction TB
        Down1["第一步: 配置 PLL 降低工作主频 (如 2.0GHz -> 1.2GHz)"] --> Down2["第二步: 通知 PMIC 降低电压 (如 1.0V -> 0.8V)"]
        Down2 --> Down3["第三步: 电压缓慢下落至 0.8V (功耗平滑降低)"]
    end
```

### 违背调节顺序的微架构物理后果：
- **若升频时“先升频、后升压”**：CPU 逻辑在 $0.8\text{V}$ 低压下，MOS 管充放电速度无法支撑 $2.0\text{GHz}$ 的极窄时钟周期，信号在时钟上升沿到来时未能完成建立（**Setup Time Violation**），触发随机逻辑翻转与系统死锁崩溃！

---

## 3. 全系统休眠（System Suspend）与自刷新（Self-Refresh）全景机制

```mermaid
sequenceDiagram
    participant OS as Linux 内核 (PM Core)
    participant DDRC as DDR 内存控制器
    participant DRAM as 外部 DDR 物理颗粒
    participant TF_A as TF-A 固件 (EL3 / PSCI)
    participant AON as AON 常开唤醒控制器

    Note over OS,TF_A: 1. 进入深度休眠 (Suspend to RAM)
    OS->>OS: 挂起所有外设驱动 (dpm_suspend)
    OS->>DDRC: 驱动 DDR 控制器向 DRAM 下发 Self-Refresh 命令
    DRAM->>DRAM: 外部 DDR 颗粒进入自刷新模式 (仅依靠内部定时器维持电荷, 功耗 < 10mW)
    OS->>TF_A: 通过 PSCI CPU_SUSPEND SMC 调用陷入 EL3
    TF_A->>AON: 配置唤醒源引脚 (Wakeup Pin / RTC), 关闭全芯片非常开电源域
    TF_A->>TF_A: 执行 WFI 指令 (CPU 彻底停机)

    Note over DRAM,AON: 2. 外部事件唤醒 (System Resume)
    AON->>AON: 检测到 GPIO 按键下降沿或 RTC 定时中断
    AON->>TF_A: 唤醒 CPU 供电域与时钟, CPU 从 AON Reset Vector 取指
    TF_A->>DDRC: 解除 DDR 自刷新模式 (Exit Self-Refresh)
    DDRC-->>TF_A: DDR 数据完整保留且访问恢复可用
    TF_A-->>OS: ERET 返回 Linux 内核恢复上下文
    OS->>OS: 依次恢复各外设驱动 (dpm_resume)
```

---

## 4. 常见电源与复位故障排查手册

| 故障现象 | 硬件/驱动微架构根因 | 排查与修复方法 |
| :--- | :--- | :--- |
| **CPU 满载加频瞬间系统突发重启或死机** | DVFS 驱动中配置的 PMIC 电压建立时间（Settling Time）过短，时钟在电压尚未达到目标值时提前提升 | 检查 PMIC 手册中的 Slew Rate（如 $10\text{mV}/\mu\text{s}$），在 DTS 的 regulator 节点中补齐 `regulator-ramp-delay` 参数 |
| **某外设电源域下电后，AON 域芯片异常发热漏电** | 隔离单元（Isolation Cells）未使能或使能时序落后于供电切断，下电域引脚呈现浮空电平（Floating），向常开域反向注入击穿电流 | 严格检查 PMU 固件中的下电时序，确保在断开 Power Switches 之前隔离信号（IsoEn）已完全置位 |
| **系统从 Suspend 唤醒后内存数据全部乱码** | DDR 进入自刷新（Self-Refresh）后，板级 VDDQ 供电被外部电源芯片意外切断；或唤醒退出自刷新时未等待足够的恢复时间（$t_{\text{XS}}$） | 用示波器监控 Suspend 期间 DDR 供电轨是否恒定保持；检查 DDR 控制器退出自刷新的时序延时配置 |
