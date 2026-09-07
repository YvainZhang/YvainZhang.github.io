---
title: GPU 芯片全栈知识体系
hide:
  - toc
---

<section class="gpu-home-hero">
  <p class="gpu-home-kicker"><span></span> Silicon Architecture / GPGPU System Atlas</p>
  <h1>GPU System Atlas</h1>
  <p class="gpu-home-lead">从芯片原厂视角出发，系统梳理 GPU 从 SIMT 微架构、Warp 调度与 Tensor Core，到 HBM3e/GDDR7 显存系统、PCIe/NVLink 高速互联、Linux KMD/UMD 驱动、PTX/SASS 编译器后端，再到 NCCL 多卡集群与算子极致性能调优的全栈工程地图。</p>
  <div class="gpu-home-stats">
    <span><strong>11</strong>核心模块</span>
    <span><strong>98</strong>篇笔记</span>
    <span><strong>52</strong>张架构图</span>
    <span><strong>3</strong>个实验</span>
  </div>
</section>

<section class="gpu-home-section">
  <div class="gpu-home-section-head">
    <p>Hardware Flow / 01</p>
    <h2>看一个 Kernel 指令与张量数据如何流过整颗 GPU。</h2>
  </div>
  <div class="gpu-home-flow" aria-label="GPU 系统全硬件路径">
    <a href="01-GPU-Architecture/">Host GigaThread</a><i>→</i>
    <a href="02-Compute-Core-SIMT/">Warp Issue</a><i>→</i>
    <a href="02-Compute-Core-SIMT/">Tensor Core</a><i>→</i>
    <a href="03-Memory-Hierarchy-VRAM/">Shared/L1</a><i>→</i>
    <a href="03-Memory-Hierarchy-VRAM/">L2 Cache</a><i>→</i>
    <a href="03-Memory-Hierarchy-VRAM/">HBM3e PHY</a>
  </div>
  <p class="gpu-home-flow-note">Copy Engine 实现三向并发数据搬运，GPU MMU/UVM 提供全局虚拟地址转换，NVLink/NVSwitch 编织跨卡超节点互联，PMU 固件全天候调控 DVFS 功耗与温控防护。</p>
</section>

<section class="gpu-home-section">
  <div class="gpu-home-section-head">
    <p>Reading Routes / 02</p>
    <h2>按工程角色与研发场景，选择最适合的学习路线。</h2>
  </div>
  <div class="gpu-route-grid">
    <a class="gpu-route-card" href="00-Overview/">
      <span>Route 01</span>
      <h3>算子开发与性能调优</h3>
      <p>SIMT 调度 → Shared Mem 冲突 → Tensor Core → Roofline 模型 → FlashAttention</p>
    </a>
    <a class="gpu-route-card" href="00-Overview/">
      <span>Route 02</span>
      <h3>底层驱动与系统软件</h3>
      <p>GPU MMU/UVM → PCIe/NVLink → Linux DRM/KMD → UMD Doorbell → Xid 故障诊断</p>
    </a>
    <a class="gpu-route-card" href="00-Overview/">
      <span>Route 03</span>
      <h3>芯片架构与系统互联</h3>
      <p>GPC/SM 拓扑 → HBM3e/CoWoS → NVLink/NVSwitch → DVFS/PMU → 3D 并行集群</p>
    </a>
  </div>
</section>

