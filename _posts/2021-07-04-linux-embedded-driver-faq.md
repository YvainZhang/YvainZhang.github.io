---
layout: post
title: "Linux 嵌入式驱动开发基础与常见问题"
subtitle: "从字符设备注册、Platform 总线匹配、中断锁选型到 ioremap 与 Oops 调试"
date: 2021-07-04
redirect_from:
  - /2022/06/28/linux-embedded-driver-faq/
author: Yvain Zhang
header-img: "img/post-bg-unix-linux.jpg"
series: "技术"
tags:
  - 操作系统
  - 嵌入式
  - Linux
  - 驱动开发
  - C语言
---

在嵌入式 Linux 驱动开发与底层调试中，常遇到以下基础机制问题：
- 字符设备注册后，`/dev` 目录下如何生成设备节点；
- 在驱动中操作硬件寄存器为何需要执行 `ioremap()`；
- 中断服务例程（ISR）与普通进程共享数据时自旋锁的选型；
- 发生内核 Oops 调用栈时如何定位对应的 C 代码行号。

本文梳理 Linux 字符设备模型、同步机制、I/O 内存映射与驱动调试方法。

---

## 1. 字符设备注册与 `/dev/` 节点创建

Linux 驱动中，动态创建 `/dev/my_dev` 设备节点的过程如下：

```mermaid
graph LR
    Step1[1. alloc_chrdev_region: 申请主次设备号] --> Step2[2. cdev_init & cdev_add: 绑定 file_operations 注册 cdev]
    Step2 --> Step3[3. class_create: 在 /sys/class 创建设备类]
    Step3 --> Step4[4. device_create: 向 sysfs 注册设备并发送 uevent]
    Step4 --> Step5[5. udev / mdev 接收 uevent 自动在 /dev 创建节点]
```

- **`mknod` 与 `udev/mdev` 的关系**：
  - `mknod /dev/my_dev c <major> <minor>` 为手动创建设备节点的方式；
  - `device_create()` 会在 `/sys/class/<class_name>/` 下生成设备属性并向用户态广播 `uevent`，系统中的 `mdev`（BusyBox）或 `udev` 守护进程捕获事件后，在用户空间自动创建 `/dev/my_dev` 节点。

---

## 2. Linux 设备驱动模型：Platform 平台总线匹配

对于集成在 SoC 内部的独立控制器（如片上 UART、I2C、GPIO 控制器），由于缺少物理总线的硬件枚举能力，Linux 抽象出虚拟的 **`platform_bus_type`（平台总线）** 进行设备与驱动的绑定：

```
[ Device Tree 设备树 .dts ]          [ Platform 驱动 .c (platform_driver) ]
  compatible = "vendor,my-sensor";       .of_match_table = { { .compatible = "vendor,my-sensor" } }
           │                                          │
           └───────────────────┬──────────────────────┘
                               ▼
        [ platform_bus_type 匹配引擎 ]
                               │
                 字符串一致 -> 匹配成功
                               ▼
        调用 driver 的 .probe(struct platform_device *pdev)
```

- **常见匹配方式**：
  1. **设备树匹配（OF Table）**：比对 `of_match_table` 中的 `compatible` 字符串（主流方式）；
  2. **ID 表匹配**：比对 `platform_device_id` 数组；
  3. **名称匹配**：直接比对 `driver.name` 与 `device.name`。

---

## 3. 驱动同步原语与锁选型

| 同步机制 | 核心原理 | 中断上下文可用性 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **`atomic_t`** | 基于硬件指令（如 ARM `LDREX/STREX`） | 支持 | 简单的整数计数与状态标志位。 |
| **`spinlock_t`** | 忙等待自旋，不让出 CPU | 支持（需注意关抢占/中断） | 极短时间（微秒级）的临界区保护。 |
| **`mutex`** | 阻塞睡眠，让出 CPU | 不支持 | 涉及 I/O 操作、内存申请等耗时较长的临界区。 |
| **`spin_lock_irqsave`** | 自旋锁 + 保存中断状态并关本地中断 | 支持 | **共享数据同时被进程上下文与硬件 ISR 访问时使用**（避免中断打断进程持锁导致死锁）。 |

---

## 4. 硬件寄存器地址映射：`ioremap` 的作用

```
物理内存总线 (Physical Address) ──[ 硬件 MMU (禁止直接物理寻址) ]──> 虚拟地址 (Kernel Virtual Address)
                                                ▲
                                                │
                                  ioremap(phys_addr, size) 建立页表映射
```

- **原因**：启用 MMU 后，CPU 执行的所有指针解引用操作都会被当作虚拟地址处理；
- **作用**：若直接向 `0x01C20800`（物理 GPIO 地址）写入，会因页表无该映射而触发异常。需通过 `ioremap()` 为该段物理 I/O 地址分配内核虚拟地址并建立页表映射，再通过 `readl()` / `writel()` 进行读写访问。

---

## 5. 驱动调试：分析内核 Oops 调用栈

当驱动发生空指针或非法内存访问时，内核会打印 Oops 诊断信息：

```
[  12.345678] Unable to handle kernel NULL pointer dereference at virtual address 00000010
[  12.345680] Internal error: Oops: 80000005 [#1] PREEMPT SMP ARM
[  12.345700] PC is at my_driver_write+0x24/0x80 [my_driver]
[  12.345710] LR is at vfs_write+0xb8/0x1c8
[  12.345720] Call trace:
[  12.345730]  my_driver_write+0x24/0x80 [my_driver]
[  12.345740]  vfs_write+0xb8/0x1c8
[  12.345750]  ksys_write+0x58/0xd0
```

### 定位崩溃源码行号的方法

#### 方式 A（推荐）：使用内核自带的 `scripts/faddr2line`
内核源码树提供了专用脚本，可直接解析 `function+offset/size` 格式：

```bash
# 语法：./scripts/faddr2line <带调试信息的.ko或vmlinux> <函数名+偏移/函数大小>
./scripts/faddr2line my_driver.ko my_driver_write+0x24/0x80

# 输出定位结果：
# my_driver_write+0x24/0x80:
# my_driver_write at /home/user/project/drivers/my_driver.c:142
```

#### 方式 B：使用 `nm` 获取基址并传给 `addr2line`
GNU `addr2line` 需要十六进制数值地址，可通过符号表计算：

```bash
# 1. 查找函数符号的起始基址
FUNC_ADDR=$(nm my_driver.ko | grep "T my_driver_write" | awk '{print "0x"$1}')

# 2. 加上崩溃偏移量 0x24
TARGET_ADDR=$(printf "0x%x" $((FUNC_ADDR + 0x24)))

# 3. 传给 addr2line 转换行号
arm-linux-gnueabihf-addr2line -e my_driver.ko $TARGET_ADDR
# 输出：/home/user/project/drivers/my_driver.c:142
```

---

## 6. 总结

1. **设备模型**：Platform 总线用于解耦板级硬件描述（Device Tree）与驱动实现代码；
2. **内核边界**：用户空间与内核空间传递数据使用 `copy_to_user()` / `copy_from_user()`，物理寄存器访问需经过 `ioremap()` 映射；
3. **并发保护**：进程与 ISR 共享数据采用 `spin_lock_irqsave()` 避免中断重入竞争。
