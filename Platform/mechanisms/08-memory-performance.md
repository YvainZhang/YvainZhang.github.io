# 在途额度变大以后，内存和延迟怎样变化

把请求额度从 4 提高到 16，吞吐会变高吗？内存也会增长四倍吗？答案取决于实现如何分配池、backend 能否并行推进，以及请求在哪个阶段等待。先把资源指标和测量边界分开，才能解释结果。

本节使用[源码包](../reference/source.md)中的 `labs/mechanisms.c:memory_lab()`、`platform/examples/benchmark.c` 和 `scripts/benchmark-report.py`。依赖与容器入口见[环境说明](../guide/environment.md)。

## mmap 成功与实际驻留

`memory_lab()` 建立 1024 页私有匿名映射，再每页写一个字节，前后用 `getrusage` 观察 minor fault。得到虚拟地址并不表示所有页都已按应用期望驻留，逐页触碰让实际页访问显现出来。

容器内源码根目录：

```sh
make -C labs all
./build/labs/mechanisms memory
```

输出中的 `L5-page-touch` 包含 `minor_fault_delta` 和 `pages: 1024`。该差值受页大小、映射策略及运行环境影响；代码只断言计数没有倒退，不要求恰好一页一个 fault。

接着 fork，子进程将私有映射首字节改为 9，父进程 wait 后仍看到 1；共享映射里，子进程改为 8，父进程 wait 后看到 8。前者展示私有映射的写时复制语义，后者通过等待子进程完成保证这次读写顺序，不是一套适用于并发更新的共享内存协议。[mmap 手册](https://man7.org/linux/man-pages/man2/mmap.2.html) 全部机制与构建回归为 `make -C labs test`。

## 资源指标各自回答什么

| 指标 | 问题 | 常见误读 |
|---|---|---|
| live 请求 / 对象 | 业务尚未结束多少？ | 与池容量混为一谈 |
| 固定池预留 | 已为最坏容量留多少空间？ | 空闲槽不等于未分配内存 |
| heap live / allocator 保留 | 仍在使用多少，分配器留了多少？ | free 后 RSS 必须立即下降 |
| RSS、fault | 本进程的驻留与页访问现象 | 当成全部系统成本 |
| owner 栈、子进程、内核队列 | 执行和 OS 的额外成本 | 只算 payload 总和 |

`sdk_resource_budget()` 返回 core、runtime 和 owner 栈的实现预算。首期 Linux owner 栈配置为 256 KiB；backend 的进程地址空间、socket 和内核对象需另核算。结构体 `sizeof` 同样受目标编译环境影响。

当前请求池的物理上限固定为 16；配置 `request_limit=4` 限制逻辑并发，并不会把结构体中的固定数组缩成四项。因此 4/16 对比主要改变可同时推进的请求量，并没有自动形成对应的内存缩放。

## 基准怎样定义样本

每个配置运行五轮，每轮 10000 次请求，payload 为 256 字节。producer 限制尚未完成的入队量，callback 记录终态与从提交时间开始的单调延迟，同时检查完成 payload 内容。

```text
提交前开始计时 → 本地 ingress → core 接受 → 输出 / backend
             → 回到 owner → terminal callback 记录结束
```

这一延迟包含所走路径中的排队、IPC 和回调抵达；它不单独提供 CPU 执行时间或每个阶段的等待拆分。producer 在提交前等待可用额度的时间也不包含在该请求的 latency 内。

容器内源码根目录：

```sh
make -C platform benchmark
python3 scripts/benchmark-report.py
cat build/benchmark/summary.json
```

正常完成会生成 `limit-4-round-1.csv` 至 `limit-16-round-5.csv` 共十份 CSV。每条 CSV 保存请求结果与 latency；程序另外输出每轮总时间和 `requests_per_s`。

汇总中的 median/p95/p99 来自 completed 样本，`failures` 来自所有样本中未 completed 的数量。解释分位数时必须同时展示失败数；若慢请求大量超时，成功样本的 p99 下降并不说明服务改善。

## 比较结果前，先固定问题

这个 A/B 对比保持模拟器服务行为不变，只调整本地并发额度。应该一起看：每轮样本数、失败、内容检查、吞吐、median/p99，以及停止后 `live=0` 的守恒。

更多在途请求可能让流水线重叠，也可能增加队列等待和停止积压。若服务长期慢于到达，扩容只能延后满队列；不能把增加缓存当成解决服务不足。完整容量与排空算例见[资源预算](../design/06-resource-budget.md)，本项目对比的设计依据见[在途额度案例](../cases/02-inflight-budget.md)。

遇到 CPU 利用率低而请求慢，可以进一步按排队、锁、IO、调度和 callback 工作拆分等待。这需要 profile 或额外时间戳；本基准没有这些证据，所以不能直接归因为 CPU 瓶颈、缓存行冲突或优先级问题。

这里也没有硬实时最坏延迟保证。虚拟环境的 p99、FreeRTOS 宿主 port 的结果，以及真实 MCU 上的中断与调度延迟，各自具有不同测量边界。[Linux / FreeRTOS 对照](../design/03-linux-freertos.md)说明该怎样保留公共语义并验证目标运行环境。
