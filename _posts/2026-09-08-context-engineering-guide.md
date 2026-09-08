---
layout: post
title: "上下文工程 (Context Engineering) 完全指南：KV Cache 优化、Attention 衰减与三层记忆架构"
subtitle: "为什么说“提示词已死，上下文工程当立”"
date: 2026-09-08
author: "Yvain Zhang"
series: "技术"
header-img: "img/post-bg-desk.jpg"
catalog: true
permalink: /geek/context/
tags:
    - AI
    - 上下文工程
    - KV Cache
    - 系统架构
    - 大模型
---

## 1. 范式跃迁：从 Prompt Engineering 到 Context Engineering

在 2023 年大语言模型刚普及的阶段，“Prompt Engineering（提示词工程）”曾被视为人机交互的核心技术。人们尝试在单次输入里塞入精妙的修辞、“请你扮演一位资深专家”的角色设定，或是复杂的思维链句式。

但在今天构建多轮交互、工具调用、长期存活的**自主执行系统（Autonomous Systems）**时，团队普遍发现：**提示词技巧能解决的只是单次推理质量，而系统的整体稳定性、计算开销与执行收敛性，取决于整条上下文管道的组织架构。**

这就是 **Context Engineering（上下文工程学）**。

| 维度 | 提示词工程 (Prompt Engineering) | 上下文工程 (Context Engineering) |
| :--- | :--- | :--- |
| **交互模式** | 单次或浅层问答 (One-shot / Chat) | 持续长周期自主执行循环 (Autonomous Loop) |
| **关注核心** | 单词修辞、Few-shot 示范、角色扮演 | Token 预算、KV-Cache 命中率、记忆分层、注意力衰减管理 |
| **优化目标** | 提高单次回答的拟人度与采纳率 | 降低首字延迟 (TTFT)、消解长上下文失真、确保多轮确定性收敛 |
| **工程属性** | 经验主义与黑盒调优 | 系统体系结构与确定性状态管道设计 |

---

## 2. 物理成本：Attention 机制与 KV Cache 的底层制约

理解上下文工程，首先必须理解底层计算与显存的物理制约：

### 2.1 计算复杂度与内存墙
Transformer 的标准自注意力计算中，每个 Token 都需要与前序所有 Token 计算点积：
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
当上下文长度从 8k 增加到 128k 时，计算量以平方级增加，同时 KV Cache（键值缓存）所占用的高带宽显存（HBM）也会线性暴增。一个未加节制的 Agent 几轮工具交互就可能产生数万 Token 的无用日志，导致推理集群的并发吞吐断崖式下跌。

### 2.2 Prefix Prompt Caching 的工业级落地
现代大模型推理框架（如 vLLM, SGLang, Claude, Gemini, DeepSeek）广泛引入了 **Prefix Prompt Caching（前缀提示词缓存）** 机制。

```
 ┌─────────────────────────────────────────────────────────────┐
 │  Byte-for-Byte Identical Prefix (Hit Cache: Skip Prefill)   │
 ├─────────────────────────────────────────────────────────────┤
 │ [System Prompt] ── [Tool Declarations] ── [Core Constraints]│
 └─────────────────────────────────────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  Dynamic Volatile Suffix (Sliding Window & Recent Steps)    │
 ├─────────────────────────────────────────────────────────────┤
 │ [Working Scratchpad] ── [Step History] ── [Tail Assertion]  │
 └─────────────────────────────────────────────────────────────┘
```

**工程法则：静态上下文字节级不可变**
- **必须置顶**：System Prompt、静态代码规范、所有工具的 JSON Schema 定义。
- **绝对不可注入动态变量**：切勿在前缀中拼接当前时间戳、随机数或每次变动的会话 ID！一旦前缀改变哪怕一个字符，整段前缀的 KV Cache 全部失效，导致必须全量重新计算 Prefill，不仅失去官方通常提供的 75%~90% 缓存成本折扣，更会导致首字延迟（TTFT）随提示词长度线性激增。

---

## 3. 注意力衰减与“迷失在中间 (Lost-in-the-Middle)”

学术研究（如 Stanford 关于 *Lost in the Middle: How Language Models Use Long Contexts* 的实证研究）与工程实践均表明，Transformer 模型在处理长上下文时，其注意力权重并非均匀分布，而是呈现典型的 **U 型曲线**：
- **开头部分**（Primacy Effect）：注意力极高。
- **结尾部分**（Recency Effect）：注意力最高。
- **中间部分**（Middle Depths）：注意力明显衰减，关键事实极易被忽略。

```
 Attention Weight
   ▲
1.0│ *                                                  *
   │  *                                                *
0.5│   *                                              *
   │    *                                            *
   │     * * * * * * * * * * * * * * * * * * * * * *
0.0└───────────────────────────────────────────────────────►
   Start (Prefix)           Middle (Lost)          End (Tail)
```