<section class="gpu-home-section">
  <div class="gpu-home-section-head">
    <p>Core Modules / 03</p>
    <h2>十一个模块，拼合现代高性能 GPU 的完整硅片画像。</h2>
  </div>
  <div class="gpu-module-grid">
    <a href="01-GPU-Architecture/"><span>01</span><strong>GPU 总体架构</strong><em>GPC · BAR · Bring-up</em></a>
    <a href="02-Compute-Core-SIMT/"><span>02</span><strong>计算核心与 SIMT</strong><em>Warp · Scoreboard · TensorCore</em></a>
    <a href="03-Memory-Hierarchy-VRAM/"><span>03</span><strong>显存系统与存储层次</strong><em>HBM3e · Bank Conflict · Coalescing</em></a>
    <a href="04-Address-Space-Unified-Memory/"><span>04</span><strong>地址空间与统一内存</strong><em>GPU MMU · Page Fault · ATS</em></a>
    <a href="05-Interconnect-Multi-GPU/"><span>05</span><strong>片上与片间高速互联</strong><em>PCIe 6 · NVLink · NVSwitch</em></a>
    <a href="06-DMA-Async-Data-Transfer/"><span>06</span><strong>异步数据搬运与 DMA</strong><em>Copy Engine · GPUDirect · Graph</em></a>
    <a href="07-Clock-Power-Thermal-DVFS/"><span>07</span><strong>频率功耗与电源管理</strong><em>DVFS · PMU · Throttling</em></a>
    <a href="08-Graphics-Video-Engines/"><span>08</span><strong>图形视频与专用引擎</strong><em>Raster · RT Core · NVENC</em></a>
    <a href="09-Driver-Runtime-Software-Stack/"><span>09</span><strong>驱动与软件运行时体系</strong><em>DRM/KMS · UMD · PTX/SASS</em></a>
    <a href="10-Debug-Profiling-Performance/"><span>10</span><strong>调试性能与故障分析</strong><em>Roofline · NSight · Xid Hang</em></a>
    <a href="11-Distributed-Parallel-Scale/"><span>11</span><strong>多卡集群与分布式并行</strong><em>NCCL · 3D 并行 · RoCEv2</em></a>
  </div>
</section>

<section class="gpu-home-section gpu-home-practice">
  <div class="gpu-home-section-head">
    <p>Practice / 04</p>
    <h2>把微架构理论放回全链路端到端案例与可复现源码实验。</h2>
  </div>
  <div class="gpu-practice-grid">
    <a href="Case-Studies/"><span>Case Studies</span><strong>跨模块工程案例</strong><p>FlashAttention 硬件路径、PCIe P2P 事务流与 8 卡 AllReduce 数据流推演。</p></a>
    <a href="Labs/"><span>Labs</span><strong>可复现代码实验</strong><p>手写极致 GEMM 调优、NSight Roofline 实战与开源 GPU 驱动任务提交跟踪。</p></a>
    <a href="Glossary/"><span>Glossary</span><strong>专业术语与缩写</strong><p>涵盖 GPC、SIMT、Warp、HBM3e、NVLink、PTX、SASS、Xid 等 90+ 词条。</p></a>
  </div>
</section>

## 文档约定与原厂工程“七问”

知识库中的每个技术模块与子章节均严格遵循芯片原厂软硬件协同工程规范，解答以下 7 个核心问题：

1. **硬件解决什么问题**：该模块在算力吞吐、访存带宽、功耗控制或互联扩展中的根本职责。
2. **硬件微架构与组成**：数字电路模块如何划分，与 NoC/Crossbar/总线如何连接。
3. **软件可见接口**：KMD/UMD/编译器能看到的寄存器、BAR 空间、指令格式与描述符结构。
4. **四流全链路分析**：地址流、数据流、控制流、事件/中断/DMA 流如何在硬件管道中流转。
5. **软硬件设计约束**：面积（PPA）、时序收敛、功耗上限、Bank 冲突与一致性限制。
6. **现场排错与调试清单**：面对硬件 Hang 死、数据踩踏（Mismatch）、性能断崖时的系统化排查步骤。
7. **实验与验证推演**：如何通过 C-Model / 周期精确仿真器（GPGPU-Sim / Accel-Sim）或实卡验证。

!!! note "阅读说明与免责声明"
    文档中的地址、寄存器偏移和微架构参数若无特别说明，均用于解释工业界通用 GPU 架构机制，不对应特定商业芯片私密设计。实际工程项目应以目标 GPU 芯片的 TRM、官方数据手册、架构白皮书和勘误表（Errata）为准。
