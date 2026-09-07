# 实验 04：Linux Wi-Fi 低功耗、Runtime PM 与 WoWLAN 唤醒观测

## 实验目标

观测 Linux 系统下 Wi-Fi 芯片在空闲时的 **Runtime PM 自动休眠**、整机 **System Suspend/Resume** 过程，掌握 **WoWLAN (Wake on Wireless LAN)** 的配置与抓取唤醒源（Wakeup Source）的调试技能，建立完整的低功耗时序证据链。

## 核心接口与概念

- **Runtime PM**：当网卡在一段时间内无流量进出时，内核驱动将其总线切换至低功耗状态（如 PCIe D3Hot 或 USB Suspend），有流量时通过中断自动拉回 D0。
- **WoWLAN**：主机处于系统深度休眠（S3/Suspend-to-RAM）时，Wi-Fi 芯片由固件代为维持 802.11 心跳，仅当捕获到特定空口模式（Magic Packet、断链重连、或特定 TCP SYN）时拉高 GPIO/PME 中断唤醒主 CPU。

!!! warning "安全与环境边界提醒"
    触发系统待机（System Suspend）或修改 Runtime PM 参数会导致总线挂起与网卡掉电，正在运行的 SSH 远程连接、未保存的工程文件或网络下载会被直接中断。**请仅在具备本地显示器与物理键盘/电源按键的实验机或专用虚拟机中操作**，切勿在承载远程会话的云主机或生产环境中运行休眠命令。

## 步骤 1：查询与配置 WoWLAN 唤醒触发器

```bash
# 1. 查看物理网卡支持的 WoWLAN 触发条件
iw phy phy0 wowlan show

# 2. 启用 Magic Packet (幻数据包) 与断链唤醒 (Disconnect)
sudo iw phy phy0 wowlan enable magic-packet disconnect

# 3. 验证配置是否生效
iw phy phy0 wowlan show
```
预期输出：
```text
WoWLAN is enabled:
 * wake up on magic packet
 * wake up on disconnect
```

## 步骤 2：检查设备的 Runtime PM 状态

定位 Wi-Fi 网卡在 sysfs 中的电源控制节点（以 PCIe 网卡为例）：
```bash
# 查找网卡对应的 PCI 设备路径
PCI_DEV=$(basename $(readlink /sys/class/net/wlan0/device))
cd /sys/bus/pci/devices/$PCI_DEV/power

# 查看当前电源模式 (auto 代表允许运行时省电，on 代表强制常开)
cat control

# 查看当前运行态状态 (active / suspending / suspended)
cat runtime_status

# 查看进入休眠的空闲时间阈值 (毫秒)
cat autosuspend_delay_ms
```

## 步骤 3：使用 trace-cmd 捕获休眠唤醒事件流

在终端 1 中启动 ftrace 电源事件监听（监听电源状态、软硬件中断与工作队列）：
```bash
sudo trace-cmd record -e "power:*" -e "irq:*" -e "net:net_dev_xmit" -e "net:netif_receive_skb" sleep 15
```

在此期间，触发一次 5 秒的短时间系统待机：
```bash
# 另开终端让系统休眠 5 秒后由 RTC 定时器自动唤醒
sudo rtcwake -m mem -s 5
```

待 trace 结束后解析事件时间戳报告：
```bash
sudo trace-cmd report > /tmp/power_trace.txt
head -n 30 /tmp/power_trace.txt
```

## 步骤 4：验证 WoWLAN 真实唤醒（从局域网另一台主机触发）

1. 让测试机进入深度休眠：
   ```bash
   sudo systemctl suspend
   ```
2. 在局域网内的另一台电脑（或手机）上，通过以太网向被测机 Wi-Fi MAC 地址发送唤醒魔术包：
   ```bash
   wakeonlan <STA_WIFI_MAC_ADDRESS>
   ```
3. 观察测试机是否成功被点亮唤醒。

## 步骤 5：唤醒源与内核日志对账

测试机唤醒后，第一时间检查内核唤醒源统计：
```bash
# 1. 查看最近一次唤醒系统的硬件来源
sudo cat /sys/kernel/debug/wakeup_sources | grep -E 'wlan|wifi|pci'

# 2. 查看 dmesg 中休眠与唤醒的毫秒耗时
dmesg | grep -E 'PM: suspend|PM: resume|wowlan'
```
预期关键日志：
```text
[  45.102314] PM: suspend entry (deep)
[  45.145021] wifi_driver: WoWLAN armed, firmware sleep mode active
[  52.890124] PM: early resume of devices complete after 2.451 msecs
[  52.891040] wifi_driver: wake reason: MAGIC_PACKET_RECEIVED
[  52.895120] wifi_driver: netif_wake_queue called, all queues active
```

## 常见异常排查提示

1. **休眠后网卡被完全掉电，无法被唤醒**：检查主板 BIOS/UEFI 设置中的 `PCIe PME / Wake on LAN` 是否被 Disable，或者 USB 口在休眠后是否被 5V 断电。
2. **休眠瞬间被秒唤醒 (Spurious Wakeup)**：空口广播中存在异常的组播流量触发了条件，或 DTIM 未做组播过滤，可通过 `iw phy phy0 wowlan enable magic-packet` 单独限制仅由单播 Magic Packet 唤醒。
3. **唤醒后网络不可用**：参考 [案例 04：休眠唤醒后断流](../../Case-Studies/04-resume-no-traffic.md) 检查驱动是否遗漏了 RX DMA 描述符填充。

