# Lab 03: 开源 GPU 驱动任务提交与跟踪

## 实验目标

在 Linux 环境下，通过 `bpftrace` 动态跟踪 Linux DRM（Direct Rendering Manager）调度器核心函数 `drm_sched_job_run`，观测用户态应用程序如何通过 Ring Buffer 和 Doorbell 将计算指令提交至底层 GPU 硬件。
