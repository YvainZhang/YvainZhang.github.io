---
title: NPU / AI 芯片全栈知识体系
hide:
  - toc
---

<section class="npu-home-hero">
  <p class="npu-home-kicker"><span></span> Domain-Specific Architecture / AI Accelerator Atlas</p>
  <h1>NPU System Atlas</h1>
  <p class="npu-home-lead">从 AI 芯片原厂视角出发，系统梳理 NPU 从专用领域架构（DSA）定义、2D 脉动阵列微架构与片上 Scratchpad SRAM，到多维 Tensor DMA、AI 编译器离线 Tiling 切分与双缓冲、底层驱动、端云分化，再到万卡集群互联与极致算力利用率（MFU）调优的全栈知识地图。</p>
  <div class="npu-home-stats">
    <span><strong>11</strong>核心模块</span>
    <span><strong>97</strong>篇笔记</span>
    <span><strong>56</strong>张架构图</span>
    <span><strong>3</strong>个实验</span>
  </div>
</section>

<section class="npu-home-section">
  <div class="npu-home-section-head">
    <p>Hardware Flow / 01</p>
    <h2>看一个张量数据如何流过脉动阵列与向量流水线。</h2>
  </div>
  <div class="npu-home-flow" aria-label="NPU 系统数据路径">
    <a href="01-NPU-Architecture/">Task Queue</a><i>→</i>
    <a href="05-NPU-DMA-Dataflow-Engine/">Tensor DMA</a><i>→</i>
    <a href="03-Scratchpad-OnChip-Buffer/">Ping-Pong SRAM</a><i>→</i>
    <a href="02-Tensor-Matrix-Compute-Core/">2D Systolic Array</a><i>→</i>
    <a href="02-Tensor-Matrix-Compute-Core/">VPU Engine</a><i>→</i>
    <a href="05-NPU-DMA-Dataflow-Engine/">External DDR/HBM</a>
  </div>
  <p class="npu-home-flow-note">AI 编译器离线生成确定性 VLIW 指令与静态内存排布，多维 Tensor DMA 边搬运边转置，硬件 Barrier 与 Event 状态机确保计算与传输 100% 异步重叠。</p>
</section>

<section class="npu-home-section">
  <div class="npu-home-section-head">
    <p>Reading Routes / 02</p>
    <h2>按研发分工与工程场景，选择最适合的学习路线。</h2>
  </div>
  <div class="npu-route-grid">
    <a class="npu-route-card" href="00-Overview/">
      <span>Route 01</span>
      <h3>AI 编译器与算子切分</h3>
      <p>脉动阵列微架构 → Scratchpad SRAM → 算子融合 → Tiling 策略 → MLIR Codegen</p>
    </a>
    <a class="npu-route-card" href="00-Overview/">
      <span>Route 02</span>
      <h3>底层驱动与任务调度</h3>
      <p>Host-Device 接口 → Tensor DMA → VLIW 指令流 → 硬件 Barrier → 故障定位</p>
    </a>
    <a class="npu-route-card" href="00-Overview/">
      <span>Route 03</span>
      <h3>芯片架构与集群互联</h3>
      <p>DSA 架构设计 → 2D Mesh NoC → 端云架构分化 → HCCL 集合通信 → 万卡集群</p>
    </a>
  </div>
</section>

