# 性能证据链推导、因果关系定界与工程报告实战

## 1. 结构化性能证据链推导模型

性能调优和故障排查需要把现象、测量结果与可能原因联系起来，再通过复测验证。下面用一组示例数据说明排查顺序；计数器之间的相关性只能提供线索，还需要检查其他解释：

```mermaid
flowchart TD
    Phenomenon["1. 业务现象: 视频流端到端延迟 P99 从 4ms 劣化至 40ms"] --> Step1

    subgraph Evidence_Chain ["逐层收集证据"]
        Step1["2. 排除调度干扰 (ftrace sched_switch)\nTrace 证实任务处于 Running 态, 未被其他进程抢占"]

        Step1 --> Step2["3. 捕获微架构停顿 (perf PMU)\nCPU STALL_BACKEND_MEM 激增, LLC Miss 增加 300%"]

        Step2 --> Step3["4. 监控片上总线 (NoC / DDR Monitor)\n总带宽利用率仅 55%, 但 DDR Channel 0 队列持续满溢 (100% 饱和), Channel 1 处于空闲!"]

        Step3 --> Step4["5. 锁定物理根因 (Address Map Interleaving)\n视频帧 Buffer 物理地址由于分配器缺陷, 全部落入了同一 Channel 0 的单一 Bank 中, 引发严重的 Bank 冲突!"]
    end

    Step4 --> Solution["6. 复测: 调整 DDR 交织粒度 (示例: 128B) -> 比较 P99 与各通道负载"]
```

---

## 2. 性能计数器相关性 vs 因果性判断准则

在性能分析中，“两个指标同时升高”不表示其中一个一定是另一个的原因：

```mermaid
flowchart LR
    subgraph Ambiguous ["看似相关的表面现象: 温度上升 与 延迟上升 同时发生"]
        Temp["温度上升 (T > 85°C)"] <--> Latency["系统延迟上升 (P99 劣化)"]
    end

    subgraph Causal_A ["因果假说 A: 硬件热节流 (Thermal Throttling)"]
        A_T["温度超标"] -->|硬件动作| A_DVFS["CPU 强制降频 (OPP 降至最低)"] -->|导致| A_Lat["延迟飙升"]
    end

    subgraph Causal_B ["因果假说 B: 业务死循环 (Software Bug)"]
        B_Bug["业务出现自旋锁死循环"] -->|导致| B_Lat["处理延迟飙升"] & B_Load["CPU 100% 满载"]
        B_Load --> B_Heat["发热增加, 温度上升"]
    end
```

### 时序先后判别法定界：
- 查看事件高精度时间戳（Timeline）：
  - 若 `Thermal Throttle Interrupt` **先于** IPC 下降发生，可以优先检查假说 A，并核对频率、电压与散热状态；
  - 若 CPU 利用率升高 **先于** 温度爬升，可以检查假说 B，并查看高负载线程的执行路径。

时间上的先后有助于筛选假说，本身不足以证明因果关系。改变负载、频率或散热条件后，还需要观察现象是否随之变化。

---

## 3. 性能与故障复盘报告示例

报告可以按下面的结构记录。模板里的硬件版本、日志、性能数值和测试结果用于示范填写方式，不能代替目标平台的实测记录；`dma-coherent` 也只有在硬件支持并启用一致性时才适用。

```text
================================================================================
【性能问题排查与根因分析报告】
1. 核心结论 (Summary)
   - 现象：万兆网卡在 64B 小包转发时吞吐仅达 4.2Mpps (目标 14.88Mpps)。
   - 根因：RX 缓冲区在非一致性 DMA 架构下，驱动频繁调用 dma_sync 执行 Cache 失效，消耗了 72% 的 CPU 周期。
   - 结果：开启硬件 I/O 一致性 (dma-coherent) 并优化描述符环后，吞吐达标至 14.2Mpps。

2. 复现环境与基准 (Environment)
   - 硬件版本: SoC Rev B0, DDR4-3200 16GB, Kernel 5.15.0-arm64
   - 固件与 Build ID: TF-A v2.8 (Commit a1b2c3d)

3. 证据链 (Evidence Timeline)
   - [00:01:23] perf top 显示 arch_sync_dma_for_cpu 占用率 71.8%。
   - [00:02:15] ARM PMU 事件 L1D_CACHE_REFILL 达到 820 MPKI。

4. 修复与验证 (Fix & Verification)
   - 补丁: [PATCH] net: driver: enable hardware snoop via dma-coherent in DTS.
   - 连续 48 小时线速压力测试，零丢包，CPU 利用率从 98% 降低至 23%。

5. 剩余风险与跟进 (Remaining Risks)
   - PCIe 早期批次固件存在 No-Snoop 属性兼容问题，需配合升级网卡 Option ROM。
================================================================================
```