### 应对策略：尾部强制回填 (Tail Re-anchoring)
在每一步执行循环装配上下文时，我们在请求的最尾部增加一段简短的强约束回填：
```markdown
[CURRENT CRITICAL ANCHOR]
- Ultimate Target: Complete Wi-Fi driver packet trace analysis.
- Step Budget: 18 / 25 consumed.
- Rule: Before claiming SUCCESS, you MUST run `./tests/verify.sh` and verify exit code 0.
```
这种做法将原本沉没在中间历史中的核心约束，重新拉回到模型的最近注意力高权重区。

---

## 4. 三层记忆体系分级架构 (Layered Memory Hierarchy)

仿照计算机体系结构中 L1 Cache / L2 Cache / 主存 DDR 的分级思想，生产级 Agent 必须建立分级解耦的记忆模型：

```
 ┌──────────────────────────────────────────────────────────────┐
 │ L1: Working Scratchpad (工作记忆)                            │
 │ - 当前执行步骤的状态机寄存器、待办列表、局部环境变量           │
 │ - 驻留于 System Prompt 动态槽位，步步更新，步步清空          │
 └──────────────────────────────────────────────────────────────┘
                                ▲
                                │ 状态提炼与压缩
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ L2: Ephemeral Sliding Buffer (短暂会话缓冲)                  │
 │ - 最近 3~5 轮交互历史与直接工具返回结果                       │
 │ - 超出步数阈值执行结构化有损压缩（只保留 Exit Code 与错误行）   │
 └──────────────────────────────────────────────────────────────┘
                                ▲
                                │ 经验沉淀与向量召回
                                ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ L3: Semantic & Episodic Memory (长期语义与情景记忆)          │
 │ - 本地向量数据库 (Chromadb/Qdrant) + 知识图谱               │
 │ - 跨会话沉淀历史排错反思、代码模式与领域规范                 │
 └──────────────────────────────────────────────────────────────┘
```

### 4.1 L1 工作记忆 (Working Scratchpad)
- 类似于 CPU 的寄存器与 L1 缓存，容量极小（通常在 500 Token 以内）。
- 记录当前正在解决的微任务目标、子步骤列表（Checklist）和当前假设。

### 4.2 L2 短暂滑动缓冲 (Ephemeral Buffer)
- 保存最近的执行动作与工具输出。
- **关键技术：输出清洗压缩**。例如，执行 `make` 产生 5000 行输出，若直接注入上下文将瞬间占满窗口。压缩算法会截取前 20 行构建概况、后 50 行报错堆栈，将 5000 行压缩为 70 行结构化观察。

### 4.3 L3 长期情景记忆 (Episodic Memory)
- 将每一次排查失败的根本原因和成功修复的 diff 提交记录提取为向量 embedding。
- 当未来遇到相似的内核崩溃（如 `Kernel panic - not syncing: Fatal exception in interrupt`）时，通过语义检索将当年的修复证据链作为 Few-Shot 召回，注入给当前的 Agent。

---

## 5. 分层子代理 (Hierarchical Subagent DAG)

当单一任务需要遍历 50+ 个源文件、阅读千行规范时，单 Agent 的单上下文会发生**认知过载（Cognitive Overload）**。

### 认知过载的表象
1. 模型开始忘记最初的目标。
2. 陷入工具反复调用的无休止死循环。
3. 产生幻觉，误以为某些未修改的文件已经修改。

### 终极解法：父子代理拓扑解耦

```
                   ┌───────────────────────┐
                   │  Parent Agent (主代理) │
                   │  - 掌控全局任务计划    │
                   │  - 维持最终验收断言    │
                   └───────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │ 派发临时子任务    │ 派发临时子任务    │ 派发临时子任务
            ▼                  ▼                  ▼
     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
     │ Subagent A  │    │ Subagent B  │    │ Subagent C  │
     │ 代码全局检索│    │ 单元测试构建│    │ 文档规范查阅│
     └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
            │                  │                  │
            │ 回传结构化结论   │ 回传结构化结论   │ 回传结构化结论
            ▼                  ▼                  ▼
     [临时上下文销毁]   [临时上下文销毁]   [临时上下文销毁]
```

- **子代理上下文的瞬时性**：子代理在执行大规模全文搜索时产生的大量无关阅读上下文，在子任务结束时**随子代理一同销毁**。
- **主代理上下文的纯净性**：子代理向主代理仅回传精简的事实结论（例如：`"Symbol wpa_driver_ops is defined in src/drivers/driver_wext.c:142"`），主代理上下文始终保持轻巧高效。

---

## 6. 总结：系统级上下文管理清单

在设计你的 Agent 上下文工程时，请核对以下 Checklist：
- [ ] **Prefix 静态性**：System Prompt 与 Tools 声明是否维持字节级一致？
- [ ] **工具输出压缩**：是否有针对编译输出、抓包输出的大文本有损提取管道？
- [ ] **尾部重锚定**：在每轮推理提示词末尾，是否显式回填了目标与剩余步数？
- [ ] **子代理隔离**：耗费海量 Token 的探测型任务是否移交给了独立的子上下文？
- [ ] **断言机制**：是否使用确定性断言代替模型的自我评估？
