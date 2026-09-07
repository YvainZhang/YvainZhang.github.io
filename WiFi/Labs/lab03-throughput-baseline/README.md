# 实验 03：iperf3 性能基线测试与系统级瓶颈分析

## 实验目标

建立科学、可重复的 Wi-Fi 吞吐量基线测试流程。学习如何区分**物理层速率 (PHY Rate)** 与**应用有效吞吐 (Goodput)**，掌握测试期间 CPU 软中断、空口重传率、RTT 时延抖动与协议栈瓶颈的联合观测方法。

## 测试环境与原则

1. **拓扑准备**：
   - AP 与 iperf3 Server 通过千兆/2.5G 有线网线直连，避免回程有线瓶颈。
   - STA 通过被测 Wi-Fi 连接 AP，固定在 5GHz 干净信道（如 Channel 149 80MHz），测试距离 2~3 米，无大功率干扰源。
2. **CPU 调频模式固定**：
   测试前务必将测试机与服务端的 CPU Governor 置为高性能模式，避免频率动态升降造成抖动：
   ```bash
   sudo cpupower frequency-set -g performance 2>/dev/null || true
   ```
3. **警惕 USB 降级**：
   若使用 USB 3.0 无线网卡，先用 `lsusb -t` 确认处于 `5000M` 模式，防止插在 USB 2.0 口上被硬性限速在 ~300 Mbps。

## 理论吞吐上限测算 (基于 Airtime 预算模型)

绝不能使用 `PHY rate × 75%` 这种静态估算公式，因为不同聚合度、包长和信道质量下的协议开销占比截然不同。

按照 [从 PHY Rate 到 Goodput 的性能预算](../../07-Performance/03-throughput-budget-model.md) 的空口时间模型：

```text
T_burst = T_AIFS + E[backoff] + T_preamble + T_AMPDU + T_SIFS + T_BA
```

以 Wi-Fi 6 (802.11ax) 2x2 MIMO 80MHz 频宽、MCS 11（理论物理速率 1201.0 Mbps）、单用户干净信道为例进行推演：
1. **假设硬件达到大聚合**：一次 A-MPDU 聚合 64 个以太网帧（约 96 KB 数据），净荷空口发射时长 `T_AMPDU ≈ (96000 × 8) / 1201 ≈ 640 μs`。
2. **固定空口竞争与确认开销**：AIFS (34 μs) + 平均退避 (67.5 μs) + 前导码/信令 (~40 μs) + SIFS (16 μs) + BlockAck (~32 μs) ≈ 190 μs。
3. **空口发射效率上限**：`640 / (640 + 190) ≈ 77%`。
4. **叠加上层开销**：扣除以太网/IP/TCP 头部封装开销（约 2%~3%）及 TCP 反向 ACK 竞争时间后，理论应用层 Goodput 上限约为 **850 ~ 900 Mbps**。

若固件聚合能力不足（例如每个 A-MPDU 仅能聚合 8 帧），净荷发射时间骤降至 80 μs，而协议开销依然是 190 μs，此时空口效率将暴跌至不足 30%（吞吐上限跌至 300 Mbps 以下）。

## 自动化基线测试脚本

保存以下脚本为 `wifi_benchmark.sh` 并执行。注意：**测试带载时延时，Ping 必须与吞吐压测并发运行**，否则测出的只是空闲网络下的假时延。

