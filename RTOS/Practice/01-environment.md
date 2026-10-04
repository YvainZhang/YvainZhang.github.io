# FreeRTOS 实验环境

本组使用官方 FreeRTOS-Kernel V11.1.0 的 POSIX port，在独立 ARM64 Linux 工具容器中运行。宿主可以是 macOS；任务由 POSIX port 承载，实验尚未包含 MCU 启动代码或板级中断。

## 源码与依赖

从 [源码页](https://xidianedu.cc/tech/platform/reference/source/)下载归档并核对 SHA256。在宿主终端执行：

```sh
tar -xzf platform-lab-source.tar.gz
cd platform-lab-source
docker build --platform linux/arm64 -t platform-arch-lab:alpine3.22 -f scripts/deps/Dockerfile .
docker run --rm --platform linux/arm64 \
  -v "$PWD:/work" -w /work platform-arch-lab:alpine3.22 \
  sh scripts/deps/fetch-freertos.sh
```

下载脚本校验固定版本的上游归档 SHA256，依赖保存于 `third_party/` 并保留原许可。镜像的软件仓库尚未锁定快照，重新构建时记录实际工具版本。

## 运行任务级回归

继续在宿主源码根目录执行：

```sh
./scripts/run-container.sh freertos
```

该脚本使用无网络的一次性容器。需要分步观察时，在同一目录执行：

```sh
./scripts/run-container.sh shell
```

容器内目录为 `/work`，执行：

```sh
make -C platform core-test freertos-test
```

`core-test` 核对纯 C 状态转换，`freertos-test` 在真实 FreeRTOS 任务中运行 core 向量及 runtime 回归，覆盖复制、队列满、旧代际、恢复、多实例和停止。按输出中的 test / result 与退出码确认结果；公开快照的已执行范围见 [验证记录](https://xidianedu.cc/tech/platform/reference/verification/)。

## 迁移到 MCU

先换到目标 port、启动和链接配置，再核对 tick 分辨率与回绕、中断优先级、FromISR API、临界区、任务栈、heap、DMA/cache 和设备完成。宿主的 heap_free、栈水位与延迟分位不能覆盖全部 pthread 开销，也不能作为 MCU 最坏执行时间。

下一章从 [队列与 owner](02-queue-owner.md)进入实际数据路径。
