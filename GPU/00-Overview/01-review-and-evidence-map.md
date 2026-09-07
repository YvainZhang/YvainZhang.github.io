# GPU 知识体系：掌握标准、复习路线与证据

这套专题面向有驱动、总线和嵌入式经验的读者。先把已有的 DMA、地址空间、并发和恢复经验迁移到 GPU，再补 SIMT 和算子调优，而不是先背型号与峰值参数。

## 阅读边界

GPU 不是 NVIDIA 的同义词。SM、Warp、PTX/SASS 是 NVIDIA 语境；其他厂商的执行组织、ISA、驱动和工具有各自约束。正文中的教学模型用于推演，只有带目标版本、原始记录与测试条件的结果才属于实测。公开资料不足的微架构细节应标为假设。

## 核心能力覆盖

| 能力 | 复习入口 | 能独立完成才算掌握 |
| --- | --- | --- |
| 执行模型 | [SIMT](../02-Compute-Core-SIMT/01-simt-execution-model.md) | 解释线程、warp、block 的映射及同步作用域 |
| 资源约束 | [寄存器](../02-Compute-Core-SIMT/03-register-file-allocation.md) | 根据寄存器/shared memory 判断驻留限制，并验证 spill |
| 数据复用 | [存储层次](../03-Memory-Hierarchy-VRAM/README.md) | 区分合并访存、bank conflict、cache miss 和实际流量 |
| 地址空间 | [MMU/UVM](../04-Address-Space-Unified-Memory/README.md) | 区分统一地址、驻留位置、迁移与一致性 |
| 提交与恢复 | [UMD 提交](../09-Driver-Runtime-Software-Stack/02-umd-command-submission.md) | 画出依赖、buffer 生命周期与错误结束路径 |
| 性能推导 | [GEMM 证据链](../Case-Studies/04-gemm-evidence-path.md) | 算工作量和时间下界，再用计数器验证瓶颈 |
| 多卡通信 | [集合通信](../11-Distributed-Parallel-Scale/01-nccl-collective-comm.md) | 区分算法字节与链路流量，定位拓扑和同步影响 |
| 验证与实验 | [实验目录](../Labs/README.md) | 给出正确性基线、重复测量及完整环境记录 |

## 十二个递进追问

1. **Warp 为什么能隐藏延迟？** 驻留上下文降低切换成本，但前提是其他 warp 有可发射工作，不是所有等待都能隐藏。
2. **分支分化损失是什么？** 活跃 lane 和执行路径效率下降；不能简单把每个 if 都判为固定减半。
3. **Occupancy 越高越快吗？** 它是资源驻留比例，不是有效指令吞吐；用复用、spill、eligible warp 一起解释。
4. **Shared Memory 为什么冲突？** 先给出目标架构 bank 映射与访问宽度，再分析同一指令的地址集合；广播不能按普通冲突处理。
5. **UVA 等于不用搬数据吗？** 统一命名不消除物理驻留与迁移成本，更不自动保证任意并发访问安全。
6. **跨 stream 为什么偶发错？** 核对生产完成、消费等待和最后使用者，不以 Host 返回顺序替代设备依赖。
7. **Roofline 需要什么字节？** 指定存储层，区分算法下界与测得流量，并匹配精度和稀疏口径。
8. **FlashAttention 改了什么？** 从避免物化大中间矩阵、分块和在线归一化解释 IO，而不是声称消除了注意力的所有计算。
9. **多卡一定线性加速吗？** 通信、同步、负载不均和重叠能力决定扩展，单链路峰值不能代表集合通信时间。
10. **GPU busy 高为什么业务慢？** busy 不代表在做有效工作，可能包含冗余计算；同时检查 CPU 和搬运关键路径。
11. **超时可以直接 reset 吗？** 先保留证据与影响范围，处理在途任务和资源生命周期，避免迟到完成污染新队列。
12. **如何证明优化有效？** 同条件正确性通过，未插桩端到端收益稳定，同时说明反例和适用形状。

## 一次复习的交付物

用一个 GEMM 贯穿：写出精度和布局契约，算 FLOP/最小字节，标注 buffer 的生产者与消费者，再设计两个可区分瓶颈的实验。最后写一段“观察—假设—反证—结论”，注明还没有证实的部分。

面试展示的是可追问的分析过程，不把阅读公开文档写成亲历流片或量产故障。建议保留报告字段：设备/软件版本、输入形状、计时范围、误差门限、原始 trace、配置变化和结论边界。

## 一手资料怎么用

- [CUDA 编程指南](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)：编程模型与同步契约；该入口已标为 legacy，使用时选择与工具链匹配的版本或其新指南入口。
- [Nsight Compute](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)：指标口径和采集扰动，不能当作架构峰值表。
- [FlashAttention 论文](https://arxiv.org/abs/2205.14135)：IO-aware 算法原理，不等于所有版本的 kernel 实现。
- [Linux DRM 文档](https://docs.kernel.org/gpu/drm-mm.html)：Linux 内存与同步对象，不代替某厂商完整驱动 ABI。

对照 [NPU 专题](/tech/npu/) 时，关注运行时动态调度与编译期显式数据安排的不同；GPU 也有显式分块，NPU 也可以动态调度，不能把二者绝对二分。
