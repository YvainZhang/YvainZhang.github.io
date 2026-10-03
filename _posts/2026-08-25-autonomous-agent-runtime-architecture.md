---
layout: post
title: "Agent 运行时设计笔记：控制循环、参数校验与外部验收"
subtitle: "按六个阶段梳理执行流程，附 Python 参考骨架和实现边界"
date: 2026-08-25
author: "Yvain Zhang"
series: "技术"
header-img: "img/post-bg-unix-linux.jpg"
catalog: true
permalink: /geek/runtime/
tags:
    - AI
    - Agent
    - 系统架构
    - 运行时
    - Python
---

## 1. 让模型输出接上环境反馈
{: id="1-为什么问答式-llm-无法解决真实工程任务"}

模型可以根据输入给出代码和排查建议，但如果没有工具反馈，就无法直接确认文件是否修改、代码是否编译通过，或设备是否处于预期状态。多轮对话可以由应用保存历史，运行状态也需要应用维护。

在代码重构、固件调试或网络排障中，运行时需要处理几个问题：
1. **环境反馈**：把编译、测试或设备查询结果返回给模型，区分建议与已验证事实。
2. **执行状态**：记录任务进度、失败原因和下一步动作，限制重复调用和无进展的重试。
3. **副作用与权限**：明确工具可访问的路径、可执行的动作，以及哪些操作需要授权或恢复方案。

本文把 Agent 运行时按目标、上下文、决策、执行、观察和状态更新六个阶段拆开讨论。有限状态机（FSM）可用于规定允许的转移；下面的代码则演示较简化的顺序控制循环，并未实现完整的状态转移表。

```
 ┌──────────────────────────────────────────────────────────────┐
 │               AUTONOMOUS RUNTIME CONTROL LOOP                │
 └──────────────────────────────────────────────────────────────┘
           │
           ▼
   [01. 根目标规范化]  ──> 注入 Step/Token 预算、只读环境约束
           │
           ▼
   [02. 上下文装配]    ──> 前缀缓存 (Prefix Cache) 对齐 + 注意力预算裁剪
           │
           ▼
   [03. 决策推理]      ──> LLM 产生结构化 Tool Call 或完成声明
           │
     ┌─────┴─────────────────────┐
     ▼                           ▼
[Tool Call 命中]           [任务收敛判定]
     │                           │
     ▼                           ▼
[04. 沙箱受控执行]          [最终断言评估]
  - 权限与隔离边界            - 单元测试与构建检查
  - 超时心跳熔断              - 产物完整性验证
  - 破坏性命令拦截                 │
     │                           ▼
     ▼                    [成功终结退出]
[05. 观察提取与清洗]
  - 提取 Exit Code 与 Trace
  - 日志截断与脱敏
     │
     ▼
[06. 状态更新与 Reflexion] ──> 回写工作记忆，策略微调，进入下一轮
```

---

## 2. 三个运行时设计问题
{: id="2-核心架构三大硬约束公理-runtime-axioms"}

设计执行循环时，可以先明确工具范围、状态来源和失败恢复方式。

### 一：限制工具范围与执行预算
{: id="公理一约束优于自由-constraint-over-freedom"}
- 用 JSON Schema 或 Pydantic 等校验工具参数，在执行前返回类型、必填字段或范围错误。通过校验的参数仍可能在业务语义上不合适。
- 设定 **Step Budget（最大步数限制，如 25 步）**、Token 和时间预算。预算耗尽时返回未完成状态，而不是继续无上限重试。

### 二：显式记录环境状态
{: id="公理二状态显式化-explicit-state-representation"}
运行时可以维护以下状态，并将本轮需要的部分提供给模型：
- **当前激活的工作路径**（Working Directory）
- **当前已修改但未提交的文件清单**（Dirty File List）
- **当前步骤消耗与剩余步数**（Step Counter）
- **环境检查的关键断言结果**（Assertion Status）

状态应来自实际工具查询或运行时记录，不能只沿用模型的描述。放在动态上下文区域可避免频繁改变静态前缀。

