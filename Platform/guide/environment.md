# 实验环境索引

源码采用共用 core 和独立 runtime，Linux 与 RTOS 分别安排实验步骤。

| 实验 | 环境与执行步骤 |
| --- | --- |
| Linux 机制、异步 SDK、启动回归与检测工具 | [Linux 环境准备](https://xidianedu.cc/tech/linux/guide/environment/) |
| TAP 与 namespace 网络路径 | [Linux 环境中的网络实验](https://xidianedu.cc/tech/linux/guide/environment/) |
| ARM64 内核软件设备与专用 QEMU | [Linux 环境准备](https://xidianedu.cc/tech/linux/guide/environment/) |
| FreeRTOS V11.1.0 POSIX port 与任务级回归 | [FreeRTOS 实验环境](https://xidianedu.cc/tech/rtos/Practice/01-environment/) |

先从 [源码页](../reference/source.md)取得归档并核对 SHA256，再按对应系统的步骤准备环境。所有章节中的源码路径相对于解压后的 `platform-lab-source/` 根目录。

共用业务状态转换通过 `make -C platform core-test` 核对。运行时行为需要各端的任务或线程级回归；换到目标芯片后补充硬件与 port 验证。已执行范围见 [验证记录](../reference/verification.md)。
