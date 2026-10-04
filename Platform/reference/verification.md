# 验证范围与记录

实验结果按执行日期与源码版本解释。当前公开源码见 [下载页](source.md)，操作步骤见 [环境页](../guide/environment.md)。功能回归、性能样本和真实硬件测量分别记录。

## 当前公开源码

2026-10-04 的公开整理校准了 exec / CLOEXEC 解释，并补充 Linux owner 启动发布的同步与定向测试。从公开归档的干净解压目录运行以下六组验证，全部通过；命令、退出码、工具版本及源码标识见 [本轮验证 JSON](../assets/verification-2026-10-04.json)。该记录与下载页中的归档 SHA256 一致。

| 验证组 | 结果 | 具体范围 |
|---|---|---|
| user | PASS | core / Linux、复制、停止、同编号 spawn 语义、裁剪、消费者、机制和反例 |
| startup | PASS | 受控启动顺序、发布前无 READY、回调上下文；注入线程创建错误后的回滚与重试 |
| reproduction | PASS | 单实验入口、包内文档检查、重打包；生成归档 SHA 与下载包相同 |
| freertos | PASS | 官方 POSIX port 下的 core、任务、队列、通知和运行契约 |
| sanitize | PASS | Linux / 机制 ASan、UBSan，另包含定向 startup 测试 |
| tsan | PASS | 普通与定向 Linux runtime 的已执行交错；本轮无 SKIP |

普通回归环境是 aarch64 Alpine / musl / GCC 14.2.0，检测环境是 aarch64 Debian / glibc 2.36 / GCC 12.2.0。源码包不包含生成的库与第三方缓存，依赖先下载并校验，再在无网络容器运行测试。

受控测试通过同步钩子让 owner 先到达入口，核对 started 发布前不能执行 READY 回调；创建错误由测试构建注入，验证回滚与重试路径。它不表示复现了真实资源耗尽事件。普通构建不包含这些钩子，检查工具通过也不穷尽所有交错。

本轮网络、性能、内核构建和 QEMU 没有重新执行，使用下方按日期说明的历史记录。

## 2026-10-02 / 03 基线

| 实验层 | 当时记录 | 支持的结论 |
|---|---|---|
| core / 协议、Linux runtime | PASS | 容量、身份、超时边界、回显、取消、错误协议、恢复、多实例与停止守恒 |
| FreeRTOS V11.1.0 POSIX port | PASS | 同 core 向量、实际任务 / 队列 / 通知与恢复运行 |
| Linux 机制实验 | PASS | fd、IPC、LT / ET、部分写、队列、原子、映射和调用行为 |
| TAP | PASS | 路径、禁止 / 恢复、延迟、方向丢弃和 local route 对照 |
| Linux ASan / UBSan、TSan | PASS | 当时执行路径下的内存、未定义行为与数据竞争检查 |
| QEMU 软件设备 | PASS | UAPI、多实例、probe 回滚、持 fd 解绑和重复退出 |
| 内核 KASAN / lockdep | SKIP | 该配置没有启用对应检查 |
| 性能 | 两额度 × 五轮 × 一万请求，零失败 | 当前下载的历史样本与对应场景下的分位数 |

用户态环境是 aarch64 Linux、Alpine 3.22、musl 1.2.5、GCC 14.2.0；检测镜像使用 Debian bookworm / glibc / GCC 12。内核基线为 Alpine `6.12.111-0-virt` 和匹配头文件，QEMU ARM64 virt、TCG、512 MiB、2 CPU、无网络，未启用 PREEMPT_RT。

源码后续发生修订，以上记录保留原日期与覆盖范围。[历史性能 CSV 和汇总](../cases/02-inflight-budget.md)作为案例数据公开；重新构建的性能输出应另外保存，不能覆盖为同一轮结果。

## 验证仍需目标平台支持的部分

FreeRTOS POSIX port 使用宿主线程，不能据此推出 MCU 中断响应或最坏时延。QEMU 模块展示软件设备的对象寿命，没有覆盖真实 DMA、MMIO、缓存一致性、硬件 IRQ、时钟与电源。真实芯片选型、板级功耗、热、升级掉电和量产可靠性需要对应材料与目标测试。

性能比较当前没有 CPU profile 来证明瓶颈，也没有通过正常请求样本证明故障期停止预算。案例中保留请求模型、样本轮数、零失败及未知项，便于复查结论的范围。

复现时记录命令、退出码、工具版本和源码 SHA。超时、工具限制或未启用配置都明确记录，错误退出不能当成预期失败通过。
