---
layout: post
title: "自治 Agent 核心运行时与有限状态机 (FSM) 工程实战：沙箱隔离、超时熔断与自愈闭环"
subtitle: "从有限状态机、参数契约校验、并发超时看门狗到独立外部验收"
date: 2026-09-08
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

## 1. 为什么问答式 LLM 无法解决真实工程任务？

在大语言模型被广泛用作聊天助手（Chatbot）时，整个交互模型是单轮或基于直觉的多轮追加：用户输入一段文本，模型返回一段文本。这种模式被称为 **Stateless Generation（无状态生成）**。

但在操作系统、芯片固件、复杂代码重构以及长周期网络排障等真实工程场景中，单次生成面临致命缺陷：
1. **缺乏环境感知反馈**：模型无法确认自己编写的代码是否能通过编译，也无法确认自己修改的驱动寄存器是否引发死锁。
2. **缺乏原子动作与状态机约束**：模型极易陷入虚假推断（Hallucination），当中间某个步骤出错时，只会盲目道歉并重复错误代码。
3. **不可逆副作用失控**：如果在没有权限围栏的真实终端中随意执行命令，一条错误的 `rm -rf` 或破坏性写盘操作将直接摧毁开发环境。

**工业级自治 Agent（Autonomous Agent）的本质，不是让大模型更像人说话，而是一个以大模型为决策内核、由确定性有限状态机（FSM）进行约束、并在受控沙箱中执行工具并根据环境反馈持续自愈的控制系统。**

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
   [03. 决策推理]      ──> LLM 产生思考链 (Thought) 与结构化 Tool Call
           │
     ┌─────┴─────────────────────┐
     ▼                           ▼
[Tool Call 命中]           [任务收敛判定]
     │                           │
     ▼                           ▼
[04. 沙箱受控执行]          [最终断言评估]
  - PTY 伪终端隔离            - 单元测试与构建检查
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

## 2. 核心架构三大硬约束公理 (Runtime Axioms)

在设计自动化执行引擎时，我们总结了三条不容妥协的工程硬约束：

### 公理一：约束优于自由 (Constraint Over Freedom)
给模型过高的自由度是灾难的开端。必须将任务解空间严格限制在预设的工具集合与状态转移矩阵中：
- 工具的入参必须使用强类型声明（如 JSON Schema 或 Pydantic 校验），非法参数在执行前直接拦截报错并要求模型纠偏，杜绝传参幻觉。
- 设定不可逾越的 **Step Budget（最大步数限制，如 25 步）** 与 **Token Budget**，防止因模型死循环而耗尽配额。

### 公理二：状态显式化 (Explicit State Representation)
绝不依赖大模型在漫长的自注意力机制中隐式“记住”环境状态。
- **当前激活的工作路径**（Working Directory）
- **当前已修改但未提交的文件清单**（Dirty File List）
- **当前步骤消耗与剩余步数**（Step Counter）
- **环境检查的关键断言结果**（Assertion Status）

这些状态必须在每轮推理提示词的尾部作为强约束元数据显式序列化注入，消除上下文膨胀带来的状态漂移。

### 公理三：工具原子化与回滚守卫 (Atomic & Rollback Guard)
所有可调用工具必须具备幂等性与事务保护：
- 在调用代码修改工具前，运行时自动对目标文件创建临时快照（Shadow Backup）。若执行过程异常或语法校验崩溃，自动回滚至干净状态。
- 终端命令执行必须跑在非阻塞 PTY（伪终端）内部，设置严格的超时阈值（如单命令默认 30 秒），超时自动发出 `SIGTERM` / `SIGKILL` 终止子进程，坚决防止交互提示符挂死。

---

## 3. 六阶段状态机执行流详解

### Stage 1: 目标规范化 (Goal & Constraints Initialization)
接收用户自然语言指令，解析出根任务目标，并锁定不可变的上下文元数据：
- 工作区绝对路径（Workspace Root）
- 权限安全模式（Safe / Approval / Bypass）
- 初始环境快照（Git HEAD Commit）

### Stage 2: 上下文装配与预算裁剪 (Context Assembly)
上下文装配阶段负责组织即将喂给大模型的完整消息数组：
1. **不可变前缀（Immutable Prefix）**：包含系统提示词、可用工具声明、静态规范。该部分严格保持字节级不变，以确保触发大模型推理引擎（如 Gemini / Claude）的 **Prefix Prompt Caching**，免去重复 Prefill 计算并显著改善首字生成时延与吞吐表现。
2. **动态滑动窗口（Sliding History）**：只保留最近 3~4 轮的完整工具交互日志。
3. **压缩摘要（Folded Ephemera）**：超过 4 轮的中间试错日志，折叠为结构化的摘要（如 `[COMPACT: Step 1-3 compiled failed with C2065, fixed in Step 4]`），大幅降低长文本注意力负担。

### Stage 3: 模型决策与参数路由 (Inference & Tool Routing)
调用模型生成输出。输出通常分为两类：
- **Tool Use**：模型识别出需要调用工具获取信息或修改系统。运行时提取 `tool_name` 与 `tool_args`。
- **Final Message**：模型认为任务已达成，输出总结性报告。

