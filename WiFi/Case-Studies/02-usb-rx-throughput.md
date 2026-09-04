# 案例：USB RX 吞吐瓶颈

## 现象

下行 TCP 吞吐明显低于上行，PHY Rate 与 RSSI 正常，增加 iperf 并发流改善有限；某个 CPU 的 softirq 使用率较高。

## 假设树

```text
Air RX不足？
├─ 是：干扰、重试、速率、AP 调度
└─ 否：Device→USB 供给不足？
   ├─ 是：Firmware 聚合、endpoint、device queue
   └─ 否：Host 消费不足？
      ├─ URB inflight / completion latency
      ├─ parse/copy/NAPI
      └─ softirq affinity / protocol stack
```

## 最小证据

- MAC 收包字节和空口重试统计；
- Device 侧聚合大小分布与待发送队列；
- RX URB 预提交数量、完成长度和完成间隔；
- Driver RX enqueue/drop、NAPI budget 使用；
- 各 CPU IRQ/softirq、热点和跨核迁移；
- netdev 与应用 Goodput。

## 定位示例

若 MAC 收包稳定，而 RX URB inflight 周期性变为零，USB Endpoint 会等待 Host 重新提交 buffer。此时提高 Firmware 聚合上限可能没有帮助；应缩短 Host 解析路径、提前补充 URB 或将耗时工作移出 completion context。

## 验证

一次只改变 URB 深度、聚合阈值或 CPU affinity 中的一项。除了吞吐，还比较 RTT p99、CPU、内存 high-watermark、错误率与长稳。相关完整背景见 [Wi-Fi USB 驱动架构与多核性能调优](/2025/07/13/wifi-usb-driver-performance-tuning/)。
