---
layout: post
title: "FreeRTOS 整体架构图集：RISC-V 移植版"
subtitle: "RISC-V port 的启动、Tick 和上下文切换笔记"
date: 2022-06-12
author: Yvain Zhang
header-img: "img/post-bg-debug.png"
series: "技术"
catalog: false
tags:
  - 操作系统
  - FreeRTOS
  - RISC-V
  - 嵌入式
---

这份图集把 FreeRTOS 从应用 API 一直画到 RISC-V 硬件层。新版增加了面向新手的前置知识和完整术语表，再逐步进入 TCB、任务状态、调度器启动、Tick 中断和上下文切换。

图中的第 3、4 节以 FreeRTOS-Kernel 的 RISC-V GCC port 为参照，代码片段来自 `port.c`、`portASM.S` 和 `portmacro.h`，为了阅读做了裁剪和中文注释。这里讨论的是机器模式、单核移植；具体芯片仍要结合自己的 startup、CLINT 和 BSP 实现来看。

下方是完整交互版。目录可以跳转章节，“上电 → 正常工作”部分可以逐步展开或一键全部展开，模块速查表也支持关键字筛选。窄屏阅读时，建议点右上角链接单独打开。

<div class="interactive-post-shell">
  <div class="interactive-post-toolbar">
    <div>
      <span>Interactive note</span>
      <strong>FreeRTOS Architecture / RISC-V</strong>
    </div>
    <a href="{{ '/freertos-architecture.html' | prepend: site.baseurl }}" target="_blank" rel="noopener noreferrer">全屏打开 <span aria-hidden="true">↗</span></a>
  </div>
  <div class="interactive-post-frame">
    <iframe src="{{ '/freertos-architecture.html' | prepend: site.baseurl }}" title="FreeRTOS 整体架构图集：RISC-V 移植版" loading="eager"></iframe>
  </div>
  <noscript><p>当前浏览器未启用 JavaScript。你仍可以<a href="{{ '/freertos-architecture.html' | prepend: site.baseurl }}">打开完整图集</a>阅读静态内容。</p></noscript>
</div>

阅读时我建议先看第一节的分层，再直接跳到第三、四节。内核对象的 API 很多，但移植时真正需要抓住的主线并不长：先准备任务初始栈帧，再建立 Tick，trap 发生后保存当前任务、选择下一个 TCB，最后从新任务的栈中恢复现场。

这条线看清之后，再回头读 `tasks.c`、某个芯片的 `startup.S`，或者对照 Cortex-M 的 PendSV 路径，位置感会清楚很多。
