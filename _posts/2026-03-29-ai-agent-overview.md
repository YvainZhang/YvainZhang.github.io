---
layout: post
title: "AI Agent 教程总览"
subtitle: "先把概念、结构、实现路线和工具生态放到一张图里"
date: 2026-03-29
author: Yvain Zhang
header-img: "img/post-bg-unix-linux.jpg"
series: "AI 与 Agent"
tags:
  - AI
  - Agent
  - LLM
---

最近很多人一提 Agent，就会立刻跳到某个框架或者某个产品。但如果结构没先理顺，后面很容易变成“工具名记了一堆，真正落地还是不知道从哪里开始”。

这组文章准备按四条线展开：

- 基础认知：Agent 到底是什么，和普通聊天模型差在哪
- 结构原理：规划、工具、记忆、反馈循环怎么协同
- Python 实现：怎样从一个最小可运行 Agent 开始
- 工具生态：LangChain、CrewAI、Claude Code、OpenCode 这类工具分别适合什么场景

## 1. Agent 不是聊天增强版

更实用的理解是：

`Agent = LLM + Planning + Tool use + Memory`

其中 LLM 负责理解和推理，Planning 负责拆任务，Tool use 负责把动作落地，Memory 负责保存上下文和状态。  
真正的区别不在于“回答更像人”，而在于它能不能围绕一个目标连续执行。

## 2. 学这套东西最好按什么顺序

如果直接上框架，通常会先被概念和术语淹没。更稳妥的路径是：

1. 先搞清楚 Agent 的结构和工作流
2. 再写一个最小 Agent，理解工具调用和状态保存
3. 最后再看框架和现成工具，判断哪些值得用

这个顺序的意义很直接：  
先理解“为什么需要这些部件”，再理解“框架帮你封装了什么”。

## 3. 这组文章会覆盖什么

后面的文章会把这个专题拆成若干更小的话题，例如：

- AI Agent 简介
- 核心组件
- 工作原理
- 提示词工程
- 第一个 Agent
- 工具调用与记忆系统
- LangChain / CrewAI
- Claude Code / OpenCode / Qoder CLI / Trae Solo

## 4. 怎么判断自己有没有学会

一个很实用的标准不是“会不会复述定义”，而是能不能回答下面这几个问题：

- 这个任务为什么需要 Agent，而不只是一个普通 prompt
- 它的规划步骤在哪里
- 工具调用边界在哪里
- 中间状态和长期状态怎么保存
- 出错时如何回退和继续执行

如果这些问题能答清楚，再看具体工具，效率会高很多。
