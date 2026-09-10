---
title: RTOS 系统知识库
hide:
  - toc
---

<section class="rtos-home-hero">
  <p class="rtos-home-kicker"><span></span> Technology / Embedded OS Collection 06</p>
  <h1>RTOS System Atlas</h1>
  <p class="rtos-home-lead">整理任务调度、中断、上下文切换与同步机制，对照 FreeRTOS 和 Zephyr 的实现，并记录 RVKernel 的启动、抢占、管道与多核实验。</p>
  <div class="rtos-home-stats">
    <span><strong>4</strong>大核心篇章</span>
    <span><strong>32</strong>篇技术笔记</span>
    <span><strong>4</strong>个动手实战实验</span>
    <span><strong>3</strong>个调试案例</span>
  </div>
</section>

<section class="rtos-home-section">
  <div class="rtos-home-section-head">
    <p>System Core / 01</p>
    <h2>实时系统的确定性执行主线</h2>
  </div>
  <div class="rtos-home-flow" aria-label="RTOS 执行主线">
    <a href="01-RTOS-Fundamentals/01-realtime-principles-scheduling/">硬件中断 ISR</a><i>→</i>
    <a href="01-RTOS-Fundamentals/03-interrupt-systick-critical-section/">PendSV / 现场保存</a><i>→</i>
    <a href="01-RTOS-Fundamentals/02-task-lifecycle-tcb-context-switch/">任务选择</a><i>→</i>
    <a href="02-FreeRTOS-Deep-Dive/04-queue-internals-semaphore-mutex/">IPC 解锁 / 唤醒</a><i>→</i>
    <a href="01-RTOS-Fundamentals/02-task-lifecycle-tcb-context-switch/">目标任务恢复</a>
  </div>
  <p class="rtos-home-flow-note">实时性的核心不是“运行得最快”，而是“在严格限定的时限（Deadline）内确定性完成”。</p>
</section>

<section class="rtos-home-section">
  <div class="rtos-home-section-head">
    <p>Four Steps / 02</p>
    <h2>调度、内核实现与系统选型</h2>
  </div>
  <div class="rtos-route-grid">
    <a class="rtos-route-card" href="01-RTOS-Fundamentals/">
      <span>Step 01</span>
      <h3>RTOS 通用核心机制</h3>
      <p>调度理论 RMS/EDF、TCB 控制块、上下文切换、SysTick 节拍、中断延迟与内存堆保护。</p>
    </a>
    <a class="rtos-route-card" href="02-FreeRTOS-Deep-Dive/">
      <span>Step 02</span>
      <h3>FreeRTOS 源码分析</h3>
      <p>极简微内核哲学、pxReadyTasksLists 双向链表与硬件前导零位图、PendSV 汇编现场切换、Queue 底层实现。</p>
    </a>
    <a class="rtos-route-card" href="03-Zephyr-Deep-Dive/">
      <span>Step 03</span>
      <h3>Zephyr 现代全栈 OS</h3>
      <p>DeviceTree 硬件抽象、Kconfig 编译配置、统一驱动模型 DEVICE_DT_DEFINE、MPU 用户空间隔离与子系统。</p>
    </a>
    <a class="rtos-route-card" href="04-Comparative-Study/">
      <span>Step 04</span>
      <h3>系统对比与场景选型</h3>
      <p>对照实时性、资源占用、驱动生态与内存隔离，明确不同系统的适用范围。</p>
    </a>
  </div>
</section>

<section class="rtos-home-section">
  <div class="rtos-home-section-head">
    <p>Modules / 03</p>
    <h2>四大核心模块与工程专题</h2>
  </div>
  <div class="rtos-module-grid">
    <a href="01-RTOS-Fundamentals/"><span>01</span><strong>RTOS 通用核心机制</strong><em>Real-Time · Scheduler · Context · IPC</em></a>
    <a href="02-FreeRTOS-Deep-Dive/"><span>02</span><strong>FreeRTOS 内核实现</strong><em>Microkernel · PendSV · Queue · Heap</em></a>
    <a href="03-Zephyr-Deep-Dive/"><span>03</span><strong>Zephyr 现代化架构</strong><em>DeviceTree · Kconfig · Drivers · Userspace</em></a>
    <a href="04-Comparative-Study/"><span>04</span><strong>系统对比与选型</strong><em>Footprint · Latency · MPU · Decision Tree</em></a>
  </div>
</section>

<section class="rtos-home-section">
  <div class="rtos-home-section-head">
    <p>Practice / 04</p>
    <h2>故障分析与调试</h2>
  </div>
  <div class="rtos-practice-grid">
    <a href="Projects/rvkernel/"><span>My Project / RVKernel Lab</span><strong>RVKernel 内核实验</strong><p>QEMU RV32：Sv32 页表、SBI 定时抢占、具名管道与 4 核 SMP。</p></a>
    <a href="Case-Studies/01-priority-inversion-mars-pathfinder-case/"><span>Case 01</span><strong>火星探路者优先级反转</strong><p>从信息总线死锁现场看互斥锁优先级继承与天花板协议的作用。</p></a>
    <a href="Case-Studies/02-stack-overflow-isr-corruption-debug/"><span>Case 02</span><strong>任务栈溢出与内存破坏</strong><p>MPU 硬件 Guard 保护、Canary 水位线探测与中断现场排查定位。</p></a>
    <a href="Case-Studies/03-amp-rpmsg-heterogeneous-multicore/"><span>Case 03</span><strong>异构多核 AMP RPMsg 协同</strong><p>Linux (A核) 与 FreeRTOS/Zephyr (M核) 之间的共享内存环形缓冲与核间中断。</p></a>
  </div>
</section>

!!! note "工程说明"
    代码分析涉及 ARM Cortex-M 与 RISC-V。寄存器和上下文帧布局需结合具体处理器及内核移植版本阅读。
