# RVKernel Lab：从千行 OS 到抢占、IPC 与 SMP

运行在 **QEMU virt / RV32** 上的 C 与汇编教学内核。项目从 Seiya Nuta 的 *Operating System in 1,000 Lines* 实践起步，在基础内核上扩展设备中断、用户态抢占、具名管道与多核同步。

[项目源码](https://github.com/YvainZhang/1000-lines-os-practice){ .md-button .md-button--primary }
[阅读完整教程](https://github.com/YvainZhang/1000-lines-os-practice/blob/main/docs/tutorial/README.md){ .md-button }

## 基础与扩展

| 层次 | 实现内容 | 阅读入口 |
| --- | --- | --- |
| 教程基础 | 启动、上下文切换、Sv32 页表、用户态、系统调用、shell 与简化文件系统 | [Lab 01](../Labs/lab01-rv32-boot-trap-paging.md) |
| 设备中断 | PLIC 分发、UART RX 缓冲、VirtIO 完成中断与阻塞等待 | 仓库 `external_handle_irq`、`read_write_disk` |
| 用户态抢占 | SBI TIME 10 ms tick、调度器与 sleep/wakeup | [Lab 02](../Labs/lab02-rv32-timer-preemption-scheduler.md) |
| IPC | 8 个具名管道、256 字节环形缓冲、阻塞读写与 EOF | [Lab 03](../Labs/lab03-rv32-bounded-pipe-ipc.md) |
| SMP | 1～4 hart、SBI HSM 启动、每核状态、PCB 锁与 IPI 唤醒 | [Lab 04](../Labs/lab04-rv32-smp-multicore-ipi.md) |

基础代码与后续扩展以项目提交 `6f2b063`（`16.文件系统`）为分界。教程基础功能归属上游实践，项目增量和边界以[项目 README](https://github.com/YvainZhang/1000-lines-os-practice#readme)为准。

## 学习路径

1. 从[专题实验概览](../Labs/README.md)进入，认识运行环境与四个实验。
2. 按项目的 [11 节完整教程](https://github.com/YvainZhang/1000-lines-os-practice/tree/main/docs/tutorial)学习启动、内存、进程、文件系统、Trap、设备中断、抢占、IPC 和 SMP。
3. 对照[实现讲解](https://github.com/YvainZhang/1000-lines-os-practice/blob/main/docs/IMPLEMENTATION_AND_INTERVIEW_GUIDE.md)，追踪可信栈、丢失唤醒和锁跨上下文切换的交接。
4. 阅读[验证记录](https://github.com/YvainZhang/1000-lines-os-practice/blob/main/docs/VALIDATION.md)，完成一次可复现的改进实验。

课程基于完整参考实现分章讲解；四项扩展尚未拆成逐章可编译版本。

## 运行与自测

依赖 Clang/LLVM（含 LLD、llvm-objcopy）、QEMU RISC-V 和 Bash。项目当前实测环境为 macOS / Homebrew，其他环境需要核对工具链与 OpenSBI。

```bash
git clone https://github.com/YvainZhang/1000-lines-os-practice.git
cd 1000-lines-os-practice
bash run.sh                 # 默认 2 核
# 退出 QEMU 后再运行下一条命令
NCPU=4 bash run.sh           # 4 核
```

进入 shell 后依次输入 `help`、`hello`、`irqstat`、`selftest`。全部自测通过时输出 `SELFTEST PASS`。退出 QEMU 使用 **Ctrl-a，再按 x**。

```bash
python3 scripts/smoke.py     # 顺序验证 1 / 2 / 4 核
```

回归日志保存在项目的 `test-results/`。构建共享根目录产物与磁盘镜像，应顺序执行。自测覆盖功能性行为，不等于性能基准或完整竞态覆盖。

## 实现限制

普通内核路径不可抢占，尚未在真实硬件上验证。10 ms tick 是调度节拍，最坏响应时间尚未测量。

没有完整 POSIX、fork/exec、物理页完整回收、动态 TLB shootdown 或完整负载均衡。UART TX 仍采用短轮询，块设备只有一个在途请求；简化 ustar 文件系统在运行脚本启动时重建镜像，不能据此证明重启持久化或崩溃一致性。

## 来源

- [项目源码、最新说明与验证入口](https://github.com/YvainZhang/1000-lines-os-practice)
- [Operating System in 1,000 Lines 原教程](https://operating-system-in-1000-lines.vercel.app/en/)
- [上游源码与许可声明](https://github.com/nuta/operating-system-in-1000-lines)

