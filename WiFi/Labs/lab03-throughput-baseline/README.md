# 实验 03：iperf3 吞吐基线

## 目标

建立一份可重复的 Wi-Fi 性能基线，并学习区分应用 Goodput、PHY Rate、重试、CPU 与时延。

## 固定条件

记录频段、带宽、信道、距离、RSSI、AP/STA、Driver/Firmware、CPU governor 和背景流量。测试期间不要自动漫游或切换信道。

## 测试矩阵

服务端：

```bash
iperf3 -s
```

客户端依次测试：

```bash
iperf3 -c SERVER_IP -t 30
iperf3 -c SERVER_IP -R -t 30
iperf3 -c SERVER_IP -P 4 -t 30
iperf3 -c SERVER_IP -u -b 50M -t 30
ping -i 0.2 SERVER_IP
```

根据链路能力调整 UDP 目标速率，避免一开始就用远超容量的值。

## 同步观测

```bash
iw dev IFNAME link
ip -s link show IFNAME
grep -E 'NET_RX|NET_TX' /proc/softirqs
```

有条件时增加 `ethtool -S`、Driver 统计和 `perf top`。每种场景运行至少三轮，保留中位数与波动。

## 输出表

| 方向/协议 | Goodput | RTT p50/p99 | PHY | Retry | CPU | 备注 |
|---|---:|---:|---:|---:|---:|---|
| TX TCP |  |  |  |  |  |  |
| RX TCP |  |  |  |  |  |  |
| TX UDP |  |  |  |  |  |  |

改变一个聚合、队列或 affinity 参数后完整重跑，防止把环境波动误认为优化收益。
