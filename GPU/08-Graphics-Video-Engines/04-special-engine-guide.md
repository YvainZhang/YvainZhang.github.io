# 04 专用引擎工程问题排查与规避

## 1. 常见专用引擎故障排查表

| 故障现象 | 根因诊断 | 解决与排查方法 |
| :--- | :--- | :--- |
| **视频解码器 Hang 死导致进程卡死** | 码流存在非法畸变 NAL 单元，触发硬件解码状态机死锁 | 调用驱动层硬件 Watchdog 重置 NVDEC 引擎，跳过坏帧 |
| **显示画面出现水平撕裂 (Tearing)** | Framebuffer 翻转未与 Display Engine 的 VSync（垂直消隐）信号对齐 | 在 DRM 驱动中开启 `DRM_MODE_PAGE_FLIP_EVENT` 双缓冲同步 |
