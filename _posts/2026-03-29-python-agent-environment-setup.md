---
layout: post
title: "Python Agent 环境配置"
subtitle: "环境不是重点，但不稳定的环境会直接拖垮学习体验"
date: 2026-03-29
author: Yvain Zhang
header-img: "img/post-bg-map.jpg"
series: "AI 与 Agent"
tags:
  - AI
  - Agent
  - Python
---

很多 Agent 入门挫败感，其实不来自概念，而来自环境。

## 1. 环境配置要先解决什么

至少先保证三件事：

- Python 版本清楚
- 依赖隔离清楚
- 模型或 API 接入方式清楚

如果这些混在一起，后面任何问题都很难判断是代码问题还是环境问题。

## 2. 更稳妥的起步方式

建议一开始就做：

- 使用虚拟环境
- 把依赖写进 `requirements.txt` 或类似文件
- 单独验证 API 可用性
- 用最小脚本先跑通

## 3. 为什么这一步不能跳

因为 Agent 系统通常会同时依赖：

- 模型 SDK
- HTTP 请求库
- 工具调用依赖
- 向量库或存储组件

环境一旦不稳，定位成本会迅速上升。
