---
layout: post
title: "Skills 是什么"
subtitle: "把高频任务封成可复用能力，而不是每次都从零提示"
date: 2026-03-29
author: Yvain Zhang
header-img: "img/post-bg-unix-linux.jpg"
series: "AI 与 Agent"
tags:
  - AI
  - Agent
  - Skills
---

Agent 真正开始变得稳定，往往不是因为模型突然更聪明，而是因为高频任务被沉淀成了 Skills。

## 1. Skills 本质上是什么

可以把它理解成：

- 预定义任务模板
- 固定工具组合
- 稳定输出格式
- 可复用执行习惯

它的作用，是把“每次重新描述任务”变成“直接调用一个可复用能力”。

## 2. 为什么这很重要

因为很多真实工作并不是一次性的，例如：

- 代码审查
- 文档摘要
- bug 初筛
- 数据整理

这些任务如果总靠临时 prompt，稳定性会很差。

## 3. Skills 和 prompt 的区别

Prompt 更像一次性指令。  
Skill 更像经过沉淀的操作模块。

后者更强调：

- 边界清楚
- 输入明确
- 输出稳定
- 可反复使用