<section class="npu-home-section">
  <div class="npu-home-section-head">
    <p>Core Modules / 03</p>
    <h2>十一个模块，拼合现代专用 AI 加速芯片的完整硅片画像。</h2>
  </div>
  <div class="npu-module-grid">
    <a href="01-NPU-Architecture/"><span>01</span><strong>NPU 总体架构与范式</strong><em>DSA · Spatial · Bring-up</em></a>
    <a href="02-Tensor-Matrix-Compute-Core/"><span>02</span><strong>张量与矩阵计算核心</strong><em>Systolic · WS/OS/IS · VPU</em></a>
    <a href="03-Scratchpad-OnChip-Buffer/"><span>03</span><strong>片上存储与双缓冲</strong><em>SRAM · Ping-Pong · Bank</em></a>
    <a href="04-Data-Quantization-Mixed-Precision/"><span>04</span><strong>混合精度与量化计算</strong><em>INT8 · FP8 · Microscaling</em></a>
    <a href="05-NPU-DMA-Dataflow-Engine/"><span>05</span><strong>专用张量 DMA 引擎</strong><em>Tensor DMA · Stride · NC4HW4</em></a>
    <a href="06-Interconnect-Tile-Mesh-NoC/"><span>06</span><strong>片上互联与多核 NoC</strong><em>2D Mesh · XY Routing · Multicast</em></a>
    <a href="07-Command-Processor-Task-Scheduler/"><span>07</span><strong>指令流调度与同步</strong><em>VLIW · Task Queue · Barrier</em></a>
    <a href="08-Edge-vs-Cloud-Architecture/"><span>08</span><strong>端侧与云端架构分化</strong><em>Edge ISP · Cloud HBM · Tradeoffs</em></a>
    <a href="09-AI-Compiler-Software-Stack/"><span>09</span><strong>AI 编译器与软硬件映射</strong><em>Graph IR · Tiling · MLIR</em></a>
    <a href="10-Debug-Profiling-Benchmarking/"><span>10</span><strong>性能评测与利用率分析</strong><em>MFU/HFU · Roofline · MLPerf</em></a>
    <a href="11-Multi-NPU-Cluster-ScaleOut/"><span>11</span><strong>分布式集群与大规模扩展</strong><em>Chip-to-Chip · HCCL · ScaleOut</em></a>
  </div>
</section>

<section class="npu-home-section npu-home-practice">
  <div class="npu-home-section-head">
    <p>Practice / 04</p>
    <h2>把专用架构理论放回全链路端到端案例与可复现实战实验。</h2>
  </div>
  <div class="npu-practice-grid">
    <a href="Case-Studies/"><span>Case Studies</span><strong>跨模块工程案例</strong><p>Transformer 块硬件映射、LLM Prefill/Decode 硬件流与相机 ISP-NPU 零拷贝流水。</p></a>
    <a href="Labs/"><span>Labs</span><strong>可复现代码实验</strong><p>手写时钟级 2D 脉动阵列模拟器、TVM 自定义 NPU Tiling 调度与端侧量化部署。</p></a>
    <a href="Glossary/"><span>Glossary</span><strong>专业术语与缩写</strong><p>涵盖 DSA、Systolic Array、PE、SPM、WS/OS/IS、MLIR、MFU、HCCL 等 90+ 词条。</p></a>
  </div>
</section>

## 文档约定与原厂工程“七问”

知识库中的每个技术模块与子章节均严格遵循芯片原厂软硬件协同工程规范，解答以下 7 个核心问题：

1. **硬件解决什么问题**：该模块在张量算力吞吐、SRAM 带宽、专用量化或编译调度中的根本职责。
2. **硬件微架构与组成**：数字电路模块如何划分，与片上 NoC/AXI/SRAM 总线如何连接。
3. **软件可见接口**：编译器/驱动/固件能看到的 Task 描述符、SRAM 编址、VLIW 指令格式与 Event 寄存器。
4. **四流全链路分析**：张量数据流、权重流、指令流、硬件 Barrier/DMA 事件流如何在流水线中流转。
5. **软硬件设计约束**：SRAM 面积容量上限、多维搬运对齐、量化动态范围与脉动流水气泡限制。
6. **现场排错与调试清单**：面对计算结果 Mismatch、量化精度断崖、DMA 握手死锁时的系统化排查步骤。
7. **实验与验证推演**：如何通过 C-Model / 周期级模拟器或实卡进行功能与性能验证。

!!! note "阅读说明与免责声明"
    文档中的地址、寄存器偏移和微架构参数若无特别说明，均用于解释工业界通用 NPU / DSA 架构机制，不对应特定商业芯片私密设计。实际工程项目应以目标 AI 芯片的 TRM、官方数据手册、架构规范和编译器白皮书为准。
