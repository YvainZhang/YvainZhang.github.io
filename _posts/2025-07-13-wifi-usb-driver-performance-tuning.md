---
layout: post
title: "Wi-Fi USB 驱动架构与多核性能调优"
subtitle: "收发路径、URB 管理与 CPU 负载分配"
date: 2025-07-13
redirect_from:
  - /2024/07/16/wifi-usb-driver-performance-tuning/
author: Yvain Zhang
header-img: "img/post-bg-debug.png"
series: "技术"
tags:
  - Wi-Fi
  - 驱动开发
  - 嵌入式
  - Linux
  - 性能优化
---

嵌入式 Linux 设备常通过 USB 接入 Wi-Fi 芯片。无线链路速率较高时，主控 CPU、USB 总线和驱动处理都可能限制实测吞吐，不能只看物理层速率。

网络协议栈、USB 中断和驱动线程集中在同一个核心上时，可能出现一个核心忙、其他核心空闲的情况。这时可以检查中断亲和性和网络分流配置，再判断是否需要调整。

下面用一种 USB Wi-Fi 驱动模型说明收发路径和四核分工。线程名、CPU 分配和预期负载均为示例，实际使用时需按驱动实现、SoC 拓扑和测量结果调整。

---

## 1. Wi-Fi USB 驱动收发数据流模型

可以分别沿发送路径（TX Path）和接收路径（RX Path）查看数据经过的队列、线程和回调。

```
[ 发送链路 (TX Path) ]
应用数据 / 转发数据
       │
       ▼
Linux 协议栈 / 桥接转发 (ndo_start_xmit)
       │ (将 skb 放入驱动待发环形缓冲区)
       ▼
驱动待发队列: <tx_pending_queue>
       │ (唤醒驱动专用发送线程 / Workqueue)
       ▼
驱动发送工作线程: <driver_tx_thread>
  ├── 1. 锁存并出队待发 sk_buff
  ├── 2. 执行 A-MSDU 软件报文聚合
  ├── 3. 填充硬件 TX 描述符 (TX Descriptor)
  └── 4. 组装 USB URB，调用 usb_submit_urb() 提交给 USB Core
       │
       ▼
USB 主控驱动 (xHCI / EHCI DMA 发送至芯片)
```

```
[ 接收链路 (RX Path) ]
芯片通过 USB 批量端点上报数据
       │
       ▼
USB 主机控制器硬件触发中断 (Hard IRQ)
       │ (调度 USB 完成软中断 / Tasklet)
       ▼
USB 完成回调函数: <rx_complete_callback>()
  ├── 1. 从 RX URB 池取出已完成的 URB
  ├── 2. 剥离芯片私有 RX 描述符
  ├── 3. 解聚合 A-MSDU / A-MPDU，组装为标准 sk_buff
  └── 4. 调用 napi_gro_receive() 或 netif_receive_skb() 递交协议栈
       │
       ▼
重新提交新的空闲 URB (usb_submit_urb) 保持接收窗口
```

---

## 2. 驱动中的缓冲与工作线程
{: id="2-驱动内部四大核心数据对象"}

1. **接收 URB 环**：
   - 驱动初始化时预分配的一组 `struct urb` 及其对应 DMA 内存，具体深度由吞吐、延迟和可用内存共同决定；
   - 驱动时刻保证有足够数量的 URB 挂在 USB 主控底层，防止芯片有数据上报时因 Host 端无空闲 URB 导致硬件 FIFO 溢出。
2. **待发包缓冲环**：
   - 介于协议栈 `ndo_start_xmit` 与驱动发送线程之间的 FIFO 环形队列；
   - 用于解耦网络层发包与 USB 物理总线提交，提供流量突发时的吸收缓冲。
3. **发送 URB 环**：
   - 驱动用于承载实际 USB 批量传输请求的 URB 对象池；
   - 发送完成后在 TX Complete 回调中释放 skb 并回收 URB，供下一轮复用。
4. **驱动发送引擎线程**：
   - 专职负责出队、硬件描述符封装、软件聚合与 URB 下发的内核工作线程。

---

## 3. 多核 SMP 亲和性（Affinity）分核策略

在典型四核 ARM 平台上，若中断路由与网络分流未做针对性配置，网卡和 USB 相关处理可能集中在同一核心，使该核心的软中断负载接近饱和并成为瓶颈。

