# FreeRTOS 架构哲学与源码拓扑

## 1. 架构设计哲学：极简调度微内核

与 Linux 或宏内核（Monolithic Kernel）不同，FreeRTOS 的核心定位是一个**不可分拆的高性能任务调度器库**。本文分析以官方长期维护版本 [FreeRTOS Kernel V10.5.1](https://github.com/FreeRTOS/FreeRTOS-Kernel/tree/V10.5.1) 为基准。
* **零额外硬件依赖**：只要硬件平台具备一个可递增的时钟中断和一个堆栈指针，只需编写数十行汇编即可跑起 FreeRTOS。
* **可裁剪性**：所有功能均通过静态编译宏 `FreeRTOSConfig.h` 控制，未使用的功能在编译链接阶段由死代码消除（Dead Code Elimination）移出固件，最小内核镜像仅需 **4KB~9KB Flash 与不到 1KB RAM**（参考 [官方二进制体积说明](https://www.freertos.org/Embedded-RTOS-Binary-Sizes.html)）。
* **严格代码规范**：遵循 MISRA-C 规范与官方 [FreeRTOS Coding Standard](https://www.freertos.org/FreeRTOS-Coding-Standard-and-Style-Guide.html)，全套源码采用特定的匈牙利命名法前缀，使变量作用域与数据类型在阅读时一目了然。

---

## 2. 源码树组织结构

官方源码树（[GitHub - FreeRTOS-Kernel V10.5.1](https://github.com/FreeRTOS/FreeRTOS-Kernel/tree/V10.5.1)）结构异常干净整洁：

```text
FreeRTOS-Kernel/
├── croutine.c           # [可选] 极小 RAM 协程实现（现极少使用）
├── event_groups.c       # 事件标志组
├── list.c               # 内核核心：双向循环链表实现
├── queue.c              # 内核核心：队列、信号量与互斥锁
├── stream_buffer.c      # 流式缓冲区与消息缓冲区
├── tasks.c              # 内核核心：任务管理与调度器
├── timers.c             # 软件定时器后台任务
├── include/             # 官方公共内核头文件
│   ├── FreeRTOS.h
│   ├── task.h
│   ├── queue.h
│   ├── semphr.h
│   └── list.h
└── portable/            # 硬件与编译器平台移植层
    ├── MemMang/         # 内存堆模型 (heap_1.c ~ heap_5.c)
    └── GCC/ARM_CM4F/    # 架构与编译器特定汇编 (port.c, portmacro.h)
```

---

## 3. 命名约定体系（Coding Standard）

| 前缀 | 变量 / 函数类型 | 示例 |
| :--- | :--- | :--- |
| `c` | `char` 类型 | `cTaskName` |
| `s` | `int16_t` (short) | `sCounter` |
| `l` | `int32_t` (long) | `lValue` |
| `u` | `unsigned` 无符号数 | `uxPriority`（无符号 BaseType） |
| `p` | 指针变量（Pointer） | `pxTopOfStack`、`pxCurrentTCB` |
| `x` | `BaseType_t` 或复合结构体句柄 | `xQueueCreate()`、`xTaskHandle` |
| `v` | `void` 返回值或空类型 | `vTaskDelay()`、`vTaskStartScheduler()` |
| `prv` | 私有静态函数（Private static） | `prvAddNewTaskToReadyList()` |

---

## 4. `FreeRTOSConfig.h` 裁决体系

所有内核行为均由此头文件在**预编译期**决定，没有任何运行期动态解析开销：

```c
/* 基础系统时钟与调度 */
#define configUSE_PREEMPTION                    1   /* 1: 抢占式调度, 0: 协作式调度 */
#define configCPU_CLOCK_HZ                      ( 168000000UL ) /* CPU 核心频率 */
#define configTICK_RATE_HZ                      ( ( TickType_t ) 1000 ) /* SysTick 节拍频率: 1ms */
#define configMAX_PRIORITIES                    ( 32 ) /* 任务优先级上限 (0 为最低空闲优先级) */
#define configMINIMAL_STACK_SIZE                ( ( uint16_t ) 128 ) /* 空闲任务栈大小 (字) */

/* 核心优化开关 */
#define configUSE_PORT_OPTIMISED_TASK_SELECTION 1   /* 开启硬件前导零指令 (CLZ) 优化调度器 */
#define configUSE_TICKLESS_IDLE                 0   /* 低功耗 Tickless 模式 */
#define configUSE_MUTEXES                       1   /* 编译互斥锁支持 (含优先级继承) */

/* 中断安全阈值配置 (Cortex-M 关键) */
#define configPRIO_BITS                         4   /* STM32 等平台使用 4 个优先级位 (0~15) */
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY         15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY    5   /* 优先级数值 <= 5 的中断禁止调用 FreeRTOS API! */
```
