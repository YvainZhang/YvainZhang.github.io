---
title: SoC 系统知识库
hide:
  - toc
---

<section class="soc-home-hero">
  <p class="soc-home-kicker"><span></span> Technology / System Collection 01</p>
  <h1>SoC System Atlas</h1>
  <p class="soc-home-lead">我把 SoC 拆成十个可以独立理解、又能重新连回系统的数据路径。从 CPU 发出一次访问开始，顺着地址、数据、中断和控制流，一直看到 Linux、外设和调试现场。</p>
  <div class="soc-home-stats">
    <span><strong>10</strong>核心模块</span>
    <span><strong>112</strong>篇笔记</span>
    <span><strong>167</strong>张架构图</span>
    <span><strong>4</strong>个实验</span>
  </div>
</section>

<section class="soc-home-section">
  <div class="soc-home-section-head">
    <p>System Path / 01</p>
    <h2>先看一条数据是怎么穿过整颗芯片的。</h2>
  </div>
  <div class="soc-home-flow" aria-label="SoC 系统数据路径">
    <a href="02-CPU-Architecture/">CPU</a><i>→</i>
    <a href="04-MMU-Address-Space/">MMU</a><i>→</i>
    <a href="03-Cache-Memory-Hierarchy/">Cache</a><i>→</i>
    <a href="05-Bus-Interconnect/">NoC</a><i>→</i>
    <a href="06-DMA-Cache-Coherency/">DMA</a><i>→</i>
    <a href="08-Peripherals-High-Speed-IO/">外设</a>
  </div>
  <p class="soc-home-flow-note">Boot 把系统带到可运行状态，中断把完成事件送回 CPU，Clock / Reset / Power 决定每一段路径是否真的活着。</p>
</section>

<section class="soc-home-section">
  <div class="soc-home-section-head">
    <p>Reading Routes / 02</p>
    <h2>不必从头读到尾，按现在的问题选一条路线。</h2>
  </div>
  <div class="soc-route-grid">
    <a class="soc-route-card" href="00-Overview/">
      <span>Route 01</span>
      <h3>Linux、BSP 与驱动</h3>
      <p>MMU → 中断 / 时钟 / 电源 → Boot / BSP → 外设 → DMA → 调试</p>
    </a>
    <a class="soc-route-card" href="00-Overview/">
      <span>Route 02</span>
      <h3>CPU、内存与性能</h3>
      <p>CPU → Cache / DDR → MMU → NoC → 调试与性能</p>
    </a>
    <a class="soc-route-card" href="00-Overview/">
      <span>Route 03</span>
      <h3>外设与芯片 Bring-up</h3>
      <p>Clock / Reset / Power → 总线 → 外设 → DMA → Boot → 调试</p>
    </a>
  </div>
</section>

<section class="soc-home-section">
  <div class="soc-home-section-head">
    <p>Core Modules / 03</p>
    <h2>十个模块，重新拼成一张系统地图。</h2>
  </div>
  <div class="soc-module-grid">
    <a href="01-SoC-Architecture/"><span>01</span><strong>SoC 总体架构</strong><em>Block · Address · Flow</em></a>
    <a href="02-CPU-Architecture/"><span>02</span><strong>CPU 与处理器</strong><em>ISA · Exception · SMP</em></a>
    <a href="03-Cache-Memory-Hierarchy/"><span>03</span><strong>Cache 与内存</strong><em>Cache · DDR · Coherency</em></a>
    <a href="04-MMU-Address-Space/"><span>04</span><strong>MMU 与地址空间</strong><em>Page Table · TLB · SMMU</em></a>
    <a href="05-Bus-Interconnect/"><span>05</span><strong>总线与片上互联</strong><em>AXI · NoC · Ordering</em></a>
    <a href="06-DMA-Cache-Coherency/"><span>06</span><strong>DMA 与一致性</strong><em>Descriptor · Ownership · API</em></a>
    <a href="07-Interrupt-Clock-Power/"><span>07</span><strong>中断、时钟与电源</strong><em>GIC · Timer · DVFS</em></a>
    <a href="08-Peripherals-High-Speed-IO/"><span>08</span><strong>外设与高速接口</strong><em>GPIO · PCIe · Storage</em></a>
    <a href="09-Boot-BSP-OS/"><span>09</span><strong>Boot、BSP 与 OS</strong><em>Boot Chain · DTS · Driver</em></a>
    <a href="10-Debug-Performance/"><span>10</span><strong>调试与性能</strong><em>Trace · Crash · Perf</em></a>
  </div>
</section>

<section class="soc-home-section soc-home-practice">
  <div class="soc-home-section-head">
    <p>Practice / 04</p>
    <h2>把概念放回真实路径和可复现实验。</h2>
  </div>
  <div class="soc-practice-grid">
    <a href="Case-Studies/"><span>Case Studies</span><strong>跨模块系统案例</strong><p>网卡收包、冷启动和 PCIe NVMe 读写的端到端路径。</p></a>
    <a href="Labs/"><span>Labs</span><strong>四个可复现实验</strong><p>QEMU ARM64、DMA 一致性、弱内存序和 Device Tree 驱动。</p></a>
    <a href="Glossary/"><span>Glossary</span><strong>术语与缩写</strong><p>遇到不熟悉的寄存器、协议和架构词汇时从这里查。</p></a>
  </div>
</section>

!!! note "阅读说明"
    文档中的地址和参数若无特别说明，均用于解释系统机制，不对应特定商业芯片。实际项目仍应以目标芯片的 TRM、数据手册、勘误表和架构规范为准。