```bash
#!/bin/bash
SERVER_IP="192.168.1.100"
IFNAME="wlan0"

echo "=== 1. 链路握手信息 ==="
iw dev $IFNAME link

echo "=== 2. TCP TX (上行吞吐测试 20s) ==="
iperf3 -c $SERVER_IP -t 20 -i 5 --json > /tmp/iperf_tx.json
TX_SPEED=$(jq '.end.sum_received.bits_per_second / 1000000' /tmp/iperf_tx.json)
echo "TCP TX Goodput: $TX_SPEED Mbps"

echo "=== 3. TCP RX (下行吞吐测试 20s) ==="
iperf3 -c $SERVER_IP -R -t 20 -i 5 --json > /tmp/iperf_rx.json
RX_SPEED=$(jq '.end.sum_received.bits_per_second / 1000000' /tmp/iperf_rx.json)
echo "TCP RX Goodput: $RX_SPEED Mbps"

echo "=== 4. UDP 丢包与抖动测试 (发包 100Mbps 20s) ==="
iperf3 -c $SERVER_IP -u -b 100M -t 20 -i 5 --json > /tmp/iperf_udp.json
UDP_LOSS=$(jq '.end.sum.lost_percent' /tmp/iperf_udp.json)
UDP_JITTER=$(jq '.end.sum.jitter_ms' /tmp/iperf_udp.json)
echo "UDP Loss: $UDP_LOSS %, Jitter: $UDP_JITTER ms"

echo "=== 5. 真带载时延测试 (TCP 吞吐高压下并发测量 RTT p50 / p99) ==="
# 1. 后台启动高频 Ping 探测
ping -i 0.05 $SERVER_IP > /tmp/ping_loaded.log &
PING_PID=$!

# 2. 并发启动 10 秒满载 TCP 压测 (打满发送/接收队列)
iperf3 -c $SERVER_IP -t 10 > /dev/null

# 3. 压测结束，立即终止 Ping
kill $PING_PID 2>/dev/null || true

# 4. 从日志中提取 RTT 并计算 p50 与 p99 分位数
awk -F'time=' '/time=/ {print $2}' /tmp/ping_loaded.log | awk '{print $1}' | sort -n | awk '
  BEGIN { c = 0; }
  { rtt[c++] = $1; }
  END {
    if (c > 0) {
      p50 = rtt[int(c * 0.50)];
      p99 = rtt[int(c * 0.99)];
      printf "Loaded Ping 样本数: %d, p50: %.2f ms, p99: %.2f ms\n", c, p50, p99;
    } else {
      print "未能收集到有效 RTT 数据";
    }
  }'
```

## 测试过程同步观测维度

在一个独立终端窗口运行实时监控：
```bash
# 每秒刷新网卡收发包数、丢包数与软中断
watch -n 1 "
echo '--- Network Errors & Drops ---'
ip -s link show $IFNAME | grep -E 'RX:|TX:|errors|dropped'
echo '--- SoftIRQs (NET_RX / NET_TX) ---'
grep -E 'NET_RX|NET_TX' /proc/softirqs
"
```

## 基线数据记录表范例模板

| 测试项目 | 记录 Goodput (Mbps) | 协商 PHY Rate | 丢包/重传率 | RTT p50 / p99 | CPU 瓶颈判定 |
|---|---:|---:|---:|---:|---|
| **单流 TCP TX** | ~850 | 1201 Mbps (MCS 11) | Retry 2.1% | 2.3ms / 5.1ms | CPU0 42% (健康) |
| **单流 TCP RX** | ~860 | 1201 Mbps (MCS 11) | 0% | 2.1ms / 4.8ms | CPU0 38% (健康) |
| **多流并发 TCP (4流)** | ~890 | 1201 Mbps (MCS 11) | Retry 3.5% | 4.2ms / 11.5ms| 软中断均衡分布于多核 |
| **UDP 100M (下行)** | 100 | 1201 Mbps | Loss 0.0% | Jitter 0.2ms | 几乎无负荷 |
| **重载下 Ping 延迟** | 吞吐 850M 下 | - | - | 14.2ms / 42.8ms | 排查 BQL / 驱动队列缓存积压 |

> **数据性质说明**：上表记录均为模板示例数据（用于展示基线报告格式与判定标准）。真实实验应以目标环境实测日志为准，并完整记录测试硬件型号、内核版本与驱动 commit。

## 常见四大性能陷阱

1. **测试服务端性能不足**：服务端运行在树莓派或低功耗主机上，自身 CPU 跑满导致测试瓶颈。
2. **TCP 窗口过小**：Linux 默认 `tcp_rmem` 或 `tcp_wmem` 限制，导致长肥管道（BDP）吞吐打不满。
3. **严重信道拥塞**：周边存在大量同信道或邻信道 AP，导致 CCA 物理侦听频繁退避，Airtime 被瓜分。
4. **缓冲膨胀 (Bufferbloat)**：高吞吐时 Ping 延迟飙升到几百毫秒，表明驱动层或 qdisc 队列无限制积压，需调优 BQL (Byte Queue Limits) 或 fq_codel。

