# GEMM 从提交到性能证据：完整的 GPU 排查案例

## 场景与数值契约

本案例是可手算的教学模型，不含实卡成绩。选择 `C=A×B`、`M=N=K=4096`，A/B/C 存储为 FP16，FP32 累加，`beta=0`，不读取旧 C。目标是建立输入、执行、正确性、时间与硬件证据之间的对应关系，不承诺固定利用率。

记录 layout、leading dimension、转置标志、计算精度、GPU 型号及库/编译器版本。FP32 累加不等于 FP32 输出；不同 math mode 可能改变有效输入精度，跨实现比较不能只写“都是 GEMM”。

## 1. 从业务请求拆到设备任务

执行路径为 buffer 分配/复用、H2D、GEMM、D2H（若业务需要）、结果消费。权重常驻和每次上传权重是不同基线，要分别报告。

三条依赖必须成立：输入生产结束后启动 GEMM；最后一次使用后重写输入；输出对消费者可见后读取结果。双 stream 应明确哪个 event 连接哪条边，不能靠全局同步掩盖生命周期错误。

## 2. 工作量和访存下界

```text
F = 2*M*N*K = 137438953472 FLOP ≈ 137.44 GFLOP
B_min = 2*(M*K + K*N + M*N) = 100663296 B = 96 MiB
I_ideal = F/B_min ≈ 1365.33 FLOP/B
```

B_min 假设 A/B 各从目标存储层读取一次、C 写一次。实际分块重复读取、spill 和格式转换会增加流量。L2 与 HBM 的字节数不同，不能把算法最小字节数冒充 profiler 的 DRAM 计数。

设一台**虚构设备**的匹配精度算力上界为 100 TFLOP/s、HBM 上界为 1 TB/s，则计算下界约 1.374 ms、最小访存下界约 0.101 ms。取两者最大值，理想模型倾向算力受限；这不证明实际 kernel 已经算力受限，也不能把可能重叠的耗时直接相加。

## 3. 为什么 Tile 不是越大越好

输出 Tile 增大可提高复用，但累加器随 `Tm*Tn` 增长。寄存器需求增加可能降低驻留 block 数，spill 又引入访存。Shared Memory 的多 stage 也会占用更多驻留资源。

驻留 block 上界需同时检查寄存器、共享内存、线程和 block 限制，并考虑实际分配粒度；不要用理想除法替代目标架构工具。高 occupancy 只表示驻留 warp 多，不保证 eligible warp 多或吞吐高。

调 Tile 时同时记录寄存器、共享内存、spill、驻留限制、kernel 时间和误差。降低 occupancy 但提高复用的版本可能更快；限制寄存器可能因 spill 反而变慢。

## 4. 先验证正确性

与可信参考实现比较绝对、相对误差及整体误差统计，容差按输入范围、K、累加与输出精度制定。零值、单位阵用于定位地址错误，但不能替代随机与高动态范围输入。

增加 `M=130,N=70,K=129` 等非整齐形状，检查边界 mask、padding、stride，以及接口声称支持的非连续输入。尾块越界即使没崩溃也不算通过。

## 5. 时间线决定下一步采样

先记录未插桩端到端基线，warm-up 后重复测量并保留中位数和尾部时延。CUDA event 所在 stream 与依赖必须覆盖被测工作；Host 墙钟则覆盖业务范围，两者分开报告。

| 证据 | 可检验假设 | 下一步 |
| --- | --- | --- |
| GPU 空闲，CPU 时间线有长间隙 | Host 供给不足或大量小任务 | 评估批处理、图重放 |
| H2D/D2H 占主导 | 数据驻留策略不合适 | 比较常驻输入与搬运方案 |
| kernel DRAM 吞吐高 | 复用差、spill 或转换 | 核对实际字节与编译报告 |
| 计算管线繁忙 | 接近对应精度的计算限制 | 检查指令组合与算法工作量 |
| 吞吐均低而耗时长 | 依赖、并行度或尾波 | eligible warp、stall、grid 和形状 |

指标采集可能需要 replay 并影响 cache，因此 profiler 时间与未插桩时间分开。指标集合依 GPU/工具版本而异；采集语义查阅 [Nsight Compute Profiling Guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)。

## 6. 实验记录与追问

每次改变一个主要变量：Tile、stage、layout、融合或并发。保存种子、配置、误差、原始报告和采集命令。运行时错误、未完成同步、正确性失败的样本记为失败，不参与吞吐平均。

面试追问：算法强度高为何仍 memory-bound？Tensor Core 利用率和端到端收益为何不同？减少 launch 次数为何可能比加速单 kernel 更有效？融合减少写回，为何可能因寄存器压力反而变慢？

回答时分别指向业务关键路径、选定存储层的实际流量和资源约束。测量实践参见 [CUDA Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/)。[现有 GEMM 实验](../Labs/lab01-cuda-gemm-tuning/README.md) 是实卡练习入口，本页数值不代表该实验已取得的成绩。