### 3.1 四核流水线分工模型

```
   ┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
   │     CPU 0     │     │     CPU 1     │     │     CPU 2     │     │     CPU 3     │
   ├───────────────┤     ├───────────────┤     ├───────────────┤     ├───────────────┤
   │ * 以太网中断   │     │ * RPS 协议栈   │     │ * USB 主控中断│     │ * 驱动发送线程│
   │   (eth0 IRQ)  │───> │   软中断处理  │───> │   (xhci IRQ)  │     │ * TX Worker   │
   │ * 数据入站网关│     │   (NET_RX)    │     │ * RX Complete │     │ * A-MSDU 聚合 │
   └───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
```

- **CPU 0（以太网入口）**：处理以太网入口的硬件中断与 NAPI 轮询；
- **CPU 1（协议栈分流）**：通过 Linux 内核 RPS（Receive Packet Steering）机制，将以太网接收后的 TCP/IP 协议栈计算分流到 CPU 1，卸载 CPU 0；
- **CPU 2（USB 处理）**：处理 USB 主控中断及相应接收工作，具体回调上下文由实现决定；
- **CPU 3（发送线程）**：运行驱动的发送工作线程，处理内存拷贝与聚合组包。

---

### 3.2 实际调优配置示例

在 Linux 环境下，可以通过 sysfs 与 procfs 配置中断与协议栈分流：

```bash
#!/bin/sh
# Wi-Fi USB SMP Affinity & RPS Configuration Example

ETH_IF="eth0"
WLAN_IF="wlan0"

# 1. 查找硬件中断号
ETH_IRQ=$(grep "$ETH_IF" /proc/interrupts | head -n 1 | awk '{print $1}' | tr -d ':')
USB_IRQ=$(grep -E "(xhci|ehci)" /proc/interrupts | head -n 1 | awk '{print $1}' | tr -d ':')

# 2. 绑定硬件中断亲和性
# 以太网中断 -> CPU 0 (Affinity Mask 0x1)
[ -n "$ETH_IRQ" ] && echo 1 > /proc/irq/$ETH_IRQ/smp_affinity

# USB 主控中断 -> CPU 2 (Affinity Mask 0x4)
[ -n "$USB_IRQ" ] && echo 4 > /proc/irq/$USB_IRQ/smp_affinity

# 3. 启用 RPS 协议栈软中断分流
# 将以太网入站流量的协议栈处理推给 CPU 1 (Mask 0x2)
if [ -d "/sys/class/net/$ETH_IF/queues/rx-0" ]; then
    echo 2 > /sys/class/net/$ETH_IF/queues/rx-0/rps_cpus
fi

# 4. 绑定驱动发送工作线程（若驱动提供独立 kthread）
# 请替换为目标驱动中可从 ps/top 观察到的实际线程名
TX_THREAD_PATTERN="<driver-specific-kthread-name>"
TX_PID=$(pgrep -f "$TX_THREAD_PATTERN" | head -n 1)
if [ -n "$TX_PID" ]; then
    taskset -p 8 "$TX_PID" # 绑定 CPU 3 (Mask 0x8)
fi

echo "SMP affinity configuration complete."
```

---

## 4. 如何判断调整是否有效
{: id="4-调优效果与瓶颈诊断"}

### 4.1 调整前记录负载
{: id="41-初始未调优时的瓶颈现象"}
使用 `iperf3 -c <target> -P 4` 进行 TCP 吞吐测试，同时记录各核心负载、中断计数和吞吐。如果 CPU 0 的软中断负载（`%si`）接近饱和，而其他核心负载较低，可以进一步检查处理是否过于集中。单核满载只是一个线索，还需要确认 USB 总线、无线重传和发送队列是否也存在瓶颈。

### 4.2 调整后重复同一测试
{: id="42-调优后的负载分布"}
每次修改一项配置，再用相同的流量、方向和连接条件重复测试。上面的分工希望把入口收包、协议栈、USB 处理和发送线程分散，但并不保证吞吐提升。跨核传递和缓存访问也会带来开销，应结合吞吐、时延、丢包和各核心负载判断是否保留配置。

---

## 5. 总结

绑核是处理负载集中问题的一种手段。先确定时间主要花在哪条路径，再选择中断亲和性、RPS 或线程分配；如果负载已均衡，继续拆分反而可能增加开销。最终配置应以目标平台上的重复测试为依据。
