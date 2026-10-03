# 09 驱动与软件运行时体系

本章跟踪 GPU 任务如何从软件进入硬件，涉及 **Linux KMD (Kernel Mode Driver / DRM / KMS)、UMD (User Mode Driver)、Ring Buffer 指令提交与 LLVM / PTX / SASS 编译链路**。

## 章节导航

1. [Linux KMD 内核驱动与 DRM / KMS 架构](01-kmd-drm-kms.md)
2. [UMD 用户态驱动与 Ring Buffer 异步提交](02-umd-command-submission.md)
3. [LLVM 后端代码生成与 PTX 到 SASS 编译体系](03-compiler-llvm-ptx-sass.md)
4. [驱动与运行时工程问题排查与规避](04-driver-engineering-guide.md)
