---
layout: post
title: "从 buffer 的寿命谈平台设计"
subtitle: "由一个异步队列问题，连到事件、停止与跨运行时契约"
date: 2026-10-04
author: Yvain Zhang
header-img: "img/post-bg-unix-linux.jpg"
series: "技术"
tags:
  - Linux
  - 系统架构
  - 异步 IO
---

把 buffer 的地址送进队列，提交函数返回后就把它归还给池。如果消费者稍后才使用这个地址，期间另一份请求已经覆写了内存，消费者看到的内容就会变。队列正常、线程也在运行，数据仍然可能错。

这个问题的起点很小，却会牵出一串平台设计问题：队列保存了什么，谁拥有对象，哪一层算完成，出错时谁回收，停止时还欠哪些通知。我把相关机制和实验整理成了 [平台架构实践]({{ '/tech/platform/' | relative_url }})，沿着这些关联继续展开。

## 先把接口的寿命说清楚

借用、复制与转移会形成不同的责任。借用要求调用者保留对象到规定的完成点；复制可以让原 buffer 更早复用，但需要额外内存与拷贝；转移则要说明成功和失败各由谁释放。

锁能保护一次访问，接口还需要定义整个异步过程的寿命。[fd 与对象寿命]({{ '/tech/platform/mechanisms/03-fd-lifetime/' | relative_url }})和[队列与所有权]({{ '/tech/platform/mechanisms/07-concurrency-ownership/' | relative_url }})分别用对象关系和执行时序说明这件事。

## “提交成功”之后还有几层状态

示例 SDK 提交时复制 payload，并先返回排队 ticket。owner 后续决定接受或拒绝；被接受的请求再进入完成、超时、取消或失败。取消事件进入队列，也不保证抢先于响应。

这些层次决定了统计、错误处理和停止义务。公平处理预算可以限制一轮事件的工作量，但停止时仍需处理剩余 ticket 的结果通知。[停止收尾案例]({{ '/tech/platform/cases/01-stop-drain/' | relative_url }})给出受控的队列场景与两套守恒关系。

## 再连接到运行时和平台预算

同一套接受、完成与恢复语义，可以由 Linux 的线程、epoll、eventfd 实现，也可以由 FreeRTOS 的任务、队列与通知实现。共同契约放在哪里、平台机制保留在哪里，会影响移植和验证范围。[双运行时章节]({{ '/tech/platform/design/03-linux-freertos/' | relative_url }})沿着这个问题比较两端实现。

扩大在途额度还会影响吞吐、排队、尾延迟和停止时间；缩小逻辑额度也不自动缩小固定结构占用。[资源预算]({{ '/tech/platform/design/06-resource-budget/' | relative_url }})把这些约束放到同一张账里，再比较候选方案。

专题中的章节由具体问题扩展，阅读索引按知识依赖组织。可以从一个案例进入，再追到相关机制；也可以从 C、fd、IO、进程和事件顺着读。

实验使用独立 Linux 工具容器、FreeRTOS POSIX port 和专用 QEMU 软件设备。源码、命令和结果范围分别见[下载页]({{ '/tech/platform/reference/source/' | relative_url }})、[环境准备]({{ '/tech/platform/guide/environment/' | relative_url }})和[验证记录]({{ '/tech/platform/reference/verification/' | relative_url }})。
