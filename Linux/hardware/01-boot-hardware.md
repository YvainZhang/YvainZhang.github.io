# 程序能运行以后，硬件边界还要确认什么

用户态 SDK 可以在容器中启动、收发消息、处理超时。把相同代码搬到开发板上，却可能卡在驱动加载、设备初始化或第一笔传输。这里需要先分清启动链、资源描述和异步硬件访问各自承担的责任。

前置阅读：[内核设备与退出](../mechanisms/10-kernel-lifetime.md)、[构建与 ELF](../mechanisms/02-build-elf.md)。实验条件和命令位置见[环境准备](../guide/environment.md)，代码入口见[源码与版本](https://xidianedu.cc/tech/platform/reference/source/)。

## 沿启动链定位第一处失败

常见嵌入式 Linux 启动链可以写成：

```text
Boot ROM → bootloader → kernel + DTB → rootfs → init → 服务/应用
```

每一段的输入和成功标志不同。bootloader 已经输出串口信息，只能说明早期启动与部分硬件可用；内核已经打印日志，也不说明根文件系统能挂载。根文件系统可用后，服务还可能因为库、权限、设备节点或配置失败。

本实验采用 QEMU ARM64 `virt`，直接加载预构建内核和 initramfs。`/init` 挂载 proc、sysfs、devtmpfs，加载教学模块并运行 UAPI 测试。这个流程覆盖内核到测试程序的路径；Boot ROM、板级 bootloader、电源时序和真实存储启动需要另做板上验证。

排查时保存第一处异常的完整上下文，例如 kernel command line、根文件系统类型、init 的路径与 ELF 解释器。后续报错可能只是这处失败的连锁结果。

## 设备树描述资源与关系

设备树向系统描述设备、地址范围、中断、时钟以及设备间关系。驱动仍要匹配节点、取得资源、初始化设备并承担失败回滚。一个节点出现于 DTS，不代表驱动已经正确工作。[Linux 设备树使用模型](https://docs.kernel.org/6.12/devicetree/usage-model.html)

下面导出 QEMU 自己生成的 DTB。先在宿主项目根目录运行：

```sh
mkdir -p build/vm
qemu-system-aarch64 -machine virt,dumpdtb=build/vm/virt.dtb \
  -cpu cortex-a72 -nographic -nic none
```

随后在挂载同一项目目录的专用 Linux 工具容器内运行：

```sh
dtc -I dtb -O dts build/vm/virt.dtb -o build/vm/virt.dts
```

阅读一个 `reg` 字段时，先找到父节点的 `#address-cells`、`#size-cells` 和可能存在的 `ranges`。设备地址可能需要总线翻译，不能看到一串数就直接把它当 CPU 可访问地址。本教学模块注册软件 platform device，没有虚构 MMIO 或 IRQ 资源。

## 把一次传输的责任写成时间线

考虑上层向总线适配层传入一块 buffer：

| 时点 | 上层看见什么 | 下层需要确认什么 |
| --- | --- | --- |
| 调用传输接口 | 参数通过检查 | 是否复制；是否开始异步访问 |
| 接口返回 | 提交成功或失败 | 返回是否意味着硬件访问已结束 |
| 硬件完成 | 完成通知 | DMA 是否停止；cache 是否同步；buffer 能否复用 |
| 取消或 reset | 请求结束 | 如何确保晚到的完成不访问已回收对象 |

如果接口只把地址交给 DMA，调用返回后立即把 buffer 归池，就可能被下一个请求覆盖。解决办法取决于契约：提交前复制、持续借用到完成，或者显式转移所有权。三种做法有不同的内存和收尾成本，详见[并发与所有权](../mechanisms/07-concurrency-ownership.md)。

CPU 虚拟地址、物理地址和设备使用的 DMA 地址分别处理。驱动应使用适合设备的 DMA API；一致性分配也仍需处理描述符发布等顺序要求。[Linux DMA 指南](https://docs.kernel.org/6.12/core-api/dma-api-howto.html)

## 平台适配时的核对表

| 边界 | 必须确认的内容 | 证据入口 |
| --- | --- | --- |
| 启动 | 镜像、DTB、rootfs、加载地址与启动参数 | 启动日志与构建清单 |
| 资源 | MMIO 范围、IRQ、时钟、reset、电源依赖 | 原理图、DTS、芯片文档与驱动 |
| 内存 | DMA 地址能力、可访问区、cache 与对齐 | DMA 映射结果和板上测试 |
| 异步完成 | 借用时长、失败、取消和解绑后行为 | 接口契约与定向故障测试 |
| 总线恢复 | 断连、复位、超时及晚到完成 | 恢复时序、计数与日志 |

Linux 的 USB 功能驱动、usbcore 和主控 HCD 处于不同层次。移植时把责任落实到具体实现，避免上层和下层各自假设对方已经复制或完成。

这套 QEMU 实验能够验证软件对象的引用与退出。真实 DMA、IRQ、时钟、电源和 MCU 中断上下文需要相应硬件证据。平台选择和验证计划见[从负载选择平台](https://xidianedu.cc/tech/platform/design/05-platform-selection/)。
