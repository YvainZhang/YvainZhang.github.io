# 多个实例互相拖慢：从进程边界到资源边界

设备模拟器已经独立运行在子进程里，一个实例的内存增长或 CPU 突发，却仍可能拖慢其它实例。地址空间隔离限制了直接内存访问，资源争用和生命周期还需要另外安排。

先读 [进程与 IPC](../mechanisms/05-process-ipc.md)、[尾延迟诊断](02-tail-latency.md)。本章以 Linux 6.12 的 cgroup v2 与 PSI 接口讨论部署设计；当前源码没有配置 cgroup、namespace 或 seccomp 的产品级隔离层。

## 先定义想隔离的故障

| 故障 | 进程边界的作用 | 仍要补的责任 |
| --- | --- | --- |
| backend 用户态崩溃 | SDK 可观察退出与 IPC 断开 | 终结请求、回收通道、诊断与恢复 |
| backend 消耗 CPU | 独立计量较容易 | 配额、优先级、共享资源与控制路径预算 |
| backend 内存增长 | 地址空间分别管理 | 限额、回收 / OOM 行为、服务拒绝 |
| backend 派生子进程 | 单个 PID 不代表全部工作 | 整个后代集合的归属与退出 |
| 设备或内核驱动故障 | 用户态隔离能力有限 | 驱动、硬件与系统级恢复策略 |

进程、namespace、资源控制和访问策略解决不同问题。设计先说明要挡住什么故障，再选择机制，避免把“已经放进容器”当作完整隔离证明。

## CPU 上限不等于控制线程有保留时隙

cgroup v2 的 `cpu.max` 用 quota / period 描述一组任务的带宽上限；`cpu.weight` 表达相对权重。`cpu.stat` 可以观察节流计数与时间。[cgroup v2 CPU 接口](https://docs.kernel.org/6.12/admin-guide/cgroup-v2.html#cpu)

以 `50000 100000` 为设计示例：周期内可消耗 50 ms CPU 时间。两个线程并行运行可以更快花完这笔预算；它不等于“每 100 ms 有连续 50 ms 专门留给 owner”。祖先 cgroup 的约束也可能更早限制执行。

如果 owner 与重计算 backend 共用受限组，backend 可能消耗组内预算，使轻量控制任务也被延迟。分组以后仍要考虑父级预算、设备和其它共享资源；拆组不产生额外的物理 CPU。

需要做的决定是：哪些工作必须保持进展，哪些负载可降级，控制路径怎样在过载时获得处理机会。配额配置必须与 [事件循环预算](01-reactor-scheduling.md)及 deadline 目标一起验证。

## 内存边界会改变延迟和故障终态

`memory.high` 会引入回收与节流，`memory.max` 提供更强的上限，达到无法回收的边界时可能触发组内 OOM；`memory.events` 记录相关事件。[cgroup v2 内存接口](https://docs.kernel.org/6.12/admin-guide/cgroup-v2.html#memory)

因此，“没有被杀掉”不能证明服务仍健康。回收引起的停顿可能先让请求超时，随后才出现 OOM 或退出。预算应覆盖应用、runtime、backend、内核与测量开销，并区分已使用、保留容量和限制值。

SDK 的 `runtime_bytes` 是结构预算，不是整个组的内存计量。降低 `request_limit` 也不自动缩小固定数组。只调整 memory.max 去匹配一个局部 `sizeof`，会把未纳入账本的开销转成运行时故障。

## PSI 连接资源压力与业务进展

PSI 的 cpu / memory / io 接口报告资源阻塞时间：`some` 表示至少有任务受阻，`total` 给出累计微秒；短时间窗口可以比较 total 增量。系统级 CPU `full` 有特殊语义，不能套用为通用停顿比例。[PSI 文档](https://docs.kernel.org/6.12/accounting/psi.html)

压力指标用于形成假设，不能独自指出是哪笔请求或哪个函数的问题。例如 memory pressure 上升且一批请求同时变慢，可以补 fault / 回收与路径时间点；没有这些证据，不能直接认定 RSS 大是根因。

## 只读采样先确认归属

在启用 cgroup v2、对应控制器与 PSI 的专用实验系统中，先确认目标实例实际归属和父级约束。以下路径是实验组占位，不能直接套到未知宿主：

```sh
# 替换为实际实验进程与已存在的实验组。
BACKEND_PID=1234
LAB_CGROUP=/sys/fs/cgroup/platform-experiment
cat /proc/$BACKEND_PID/cgroup
cat "$LAB_CGROUP/cpu.max"
cat "$LAB_CGROUP/cpu.stat"
cat "$LAB_CGROUP/memory.current"
cat "$LAB_CGROUP/memory.events"
cat "$LAB_CGROUP/cpu.pressure"
cat "$LAB_CGROUP/memory.pressure"
cat "$LAB_CGROUP/cgroup.events"
```

本章不给出改写宿主控制组的命令。设置对照负载时，在专用 VM 或已委托的实验层级中由启动管理者创建组、配置预算，再放入目标进程；先验证进程和后代确实在预期组中。

同一轮至少保存开始与结束两份计数。比较 `Δnr_throttled`、`Δthrottled_usec`、`Δmemory.events` 与 PSI 增量，同时记录吞吐、拒绝、超时、p99、owner 进展与停止时间。累计值高不说明当前这轮发生了同样的问题。

## 实例退出要收完整集合

`waitpid` 可以等待直接子进程，不能据此证明它派生的全部工作已结束。cgroup 的 populated 信息能帮助观察组内是否还有进程，但“组空了”仍不表示应用结果账已经闭合。

关闭 admission、终结已有请求、停止 IPC、等待后端与可能的后代，再释放实例。对于不能协作退出的独立用户态后端，外部管理者可以规定分级终止策略；强制终止会留下副作用未知、诊断缺失等问题，需要进入平台故障契约。

当前设备模拟器的直接子进程退出路径有回归，尚没有后代集合、quota / OOM 或整组强制终止的实验。把支持范围写清，避免将已有 waitpid 检查扩大为完整隔离能力。

## 两个实例的对照怎样设计

实例 A 维持稳定控制负载，实例 B 分别制造 CPU、内存和数据突发。先同组，再拆成实验组，保持 A 的负载不变。每次只改变一种限制，检查 A 的尾延迟、失败和停止是否受到影响。

若拆组后 A 仍变慢，继续检查父级限制、共享锁、设备串行能力和同步 callback。隔离边界只有在明确负载、共享资源和故障方式的条件下才有意义。

这些对照尚未执行。本文得到的部署设计要求是：进程归属、资源额度、超限结果与退出责任要成套定义。共同故障模型见 [故障与恢复边界](https://xidianedu.cc/tech/platform/design/10-failure-recovery/)。
