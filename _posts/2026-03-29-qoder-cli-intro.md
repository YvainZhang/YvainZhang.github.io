---
layout: post
title: "Qoder CLI 入门"
subtitle: "终端里的 Agent，不只是写代码，更是在接管一部分开发流程"
date: 2026-03-29
author: Yvain Zhang
header-img: "img/post-bg-unix-linux.jpg"
series: "AI 与 Agent"
tags:
  - AI
  - Agent
  - CLI
---

CLI 形态的 Agent 工具有一个很明显的优势：  
它天然适合融入已有开发流程。

## 1. 为什么 CLI 形态值得重视

因为开发者很多真正高频的动作都在终端里：

- 跑测试
- 查日志
- 改文件
- 调 git

当 Agent 在 CLI 里工作，它就更容易接到真实上下文。

## 2. 它适合什么工作

- 小步修改
- 批量分析
- 和现有 shell 工具链联动
- 自动化一些重复命令流

## 3. 使用边界

CLI Agent 很强，但也更容易误操作。  
所以权限、命令范围、工作目录边界这些约束，必须在工具设计里说清楚。
