# 04 调度器工程问题排查与规避

## 1. 常见调度器故障排查表

| 故障现象 | 根因诊断 | 规避与解决方案 |
| :--- | :--- | :--- |
| **NPU 计算流挂死在 Wait Event** | 前置 DMA 因异常中断未能发出 Set Event 信号 | 开启硬件 Watchdog 定时器，超时自动触发异常中断上报 |
| **指令队列溢出 (Queue Overflow)** | CPU 写入任务速度远快于 NPU 消费速度，且未检查 Queue 满标志 | 驱动层维护软件滑动窗口信用机制（Credit Flow Control） |
