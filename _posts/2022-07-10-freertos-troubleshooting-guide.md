---
layout: post
title: "FreeRTOS 常见故障排查指南"
subtitle: "中断优先级嵌套、Cortex-M 双栈模型 (MSP/PSP)、栈溢出检测与 Heap 选型"
date: 2022-07-10
redirect_from:
  - /2023/02/11/freertos-troubleshooting-guide/
author: Yvain Zhang
header-img: "img/post-bg-debug.png"
series: "技术"
tags:
  - 操作系统
  - FreeRTOS
  - 嵌入式
  - 故障排查
  - C语言
---

在嵌入式 MCU/SoC 上运行 FreeRTOS 时，偶发性崩溃和 HardFault 较为常见：
- 系统运行一段时间后偶发进入 HardFault；
- 增加任务或调用 `printf` 后系统出现异常；
- 触发中断后调度器出现死锁；
- 内存变量被异常改写。

排查 FreeRTOS 系统故障时，通常优先检查三大常见诱因：**中断优先级与临界区配置、任务栈空间分配、以及标准 C 库 `printf` 的使用方式**。

本文结合 FreeRTOS 内核机制，梳理排查思路与配置要点。

---

## 1. 中断优先级与 `configMAX_SYSCALL_INTERRUPT_PRIORITY`

中断优先级配置错误是导致 FreeRTOS 临界区失效与死锁的高频原因。

### 1.1 Basepri 寄存器与临界区保护机制
在 ARM Cortex-M 架构上，FreeRTOS 的内核临界区（`taskENTER_CRITICAL()`）通过向 **`BASEPRI` 寄存器** 写入 `configMAX_SYSCALL_INTERRUPT_PRIORITY`（部分端口命名为 `configMAX_API_CALL_INTERRUPT_PRIORITY`）实现中断屏蔽：
- **逻辑优先级低于或等于该阈值的中断**：被硬件临时屏蔽，确保内核数据结构操作的安全；
- **更高优先级（数值更小）的中断**：不会被屏蔽，享受极低的中断延迟（Zero Latency Interrupts）。

```
硬件最高优先级 (Priority 0)  ───┐
                               ├──> 不受 FreeRTOS 管理，严禁调用任何带 FromISR 的 API
                               │
configMAX_SYSCALL_PRIORITY ────┴── [BASEPRI 临界区屏蔽边界]
                               │
                               ├──> 允许调用带 x...FromISR 后缀的 FreeRTOS API
硬件最低优先级 (Priority 15) ───┘
```

> **核心规则**：**凡是调用了 FreeRTOS API（如 `xQueueSendFromISR`）的中断，其硬件优先级数值必须大于或等于 `configMAX_SYSCALL_INTERRUPT_PRIORITY`**。

### 1.2 Cortex-M 优先级的配置注意项
1. **反向数值逻辑**：Cortex-M 架构中，**数值越小，逻辑优先级越高**（0 为最高优先级）；
2. **高位对齐**：Cortex-M 的优先级寄存器仅使用高几位（例如 4-bit 优先级使用 bit[7:4]）。直接写寄存器与调用 CMSIS 接口 `NVIC_SetPriority`（内部会自动左移）存在差异，需注意库函数的输入参数定义。

---

## 2. 任务栈溢出与 Cortex-M 双栈机制 (MSP / PSP)

### 2.1 Cortex-M 双堆栈指针架构
在 ARM Cortex-M 架构下，FreeRTOS 采用了**主堆栈指针（MSP）与进程堆栈指针（PSP）**分离的双栈机制：
- **`PSP` (Process Stack Pointer)**：任务在线程模式（Thread Mode）下执行代码时使用，每个任务拥有独立的 PSP 栈空间（在 `xTaskCreate` 时分配）；
- **`MSP` (Main Stack Pointer)**：系统启动阶段以及**所有中断和异常处理函数（Handler Mode）**统一使用 MSP 栈空间。

> **关于中断嵌套与任务栈的关系**：
> 在 Cortex-M 上，发生中断或中断嵌套时，硬件会自动切换到 **MSP（系统中断栈）** 运行，中断执行期间的栈消耗不会直接占用当前被抢占任务的 PSP 栈。
> 任务 private 栈溢出通常是由**局部数组过大、函数调用过深、递归调用或任务切换时的上下文寄存器保存**引起的。

---

### 2.2 栈高水位监控 API
通过 `uxTaskGetStackHighWaterMark()` 查询任务历史运行中**剩余栈空间的最小值**：

```c
// 返回值表示历史运行中距离栈底剩余的最小字数 (Words)，越接近 0 说明栈越紧张
UBaseType_t hwm = uxTaskGetStackHighWaterMark(NULL);
```

### 2.3 内核运行时栈检查 (`configCHECK_FOR_STACK_OVERFLOW`)

在 `FreeRTOSConfig.h` 中配置宏：

```c
#define configCHECK_FOR_STACK_OVERFLOW  2
```

1. **方法 1 (`=1`)**：在每次任务切出时，检查 SP 指针是否超出栈有效边界；
2. **方法 2 (`=2`)**：创建任务时用已知模式（如 `0xA5`）填充栈内存。任务切出时检查**栈底最后 20 字节的金丝雀模式（Canary Pattern）是否被破坏**。

#### 溢出钩子函数实现

```c
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName) {
    // 捕获栈溢出事件
    taskDISABLE_INTERRUPTS();
    for (;;);
}
```

---

## 3. 标准库 `printf()` 的潜在风险

在多任务环境中使用标准 libc 的 `printf` / `sprintf` 需要注意：
1. **非线程安全**：标准 C 库的部分格式化实现可能包含静态缓冲区或全局状态，多任务并发调用时可能引发竞争；
2. **栈开销较大**：处理浮点数和长格式化字符串时，局部变量栈深度可能达到数百字节，容易导致小容量任务栈溢出；
3. **隐式动态分配**：部分 libc 会在初次格式化时调用底层 `malloc` 分配 I/O 缓冲区。

> **建议**：在嵌入式环境中，推荐使用轻量级、无动态分配的专用实现（如 `mpaland/printf`）或硬件调试打印通道。

---

## 4. 内存管理方案 (heap_1 ~ heap_5) 选型参考

| 方案 | 分配特点 | 释放支持 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **heap_1** | 仅递增指针，代码体积小 | 不支持释放 | 任务与队列一次性静态分配且不销毁的系统 |
| **heap_2** | 最佳匹配算法（Best-Fit） | 支持释放（不合并相邻空闲块） | 频繁申请/释放相同尺寸对象的场景 |
| **heap_3** | 封装标准 C 库的 `malloc` / `free` | 支持释放 | 依赖编译器自带堆管理器的环境 |
| **heap_4** | 首次适应算法（First-Fit）+ **合并相邻空闲块** | 支持释放 | 通用嵌入式应用首选 |
| **heap_5** | 机制同 heap_4，**支持跨越非连续物理内存区域** | 支持释放 | 内部 SRAM 与外部 SDRAM/PSRAM 混合内存系统 |

---

## 5. 开发建议：启用 `configASSERT()`

在开发与调试阶段，建议在 `FreeRTOSConfig.h` 中定义 `configASSERT`：

```c
#define configASSERT(x) if ((x) == 0) { taskDISABLE_INTERRUPTS(); for(;;); }
```

内核中的许多前置条件校验（包括中断优先级范围检查）都会在异常发生的第一时间触发断言，便于通过调试器快速定位调用栈。
