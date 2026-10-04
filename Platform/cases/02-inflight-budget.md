# 在途额度提高以后，吞吐为什么接近四倍

普通请求约 5 ms 后收到模拟器回复。最多四个在途请求时，等待不能充分重叠；增加到十六个，是否可以提高吞吐？本例只改变额度，并保留数据校验和终态守恒。

这是 2026-10-02/03 的 aarch64 Linux 容器历史基准，环境为 Alpine 3.22、musl 1.2.5、GCC 14.2.0。测量对应当时实现。本次公开源码含后续修订，新快照需要重新测量，历史结果不作为当前版本性能承诺。代码与版本见[源码入口](../reference/source.md)。

## 变量和统计边界

| 项目 | 条件 |
| --- | --- |
| 唯一配置变量 | request_limit=4 或 16 |
| 应用窗口 | 与 request_limit 相同 |
| payload | 256 bytes，全部回显校验 |
| backend | 默认响应、无故障注入、单实例 |
| 轮次 | 每配置五轮，每轮 10000 请求 |
| 请求时延起点 | 调用 submit 之前的单调时间 |
| 请求时延终点 | TERMINAL callback 采样 |
| 吞吐 | 整轮 10000 请求除以 elapsed |
| 分位数 | 成功样本排序，取 floor(q×(n−1)) 位置，无插值 |

初始化不计入请求时延；第一批请求没有另行预热剔除。原始 CSV 保存全部终态，摘要同时列出失败数。吞吐包含这一轮提交和完成的整体耗时，不能用单个请求时延的倒数替代。

## 五轮结果

| 轮次 | 额度 4 吞吐（req/s） | 额度 4 p99（ms） | 额度 16 吞吐（req/s） | 额度 16 p99（ms） |
| --- | ---: | ---: | ---: | ---: |
| 1 | 664.38 | 7.176 | 2640.73 | 7.748 |
| 2 | 663.24 | 7.038 | 2650.87 | 7.230 |
| 3 | 663.85 | 6.962 | 2642.39 | 7.617 |
| 4 | 664.96 | 6.835 | 2649.84 | 7.298 |
| 5 | 664.17 | 6.841 | 2641.32 | 7.212 |

每轮 10000 个请求全部 completed，没有 rejected 或内容错误。额度 4 的 median 约 5.982～5.987 ms，额度 16 约 5.969～5.977 ms。增加额度以后吞吐约提高四倍，p99 略增。

精确分位见[summary.json](../assets/benchmark/summary.json)，整轮耗时见[runs.json](../assets/benchmark/runs.json)。原始样本按轮次下载：

| 额度 | 原始 CSV |
| --- | --- |
| 4 | [第 1 轮](../assets/benchmark/limit-4-round-1.csv)、[第 2 轮](../assets/benchmark/limit-4-round-2.csv)、[第 3 轮](../assets/benchmark/limit-4-round-3.csv)、[第 4 轮](../assets/benchmark/limit-4-round-4.csv)、[第 5 轮](../assets/benchmark/limit-4-round-5.csv) |
| 16 | [第 1 轮](../assets/benchmark/limit-16-round-1.csv)、[第 2 轮](../assets/benchmark/limit-16-round-2.csv)、[第 3 轮](../assets/benchmark/limit-16-round-3.csv)、[第 4 轮](../assets/benchmark/limit-16-round-4.csv)、[第 5 轮](../assets/benchmark/limit-16-round-5.csv) |

CSV 含请求时延，没有整轮 wall time；用 runs 中的 elapsed 重算吞吐，使用 CSV 重算 median/p95/p99。

## 解释成立的条件

后端响应存在可重叠等待，增加流水线深度能提高同时等待的请求数。理想化估算 `N/5ms` 会忽略事件循环、通信、调度和交付开销；这里只用于说明潜在重叠，不作为实测吞吐。

没有 CPU profile，当前证据不能证明某段代码是 CPU 瓶颈。若设备真正串行执行，或者 callback 消费变慢，增加额度可能只增加排队与尾延迟。

## 重新运行与重算

在[专用工具容器](../guide/environment.md)的项目根目录执行：

```sh
make -C platform benchmark
python3 scripts/benchmark-report.py
```

Makefile 运行两种额度、各五轮，产生十个 CSV；报告写到 `build/benchmark/summary.json`。保存当前源码版本、环境和每轮标准输出，核对内容与全部终态以后再比较性能。

只重算历史分位时，将公开 CSV 下载到项目中的 `build/historical-benchmark/`，然后运行：

```sh
python3 scripts/benchmark-report.py --input build/historical-benchmark
```

输出保留失败数；如果过滤失败只看延迟，必须同时报告被排除的比例。

## 从实验结论走到平台决定

当前固定结构预留 16 槽，逻辑额度缩到 4 不会减少已分配 RAM。16 可以用于此模拟器的吞吐候选；真实系统还需核对资源峰值、SLO、慢 callback、故障期和恢复时长。[完整预算与两个候选](../design/06-resource-budget.md)

五轮数据没有消除容器调度噪声，也没有真实 Wi-Fi、USB/SDIO、功耗或硬实时结论。下一次实验优先把请求时延拆成入口等待、处理、设备等待和回调交付，再决定调整哪一层。
