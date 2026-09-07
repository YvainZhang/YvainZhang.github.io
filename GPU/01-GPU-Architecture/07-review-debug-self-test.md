# 07 架构审阅清单、调试清单与自测

## 1. 原厂架构设计审阅检查表 (Architecture Review Checklist)

- [ ] **PPA 达成率**：在目标工艺角（TT/SS 105°C）下，全芯片算力/功耗是否满足 Spec 预算？
- [ ] **NoC 带宽收敛**：跨 SM 到 L2 Cache 的 Bisection 带宽能否支撑 Tensor Core 满载时的操作数吞吐？
- [ ] **CDC 路径无死锁**：所有异步 FIFO 是否均配置格雷码指针与两级触发器同步？
- [ ] **Resizable BAR 兼容性**：BAR1 窗口在 64-bit Host 系统上是否支持动态重配大小？

---

## 2. 经典故障排查思维导图

```text
首发调试故障现象
  ├── JTAG 读不到 IDCODE
  │     ├── 检查 AON 3.3V/1.8V 供电是否正常
  │     ├── 检查 25MHz/100MHz 外部晶振是否起振
  │     └── 检查 Reset 信号是否解除拉高
  ├── PCIe 不识别 (lspci 无设备)
  │     ├── 示波器抓取 PERST# 释放时序与 REFCLK 质量
  │     ├── 检查 PCIe SerDes RX/TX 极性是否反接
  │     └── 强制降频至 Gen1 模式排查信号完整性
  └── VectorAdd Kernel 计算结果全 0 (Mismatch)
        ├── 检查 L2 Cache Flush 指令是否在 Kernel 结束时生效
        ├── 检查 GPU MMU 页表映射物理地址是否正确
        └── 检查 SM 寄存器写回总线使能信号
```
