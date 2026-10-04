# 环境准备与实验复现

实验在独立 Linux 工具容器中编译和运行。macOS 用作 Docker 和 QEMU 的宿主，不直接执行 Linux 的 epoll、eventfd、TAP 或内核模块代码。当前内核实验按 aarch64 Linux / musl 与 ARM64 QEMU 配套组织。

## 取得源码

从 [源码页](../reference/source.md)下载归档及核对 SHA256，在宿主终端执行：

```sh
tar -xzf platform-lab-source.tar.gz
cd platform-lab-source
docker build --platform linux/arm64 -t platform-arch-lab:alpine3.22 -f scripts/deps/Dockerfile .
```

以下宿主命令都在解压后的项目根目录执行。Docker 构建需要下载软件包；基础镜像固定 digest，软件仓库尚未固定快照，重建后的编译器与内核版本应重新记录。

## 进入单章实验环境

在宿主终端打开交互容器：

```sh
docker run --rm -it --platform linux/arm64 --network none \
  -v "$PWD:/work" -w /work platform-arch-lab:alpine3.22 sh
```

容器内的项目路径为 `/work`，只挂载当前实验目录。随后可以逐条运行章节里的 `make`、`strace`、`readelf` 等命令，例如：

```sh
make -C labs all
./build/labs/mechanisms fd
make -C platform test feature-test public-test
```

`fd` 只运行 fd 相关实验；全部机制实验使用 `make -C labs test`。Linux SDK 的模拟器和测试程序均由相应 make 目标编译，测试中使用有界等待。输入 `exit` 返回宿主终端。

## FreeRTOS 依赖与完整回归

FreeRTOS 锁定 V11.1.0，下载脚本核对上游归档 SHA256。在宿主终端执行联网的依赖获取步骤，随后使用无网络的一次性容器跑回归：

```sh
docker run --rm --platform linux/arm64 \
  -v "$PWD:/work" -w /work platform-arch-lab:alpine3.22 \
  sh scripts/deps/fetch-freertos.sh
./scripts/run-container.sh user
./scripts/run-container.sh freertos
```

上游依赖存放在 `third_party/`，按原许可使用。FreeRTOS POSIX port 在宿主线程上运行实际任务与调度器；更换到 MCU 时，需要对应 port、启动代码、中断与目标硬件验证。

## 其他实验入口

| 位置 | 命令 | 需要观察的结果 |
|---|---|---|
| Linux 工具容器 | `make startup-test` | 启动状态发布、READY 回调上下文，以及注入线程创建错误后的回滚 |
| Linux 工具容器 | `make -C platform benchmark`，然后 `python3 scripts/benchmark-report.py` | 两个额度各五轮 CSV 与汇总，约十万请求 |
| 宿主项目根目录 | `./scripts/run-container.sh network` | 独立 namespace / TAP 的路径、阻断、延迟与丢弃 |
| 宿主项目根目录 | `./scripts/run-container.sh kernel-build` | 匹配内核 / 头文件与 initramfs |
| 宿主项目根目录 | `python3 kernel-labs/run-vm.py` | 专用 ARM64 QEMU 串口中的 UAPI、解绑与退出结果 |

网络实验在一次性容器中增加 NET_ADMIN / SYS_ADMIN，并创建该容器内的设备节点、接口与 namespace。内核模块只在专用 QEMU 中加载。QEMU 需在宿主安装 `qemu-system-aarch64`；当前软件设备实验不需要 VM 网络。

内核构建依赖 `/lib/ld-musl-aarch64.so.1`，必须使用上述 ARM64 工具容器。内核 image、模块和匹配头文件来自同一次构建环境。若修改架构或发行版，先调整加载器、模块工具链与 VM 启动参数，再核对版本。

## 内存与竞争检查

在宿主项目根目录构建独立 glibc 检测镜像，再分别运行：

```sh
docker build --platform linux/arm64 -t platform-arch-sanitizers:bookworm -f scripts/deps/Dockerfile.sanitizers .
./scripts/run-container.sh sanitize
./scripts/run-container.sh tsan
```

普通 user 回归使用默认容器限制；TSan 检测容器单独放开 seccomp 以允许工具所需的 personality 操作。地址布局不支持时记录 SKIP，检查输出与退出码。当前覆盖情况见 [验证记录](../reference/verification.md)。

## 编译库与集成

在 Linux 工具容器中：

```sh
make -C platform libraries public-test
./build/platform/public-consumer /work/build/platform/device-sim
```

消费者只包含 `sdk.h`，链接顺序为 `-lplatformlinux -lplatformcore -pthread`。下载包提供源码，由当前工具链生成静态库；架构、libc、编译选项或 ABI 变化后重新编译。
