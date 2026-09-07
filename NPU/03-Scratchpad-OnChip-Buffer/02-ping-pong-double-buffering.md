# 02 Ping-Pong 双缓冲硬件设计与时序状态机

## 1. 双缓冲提供重叠机会，不保证消除气泡

Tile i 的计算可以与 Tile i+1 的搬运重叠，但启动、排空、带宽不足及 bank 冲突仍会造成空闲。以下是独立 DMA/计算引擎的教学时序，不是所有 NPU 的统一调度协议。

```mermaid
sequenceDiagram
    autonumber
    participant DMA as Tensor DMA (搬运引擎)
    participant Ping as Buffer A (Ping)
    participant Pong as Buffer B (Pong)
    participant PE as 脉动阵列 (计算引擎)

    Note over DMA, PE: 时隙 0 (Step 0)
    DMA->>Ping: 搬运 Tile 0 权重与特征图
    Note over PE: PE 计算空闲 (初始填充)

    Note over DMA, PE: 时隙 1 (满足依赖后可以重叠)
    DMA->>Pong: 搬运 Tile 1 数据
    Ping->>PE: PE 读取 Buffer A 全速计算 Tile 0

    Note over DMA, PE: 时隙 2 (槽位释放后才能复用)
    DMA->>Ping: 搬运 Tile 2 数据
    Pong->>PE: PE 读取 Buffer B 全速计算 Tile 1
```

## 2. 每个槽位独立记录所有权

| 状态 | 允许的操作 | 转移条件 |
| --- | --- | --- |
| FREE | 为下一 Tile 分配槽位 | 上一消费者不再使用 |
| LOADING | DMA 写入，禁止计算读取 | 输入完成且满足可见性协议 |
| READY | 等待计算资源及其他输入 | 所有依赖满足 |
| COMPUTING | 读取输入、更新累加器 | 最后一次读取/计算完成 |
| DRAINING | 若输出共用槽则等待回写 | 回写完成后才可复用 |

输出独立存储时，输入槽可以在最后一次读取后释放，不能用不相关的 `Compute_Done` 猜测。事件应关联 Tile、槽位和代际，防止迟到事件误翻转新任务的指针。错误路径停止继续填充，失败通知传播到依赖任务，引擎静止后再复用内存。

## 3. SRAM 不只是两份输入

以 INT8 GEMM、INT32 累加为例：

```text
S_inputs = 2 * (Tm*Tk + Tk*Tn)          bytes
S_acc    = 4 * Tm*Tn                   bytes
S_total  = S_inputs + S_acc + S_output + S_workspace + S_alignment
```

累加器跨 K 分块保留，不能按 INT8 计费。输出是否可原位复用需要活跃区间证明。`Tm=Tn=64,Tk=128` 时，双份输入 32768 B、累加器 16384 B，基础总量 48 KiB，尚未计输出和工作区。总量装得下仍可能违反单 bank 分区容量、端口或 DMA 对齐要求。

## 4. 两阶段流水的理想下界

假设 N 个等长 Tile，每个输入加载 L、计算 C，两引擎独立，无 bank 冲突，暂不计输出回写：

```text
T_serial   = N * (L + C)
T_pipeline = L + C + (N - 1) * max(L, C)
```

教学值 `N=8,L=30 us,C=50 us`：串行 640 us，理想流水 430 us，约 1.49 倍，不是 2 倍。若 L 大于 C，计算仍会等输入。更多缓冲可吸收抖动，不能修复长期供数速率不足。

输入和输出若共享 DMA/DDR，需将回写计入服务时间；两引擎争用 SRAM bank 时也不能套独立资源模型。

## 5. 用 Trace 证明没有踩踏，再测性能

记录 `tile_id / slot_id / load_begin / load_done / compute_begin / compute_done / store_done`。检查下一 load 不早于上一次最后读取，计算不早于输入 ready，回写前不覆盖结果。分开统计启动、稳态、排空占比。

覆盖 DMA 延迟、计算延迟、奇数 Tile 数、尾块、取消和旧代际事件。先通过功能测试，再比较单/双缓冲端到端时间，不能仅用 busy 百分比宣称加速。

公开硬件可参考 [NVDLA Unit Description](https://nvdla.org/hw/v1/ias/unit_description.html)，其结构不是所有 NPU 的共同模板。继续阅读 [量化 GEMM 映射](../Case-Studies/04-quantized-gemm-contract.md) 与 [Tiling 预算实验](../Labs/lab02-tvm-custom-npu-tiling/README.md)。