### 三：定义失败后的恢复方式
{: id="公理三工具原子化与回滚守卫-atomic--rollback-guard"}
- 文件修改可以先创建快照，失败后恢复该步骤触及的文件。恢复时要保留用户原有改动；外部设备写入或网络操作不一定可回滚。
- 命令执行需要持续读取输出、设置超时并回收进程。交互程序可使用 PTY，普通构建也可使用管道；PTY 本身不是安全沙箱。
- 区分可重复执行的幂等操作与有副作用的操作，避免重试时重复提交或写入。

---

## 3. 六阶段状态机执行流详解

### Stage 1: 目标规范化 (Goal & Constraints Initialization)
接收用户指令，记录任务目标、验收要求和初始环境信息：
- 工作区绝对路径（Workspace Root）
- 权限安全模式（Safe / Approval / Bypass）
- 初始环境快照（Git HEAD Commit）

### Stage 2: 上下文装配与预算裁剪 (Context Assembly)
上下文装配阶段组织模型请求中的消息：
1. **稳定前缀（Stable Prefix）**：包含系统提示词、工具声明和静态规范。保持一致有利于前缀缓存复用，但实际命中还取决于服务的缓存规则。
2. **近期历史（Recent History）**：按任务保留最近几轮工具交互，例如 3~4 轮；窗口大小需要结合上下文预算调整。
3. **历史摘要（Compact Summary）**：提取较早步骤中的决定、错误与修复记录，例如 `[COMPACT: Step 1-3 compile failed with C2065, fixed in Step 4]`。完整记录另存，必要时回查。

### Stage 3: 模型决策与参数路由 (Inference & Tool Routing)
调用模型生成输出。输出通常分为两类：
- **Tool Use**：模型识别出需要调用工具获取信息或修改系统。运行时提取 `tool_name` 与 `tool_args`。
- **Final Message**：模型认为任务已达成，输出总结性报告。

### Stage 4: 沙箱隔离执行 (Sandboxed Execution)
工具分发器先校验权限和参数，再执行动作。下面只是流程示意，命令模式匹配不能代替操作系统隔离：
```python
def dispatch_command(cmd_args: List[str], timeout_sec: int = 30) -> ToolResult:
    # 1. 检查已列出的危险命令模式；可执行文件白名单需另行实现
    cmd_line = " ".join(cmd_args)
    if any(pat.search(cmd_line) for pat in DANGEROUS_PATTERNS):
        return ToolResult(status=ToolStatus.SECURITY_BLOCK, error="Security Guard: Dangerous command blocked.")

    # 2. 独立会话进程组隔离运行 (start_new_session=True 或 os.setsid)
    # 3. 管道数据超时轮询读取防死锁，超时触发整组 killpg 级联终止
    # ...
```

### Stage 5: 观察清洗与确定性断言 (Observation & Assertion)
工具执行后，可以从长日志中提取本轮需要的信息：
- 剥离无用的进度条文本（如 `[===>    ] 34%`）。
- 提取非零退出码和包含 `error:`, `fatal:`, `panic` 的核心错误堆栈。
- 运行针对性检查：例如 `python -m py_compile` 或 `gcc -fsyntax-only`。语法检查只能说明对应检查通过，功能正确性还需测试或其他验收。

### Stage 6: 状态流转与 Reflexion 反思 (State Transition)
将清洗后的结构化观察回写进会话记忆：
- 若观察表明操作成功，推进子任务进度表。
- 若操作失败，可以要求模型说明下一轮排查依据：
  > “上一步失败的原因是什么？当前的假设错在哪里？下一步应当如何调整策略？”

---

## 4. 控制循环参考骨架实现：Python 核心状态机与进程安全守卫

本节代码展示参数检查、历史裁剪、子进程调用和外部验收如何接到同一循环。它是参考骨架，需要补上 `llm_client`、工具注册和验收器才能使用。

阅读时有几个实现边界要分清：`max_tokens` 尚未参与实际计数；`prune()` 丢弃较早历史并插入固定提示，并没有生成内容摘要；参数检查只覆盖部分字段类型，不是完整 JSON Schema 校验。进程组便于终止同组进程，但不限制文件或网络权限，脱离该组的后代也不在清理范围内。管道 `poll()` 的超时不等于整个接收过程都有同样的期限。代码依赖 Unix 进程机制，其他启动方式需要调整。

