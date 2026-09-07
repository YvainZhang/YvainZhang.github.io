# 03 GPU Hang 诊断与 XID 报错体系全解析

## 1. 经典 GPU XID 错误码原厂速查表

| XID 编号 | 官方定义 | 硬件根因 | 原厂排查方法 |
| :--- | :--- | :--- | :--- |
| **XID 13** | Graphics Engine Exception | 驱动向硬件发射了非法格式的指令包 | 检查 UMD 编译版本与 KMD 固件兼容性 |
| **XID 31** | GPU MMU Page Fault | 线程访问了越界显存或已被释放的指针 | 开启 `cuda-gdb` 或 Sanitizer 抓取精确 VA |
| **XID 43** | GPU Stopped Processing | GPU 核心死锁或硬件供电断开 | 检查散热风扇、电源供电插头与硬件日志 |
| **XID 62** | Internal Microcontroller Breakpoint | PMU / 固件微控制器崩溃 | 升级 VBIOS / PMU 固件至最新稳定版本 |
| **XID 79** | GPU Fallen Off the Bus | PCIe 链路中断，设备彻底在总线失联 | 检查 PCIe 插槽物理接触、供电及 SerDes 信号质量 |
