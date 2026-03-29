---
layout: post
title: "LangChain 制作智能体"
subtitle: "把模型、提示词、工具和链式流程组织起来"
date: 2026-03-29
author: Yvain Zhang
header-img: "img/post-bg-map.jpg"
series: "AI 与 Agent"
tags:
  - AI
  - Agent
  - LangChain
---

LangChain 的位置比较特别。它既不是单纯模型接口，也不是只讲 Agent，而是想把整套 LLM 应用拼装能力组织起来。

## 1. 为什么很多 Agent 教程都会提它

因为 LangChain 很适合用来组合这些部件：

- 模型调用
- Prompt 模板
- 工具
- 记忆
- 链式流程

Agent 只是它能力图谱中的一个部分。

## 2. 它最适合什么人

如果你希望：

- 快速把多个模块串起来
- 不想所有接口都手写
- 需要一套统一抽象

那 LangChain 很适合作为实验和原型工具。

## 3. 使用时要保持什么警惕

抽象层多的好处是快，代价是：

- 调试路径更长
- 实际行为更难一眼看透
- 性能和错误边界不总是显式

所以用它时，最好始终知道自己到底封装掉了哪些细节。
