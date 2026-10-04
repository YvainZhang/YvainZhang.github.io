# 实验源码与许可

[下载公开源码包](../assets/platform-lab-source.tar.gz)，解压后的顶层目录是 `platform-lab-source/`。

```text
SHA256
29659eabaf31dfb9dcfdc9ff9b15505fd98c9f95a3db8ee792f476da2c31350c
```

源码包包含 Linux 机制实验、异步 SDK 的 core 与 Linux / FreeRTOS runtime、独立设备模拟器、TAP 链路、专用 QEMU 模块及运行脚本。源码与公开教程按具体实验对应；包内 README 给出完整命令，`SOURCEFILES.json` 列出文件 SHA256。

## 解压与运行

在宿主执行：

```sh
shasum -a 256 platform-lab-source.tar.gz
tar -xzf platform-lab-source.tar.gz
cd platform-lab-source
docker build --platform linux/arm64 -f scripts/deps/Dockerfile -t platform-arch-lab:alpine3.22 scripts/deps
./scripts/run-container.sh user
./scripts/run-container.sh startup
./scripts/run-container.sh reproduction
```

`user` 检查 core / Linux、裁剪功能、消费者链接、机制实验、deadline 变异反例和有界 ABBA；`startup` 另以编译时同步钩子控制启动顺序，检查首次 READY 回调上下文，注入线程创建错误后核对回滚与重试；普通构建不包含这些钩子。普通与定向 Linux runtime 测试都包含直接 dup2 与同编号 spawn 动作的 CLOEXEC 对照。`reproduction` 检查本包文档目标、重新打包及 fd / epoll / memory 单独入口。

`deps` 获取并校验 FreeRTOS，随后单独运行 `freertos`；Sanitizer、TSan、性能、TAP 与 ARM64 内核入口各有对应 suite，详见 [环境说明](../guide/environment.md)。结果记录在 `build/verification/`，每轮关联当前源码 hash 与实际命令退出码。

## 按章节观察

`./scripts/run-container.sh shell` 打开位于 `/work` 的一次性 Linux 环境。在其中执行：

```sh
make -C labs all
./build/labs/mechanisms --list
./build/labs/mechanisms fd
./build/labs/mechanisms epoll
./build/labs/mechanisms memory
```

其他选择为 `rollback`、`save`、`ipc`、`blocking`、`stream`、`partial-write`、`queue`、`atomic`、`extra`。每个选择仍核对自身资源与 fd 基线；无参数或 `all` 运行全部机制。`make -C labs test` 还检查多文件构建与库，readelf 输出在 `build/labs/elf-header.txt`。

## 来源和许可边界

自编代码使用 MIT；`kernel-labs/archlab/archlab.c` 声明 GPL-2.0-only，模块按该许可使用。FreeRTOS-Kernel V11.1.0 是独立上游依赖，获取脚本校验固定 SHA256，原许可随下载文件保留。归档提供源码，目标架构 / libc 的库由读者重新编译。

该归档采用逐文件清单生成；构建输出与第三方下载缓存由命令在本地生成。`make package` 只按源码清单重新归档，相同内容生成相同 SHA。

当前包的实际结果见 [验证记录](verification.md)。FreeRTOS POSIX port 与 QEMU 软件设备分别提供运行时和寿命机制对照，真实 MCU 时序与板级硬件结论需要对应测试。