### Stage 4: 沙箱隔离执行 (Sandboxed Execution)
工具分发器执行具体动作：
```python
def dispatch_command(cmd_args: List[str], timeout_sec: int = 30) -> ToolResult:
    # 1. 危险命令模式与可执行文件白名单拦截
    cmd_line = " ".join(cmd_args)
    if any(pat.search(cmd_line) for pat in DANGEROUS_PATTERNS):
        return ToolResult(status=ToolStatus.SECURITY_BLOCK, error="Security Guard: Dangerous command blocked.")

    # 2. 独立会话进程组隔离运行 (start_new_session=True 或 os.setsid)
    # 3. 管道数据超时轮询读取防死锁，超时触发整组 killpg 级联终止
    # ...
```

### Stage 5: 观察清洗与确定性断言 (Observation & Assertion)
工具执行完后，不能把动辄上万行的编译器输出原封不动塞回上下文：
- 剥离无用的进度条文本（如 `[===>    ] 34%`）。
- 提取非零退出码和包含 `error:`, `fatal:`, `panic` 的核心错误堆栈。
- 运行针对性断言：例如代码修改后，自动运行静态语法检查 `python -m py_compile` 或 `gcc -fsyntax-only`，将确凿的机器验证结果转化为文字观察。

### Stage 6: 状态流转与 Reflexion 反思 (State Transition)
将清洗后的结构化观察回写进会话记忆：
- 若观察表明操作成功，推进子任务进度表。
- 若观察表明操作失败，要求模型在下一步思考中显式输出 **Reflexion（自愈反思）**：
  > “上一步失败的原因是什么？当前的假设错在哪里？下一步应当如何调整策略？”

---

## 4. 控制循环参考骨架实现：Python 核心状态机与进程安全守卫

> **定位说明**：本节代码为**教学与架构验证用的精简参考骨架（Reference Skeleton）**。它完整呈现了状态机流转、参数契约拦截（包括 `null` 与非对象保护）、超时参数归一化、可强制终止并清理的子进程执行方案，以及外部独立验收机制。在量产多租户或工业级研发环境中，底层命令需进一步置于 Docker 隔离容器、Firecracker MicroVM 或非阻塞受限 PTY 沙箱中执行。

```python
"""
Minimal Autonomous Agent Runtime Skeleton (可终止进程执行与契约校验参考实现)
Author: Yvain Zhang
Architecture: ReAct FSM + Context Budget + Schema Validation + Process Watchdog + External Verifier
Note: 用于系统架构验证与教学演示。在真实生产多租户环境中，需套接容器/微虚拟机沙箱。
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
    """负责上下文窗口预算管理、前缀缓存对齐与长历史有损压缩"""
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
    """强制清理子进程及其衍生的整棵进程树，防止任何忽略 SIGTERM 的后代进程逃逸"""
    pid = proc.pid
    if not pid:
        return

    parent_pgid = os.getpgrp()

    # 1. 尝试向 worker 建立的独立进程组发送 SIGTERM（优雅终止）
    # worker 启动时已执行 os.setsid()，其 PGID 等于 pid
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

    # 2. 关键修复：无论 worker 是否存活，必须无条件向该进程组强制下发 SIGKILL！
    # 彻底剿灭任何忽略 SIGTERM（如 trap '' TERM 或自定义信号处理器）的后代进程
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
    """强类型参数校验、独立进程组隔离、超时排空防死锁与受控沙箱分发器"""
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

        # 3. 真实可终止的进程执行方案：独立进程组隔离、超时排空防死锁与整组物理清理
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

        # 关键机制：在超时预算内先通过 poll 轮询管道数据，排空缓冲区，杜绝管道写满死锁导致的误判超时
        if not parent_conn.poll(clean_timeout):
            # 真正超时：物理终止并回收整棵进程树（包括 worker 及其衍生所有子进程）
            _kill_process_tree(proc)
            parent_conn.close()
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                output="",
                exit_code=124,
                error=f"工具执行超时 (超过 {clean_timeout} 秒)，整棵进程树已被强制终止并清理。"
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
        self.verifier = verifier  # 外部独立验收断言器（关键安全护栏：绝不盲目信任模型自报）
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

            # 3. 终结判断：必须经受外部独立断言器验收，拒绝模型虚假自报
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
                    # 验收未通过！将客观失败证据注入上下文，强迫模型分析并自愈纠偏
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

## 5. 总结与工程落地建议

1. **永远从一个最小的状态机开始**：不要试图一次性让 Agent 自治做所有事。先将任务范围限制在只读排查、测试运行或单文件修复等可验证闭环内。
2. **将单元测试当做 Agent 的“眼睛”**：只有当外部断言或编译器真正输出 exit 0 时，Agent 的任务才算成功。绝不轻信模型的自我汇报。
3. **在终端集成中善用 MCP 标准协议**：将工具拆解为独立的微服务，为团队沉淀可复用的底层基础设施。
