# 03 端侧摄像头 MIPI 输入 -> ISP -> NPU 零拷贝目标检测流水线

1. 图像传感器通过 MIPI CSI-2 接收原始 Raw 图像。
2. 硬件 ISP 完成去马赛克（Demosaic）、降噪与色彩校正。
3. ISP 将 YUV 帧写入与 NPU 共享的连续物理内存缓冲区。
4. NPU Tensor DMA 直接读取 YUV 缓冲区，硬件完成 NC4HW4 转置后灌入脉动阵列执行 YOLO 推理，全流程 0 次 CPU 拷贝。