实际部署还需补充权限隔离、输出限制、完整超时处理和任务状态持久化，不能把示例中的命令正则当作安全边界。

```python
"""
Minimal Autonomous Agent Runtime Skeleton (可终止进程执行与契约校验参考实现)
Author: Yvain Zhang
Architecture: ReAct FSM + Context Budget + Schema Validation + Process Watchdog + External Verifier
Note: 用于阅读控制流程；权限隔离、完整预算与超时处理需另行实现。
"""

import os
import sys
import json
import re
import time
import signal
import multiprocessing as mp
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Any, List, Optional

class ToolStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SECURITY_BLOCK = "SECURITY_BLOCK"

@dataclass
class ToolResult:
    status: ToolStatus
    output: str
    exit_code: int = 0
    error: Optional[str] = None

@dataclass
class ToolSpec:
    name: str
    description: str
    schema: Dict[str, Any]  # JSON Schema 格式参数契约
    handler: Callable[..., Any]
    is_destructive: bool = False

def sanitize_timeout(timeout_val: Any, default_sec: float = 30.0, min_sec: float = 0.001, max_sec: float = 300.0) -> float:
    """校验并归一化超时参数，防止 null、非法字符串或负值导致看门狗崩溃"""
    if timeout_val is None:
        return default_sec
    try:
        t = float(timeout_val)
        if t <= 0:
            return default_sec
        return min(max(t, min_sec), max_sec)
    except (ValueError, TypeError):
        return default_sec

def validate_schema(schema: Dict[str, Any], args: Any) -> Optional[str]:
    """轻量级参数契约校验器：先验证 args 为字典对象，再检查必填项与字段类型，拦截非法入参"""
    if args is None:
        return "参数对象为空 (null)，预期为包含工具入参的 JSON 字典对象"
    if not isinstance(args, dict):
        return f"参数格式非法: 预期为字典 (JSON Object)，实际传入 {type(args).__name__}"

    required = schema.get("required", [])
    for field in required:
        if field not in args:
            return f"缺少必填参数 '{field}'"

    properties = schema.get("properties", {})
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    for key, val in args.items():
        if key in properties:
            expected_type_name = properties[key].get("type")
            expected_type = type_map.get(expected_type_name)
            if expected_type_name == "integer" and isinstance(val, bool):
                return f"参数 '{key}' 应为 integer，不能传入 bool"
            if expected_type and not isinstance(val, expected_type):
                return f"参数 '{key}' 类型错误: 预期 {expected_type_name}，实际为 {type(val).__name__}"
    return None

class ContextBudgetManager:
    """按近期轮数裁剪历史；未实现 Token 计数或历史内容摘要"""
    def __init__(self, max_tokens: int = 128000, keep_recent_turns: int = 4):
        self.max_tokens = max_tokens
        self.keep_recent_turns = keep_recent_turns

    def prune(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if len(messages) <= (self.keep_recent_turns * 2 + 2):
            return messages

        prefix = messages[:2]  # 保持前缀不可变 (System Prompt + 根目标)，最大化 Prefix Cache 命中
        recent = messages[-(self.keep_recent_turns * 2):]
        compact_summary = {
            "role": "system",
            "content": "[SYSTEM COMPACT: 前序探索步骤已折叠。请专注于当前激活的任务分支与测试断言。]"
        }
        return prefix + [compact_summary] + recent

def _kill_process_tree(proc: mp.Process):
    """尝试终止 worker 及同组进程；不覆盖脱离该进程组的后代"""
    pid = proc.pid
    if not pid:
        return

    parent_pgid = os.getpgrp()

    # 1. 尝试向 worker 建立的独立进程组发送 SIGTERM（优雅终止）
    # 若 worker 的 os.setsid() 成功，其 PGID 等于 pid
    if pid != parent_pgid:
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    # 兜底直接向 worker 进程发送 SIGTERM
    try:
        proc.terminate()
    except Exception:
        pass

    # 给予短暂优雅退出窗口
    proc.join(timeout=0.05)

    # 2. 再向该进程组发送 SIGKILL
    # 同组内忽略 SIGTERM 的后代进程也会收到该信号
    if pid != parent_pgid:
        try:
            os.killpg(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    # 兜底对 worker 发送 SIGKILL
    try:
        if proc.is_alive():
            proc.kill()
    except Exception:
        pass

    try:
        proc.join(timeout=0.05)
    except Exception:
        pass

class ToolDispatcher:
    """部分参数类型校验、进程组执行与超时检查示例；未实现权限沙箱"""
    def __init__(self):
        self.registry: Dict[str, ToolSpec] = {}
        self.dangerous_patterns = [
            re.compile(r"\brm\s+-rf\s+/", re.IGNORECASE),
            re.compile(r"\bmkfs(\.\w+)?\b", re.IGNORECASE),
            re.compile(r"\bdd\s+if=", re.IGNORECASE),
            re.compile(r":\(\)\{.*\}")  # fork bomb
        ]

    def register(self, spec: ToolSpec):
        self.registry[spec.name] = spec

    def dispatch(self, name: str, args: Any, timeout_sec: Any = 30.0, allow_destructive: bool = False) -> ToolResult:
        if name not in self.registry:
            return ToolResult(status=ToolStatus.FAILURE, output="", exit_code=1, error=f"未注册的工具: {name}")

        spec = self.registry[name]

        # 1. 契约校验：在调用前拦截 null、非对象或缺失必填项的参数
        schema_err = validate_schema(spec.schema, args)
        if schema_err:
            return ToolResult(status=ToolStatus.VALIDATION_ERROR, output="", exit_code=2, error=f"参数契约校验失败: {schema_err}")

        # 2. 超时参数归一化与破坏性操作安全检查
        clean_timeout = sanitize_timeout(timeout_sec)

        if spec.is_destructive and not allow_destructive:
            return ToolResult(status=ToolStatus.SECURITY_BLOCK, output="", exit_code=126, error=f"安全阻断: 工具 '{name}' 涉及破坏性操作，未获显式授权。")

        for val in args.values():
            if isinstance(val, str):
                for pat in self.dangerous_patterns:
                    if pat.search(val):
                        return ToolResult(status=ToolStatus.SECURITY_BLOCK, output="", exit_code=126, error=f"安全阻断: 检测到高危指令模式 '{pat.pattern}'")

        # 3. 在 worker 进程中执行工具，并尝试建立独立进程组
        ctx = mp.get_context("fork" if hasattr(os, "fork") else None)
        parent_conn, child_conn = ctx.Pipe()

        def _worker(conn, fn, kwargs):
            # 脱离父会话成为独立 Process Group Leader，使后续派生的 shell/子命令归入同组
            try:
                os.setsid()
            except Exception:
                pass
            try:
                r = fn(**kwargs)
                conn.send((True, r))
            except Exception as e:
                conn.send((False, str(e)))
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        proc = ctx.Process(target=_worker, args=(child_conn, spec.handler, args))
        proc.start()
        child_conn.close()  # 父进程关闭子端，防止句柄泄露

        # 等待管道可读；后续 recv 的完整读取还需单独处理超时与输出上限
        if not parent_conn.poll(clean_timeout):
            # 等待超时：尝试终止 worker 及其同组进程
            _kill_process_tree(proc)
            parent_conn.close()
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                output="",
                exit_code=124,
                error=f"工具执行超时 (超过 {clean_timeout} 秒)，已尝试终止工具进程及其同进程组内的子进程。"
            )

        # 管道就绪后立即读取排空数据，解除 worker 端 send 阻塞，随后回收进程
        try:
            ok, val = parent_conn.recv()
            parent_conn.close()
            proc.join(timeout=0.5)
            if proc.is_alive():
                _kill_process_tree(proc)

            if ok:
                return val if isinstance(val, ToolResult) else ToolResult(status=ToolStatus.SUCCESS, output=str(val))
            return ToolResult(status=ToolStatus.FAILURE, output="", exit_code=1, error=str(val))
        except EOFError:
            parent_conn.close()
            _kill_process_tree(proc)
            return ToolResult(
                status=ToolStatus.FAILURE,
                output="",
                exit_code=proc.exitcode or 1,
                error=f"工具进程异常退出 (exit code: {proc.exitcode})，未接收到返回数据。"
            )
        except Exception as e:
            parent_conn.close()
            _kill_process_tree(proc)
            return ToolResult(status=ToolStatus.FAILURE, output="", exit_code=1, error=str(e))

class AutonomousRunner:
    """Agent 主控制循环：感知 -> 推理 -> 执行 -> 观察 -> 外部独立验收"""
    def __init__(self, llm_client, dispatcher: ToolDispatcher, verifier: Optional[Callable[[], ToolResult]] = None, max_steps: int = 25):
        self.llm = llm_client
        self.dispatcher = dispatcher
        self.verifier = verifier  # 外部验收器，检查结果是否符合任务要求
        self.budget = ContextBudgetManager()
        self.max_steps = max_steps
        self.history: List[Dict[str, str]] = []

    def execute_goal(self, goal: str, system_prompt: str) -> Dict[str, Any]:
        self.history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"目标任务: {goal}\n规则: 请逐步执行。只有当客观验收断言真正通过后，任务方可结束。"}
        ]

        for step in range(1, self.max_steps + 1):
            # 1. 缓存对齐与上下文裁剪装配
            active_context = self.budget.prune(self.history)

            # 2. 大模型决策推理
            decision = self.llm.generate_decision(messages=active_context)

            # 3. 模型声明完成后，调用外部验收器；未配置时返回未验证状态
            if decision.get("is_complete"):
                if self.verifier is None:
                    return {
                        "status": "SUCCESS_UNVERIFIED",
                        "steps": step,
                        "output": decision.get("final_summary"),
                        "warning": "未配置独立验证器，结果未经验收断言"
                    }

                # 运行外部独立断言器（如 make test / pytest / 物理硬件状态查询）
                verify_res = self.verifier()
                if verify_res.status == ToolStatus.SUCCESS:
                    return {"status": "SUCCESS", "steps": step, "output": decision.get("final_summary")}
                else:
                    # 将验收失败结果加入上下文，进入下一轮修正
                    obs_entry = (
                        f"[第 {step} 步独立验收失败] 退出码: {verify_res.exit_code}\n"
                        f"断言报错: {verify_res.error or verify_res.output}\n"
                        f"系统判定: 任务尚未完成，模型不可提前声明成功。请根据客观报错修正并重新执行。"
                    )
                    self.history.append({"role": "assistant", "content": json.dumps(decision)})
                    self.history.append({"role": "user", "content": obs_entry})
                    continue

            # 4. 工具分发执行
            tool_name = decision.get("tool_name", "")
            tool_args = decision.get("tool_args")  # 保留原始值，交由 dispatcher 严格校验
            timeout_sec = decision.get("timeout_sec", 30.0)
            tool_result = self.dispatcher.dispatch(tool_name, tool_args, timeout_sec=timeout_sec)

            # 5. 观察清洗与结构化记忆追加
            obs_preview = tool_result.output[:800] if tool_result.output else "[无标准输出]"
            obs_entry = f"[第 {step} 步观察] 状态: {tool_result.status.value}, 返回码: {tool_result.exit_code}\n输出截取: {obs_preview}"
            if tool_result.error:
                obs_entry += f"\n错误跟踪: {tool_result.error}"

            self.history.append({"role": "assistant", "content": json.dumps(decision)})
            self.history.append({"role": "user", "content": obs_entry})

        return {"status": "BUDGET_EXHAUSTED", "steps": self.max_steps, "error": "超出最大步数预算，系统未能在限制步数内收敛。"}
```

---

## 5. 从小范围任务开始验证
{: id="5-总结与工程落地建议"}

1. **限制初始范围**：可先选择只读排查、测试运行或单文件修复，检查循环是否能正确处理成功、失败和预算耗尽。
2. **按任务定义验收**：编译和测试的 exit 0 是证据之一，还要确认检查覆盖了任务要求，并记录未验证部分。
3. **按复用需求组织工具**：需要被多个客户端调用的工具可用 MCP 暴露，本地函数也适合小范围实验。
