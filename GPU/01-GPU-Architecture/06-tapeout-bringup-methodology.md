# 06 芯片流片与 Bring-up 工程方法论

## 1. 芯片研发阶段推进路线图

```mermaid
graph LR
    Spec["架构 Spec 定义 (C-Model)"] --> RTL["RTL 设计与验证 (SystemVerilog)"]
    RTL --> Emulation["硬件仿真 (Zebu / Palladium / FPGA)"]
    Emulation --> Tapeout["流片 (Tapeout to TSMC/Samsung)"]
    Tapeout --> ATE["晶圆与封测 (ATE / SLT 测试)"]
    ATE --> FirstSilicon["首片回片 (First Silicon Arrival)"]
    FirstSilicon --> Bringup["实验室 Bring-up 点亮"]
    Bringup --> AlphaDriver["驱动与算子库联调"]
    AlphaDriver --> MassProd["大规模量产与交付"]
```

---

## 2. Bring-up 实验室七步点亮法

当首颗工程样片（A0 Stepping）从封装厂返回实验室后，芯片与系统软件团队严格执行以下阶段检查：

1. **电源与阻抗静态测量**：万用表测量各供电轨（VDD_CORE, VDD_MEM）对地阻抗，确认无短路；示波器监测上电时序与电压纹波。
2. **JTAG 链路打通**：通过 JTAG 边界扫描链（Boundary Scan）读取 Chip ID、Device ID 和 Revision 寄存器。
3. **PMU 与基础时钟点亮**：加载 PMU ROM 基础固件，配置 PLL 锁相环输出基准 Core Clock（通常先以 200MHz~400MHz 安全低频运行）。
4. **PCIe 链路协商 (Link Training)**：插入 Host 服务器，通过 `lspci` 确认能够识别 Vendor ID / Device ID，协商成功至 Gen1/Gen2 模式。
5. **BAR0 MMIO 读写自检**：驱动向 BAR0 基础寄存器写入 Pattern 并读回校验，验证 CPU 对 GPU 寄存器总线通信正常。
6. **显存控制器与 Memory BIST**：初始化 HBM/GDDR PHY，执行片上 MBIST（Memory Built-In Self-Test），确认全容量显存无物理坏块。
7. **首个 Compute Kernel 执行**：下发极简 VectorAdd 算子，验证 GigaThread 调度器、Warp 发射逻辑与 L2/显存写回闭环。
