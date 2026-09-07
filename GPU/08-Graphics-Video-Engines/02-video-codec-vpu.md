# 02 NVENC 与 NVDEC 硬件音视频编解码微架构

## 1. 独立硬件编解码引擎 (NVENC / NVDEC)

- **硬件解耦**：NVENC 与 NVDEC 拥有独立的定点 ASIC 流水线，**执行视频编解码时 SM 计算核心占用率为 0%**。
- **支持标准**：硬件完全覆盖 H.264 (AVC)、H.265 (HEVC) 以及最新开源标准 AV1（支持 8K 60FPS 10-bit HDR 硬编解）。
- **零拷贝流水线**：解码后的 YUV/NV12 原始帧数据直接保留在 GPU VRAM 中，可立即被 Tensor Core 抓取执行 AI 视觉推理（如 YOLO 目标检测），消除 CPU 内存中转。
