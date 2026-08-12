---
layout: freertos-architecture
title: "FreeRTOS 整体架构图集：RISC-V 移植版"
subtitle: "RISC-V port 的启动、Tick 和上下文切换笔记"
date: 2022-06-12
author: Yvain Zhang
header-img: "img/post-bg-debug.png"
series: "技术"
catalog: false
redirect_from:
  - /freertos-architecture.html
tags:
  - 操作系统
  - FreeRTOS
  - RISC-V
  - 嵌入式
---

这份图集从应用 API 一直画到 RISC-V 硬件层，主线是任务怎么启动、Tick 怎么进来，以及一次上下文切换究竟保存了什么。图里的代码取自 FreeRTOS-Kernel 的 RISC-V GCC port，并为阅读做了裁剪和中文注释。

如果第一次接触 RTOS，可以从前置知识开始；已经熟悉任务、调度和 trap 的话，直接跳到“上电 → 运行全流程”和“中断与上下文切换”即可。
