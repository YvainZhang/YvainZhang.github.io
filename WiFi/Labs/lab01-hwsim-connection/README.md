# 实验 01：mac80211_hwsim 虚拟无线建链与状态观测

## 实验目标

在无需任何真实 Wi-Fi 射频网卡与屏蔽箱的环境下，利用 Linux 内核的 `mac80211_hwsim` 驱动创建两个虚拟无线节点（一个作为 AP，一个作为 STA），完成从扫描、WPA2 握手、关联到 IP 通信的全流程，并实时观测内核与用户态的状态机事件流。

## 实验准备与避坑说明

- **系统要求**：Ubuntu 20.04/22.04/24.04 或 Debian (内核已内置 `CONFIG_MAC80211_HWSIM=m`)。
- **工具安装**：
  ```bash
  sudo apt-get update && sudo apt-get install -y hostapd wpa_supplicant iw wireless-tools tshark
  ```
- **避坑警告 (NetworkManager 干扰)**：
  桌面发行版默认开启的 NetworkManager 会自动抢占虚拟无线网卡，导致 AP 启动失败或 STA 握手被打断。实验前务必将虚拟网卡设为未托管：
  ```bash
  sudo nmcli dev set wlan0 managed no 2>/dev/null || true
  sudo nmcli dev set wlan1 managed no 2>/dev/null || true
  ```

## 步骤 1：加载虚拟无线驱动并核验接口

加载包含 2 个虚拟 Radio 的模块：
```bash
# 加载驱动并创建两个虚拟无线射频
sudo modprobe mac80211_hwsim radios=2

# 查看生成的接口名称 (通常为 wlan0 和 wlan1)
iw dev
```
预期输出类似：
```text
phy#1
    Interface wlan1
        ifindex 4
        type managed
phy#0
    Interface wlan0
        ifindex 3
        type managed
```

## 步骤 2：启动 AP 端 (hostapd)

创建最小 AP 配置文件 `/tmp/hwsim-hostapd.conf`：
```ini
interface=wlan0
driver=nl80211
ssid=Hwsim-Lab-AP
hw_mode=g
channel=6
wpa=2
wpa_passphrase=password123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
rsn_pairwise=CCMP
```

在默认命名空间中启动 hostapd（记录 PID 便于清理）：
```bash
sudo hostapd -B -P /tmp/hwsim-hostapd.pid /tmp/hwsim-hostapd.conf
```

## 步骤 3：动态识别 STA 无线 PHY 并隔离至 Network Namespace

!!! important "为什么必须按 wiphy 隔离网络命名空间？"
    1. **避免本地回环短路**：若将两个属于同一子网的 IP（如 `192.168.99.1` 和 `192.168.99.2`）直接配置在同一个 Linux 网络命名空间，内核本地路由表（`table local`）会直接由 `lo` 回环短路交付，根本不流经虚拟无线介质。
    2. **cfg80211 的命名空间规则**：Linux 内核规定无线网卡（`net_device`）必须与其所属的无线物理层实体（`struct wiphy`）一同迁移，不能使用常规的 `ip link set <dev> netns <ns>`。必须动态识别其绑定的 `wiphy` 名称，再调用 `iw phy <phyname> set netns name <ns>`。

```bash
# 1. 动态查询与 wlan1 绑定的 wiphy 名称 (如 phy1，避免硬编码)
STA_PHY=$(iw dev wlan1 info | awk '/wiphy/ {print "phy"$2}')

# 2. 创建独立的网络命名空间
sudo ip netns add sta_ns

# 3. 将 STA 对应的整个 wiphy 迁移进命名空间
sudo iw phy "$STA_PHY" set netns name sta_ns

# 4. 验证无线物理接口已在命名空间内可见
sudo ip netns exec sta_ns iw dev
```

## 步骤 4：在命名空间内启动 STA 并完成建链

创建 STA 配置文件 `/tmp/hwsim-wpa.conf`：
```ini
ctrl_interface=/var/run/wpa_supplicant
network={
    ssid="Hwsim-Lab-AP"
    psk="password123"
    key_mgmt=WPA-PSK
    proto=RSN
    pairwise=CCMP
}
```

在 `sta_ns` 命名空间中启动 `wpa_supplicant`：
```bash
sudo ip netns exec sta_ns wpa_supplicant -B -P /tmp/hwsim-wpa.pid -i wlan1 -c /tmp/hwsim-wpa.conf
```

检查连接状态：
```bash
sudo ip netns exec sta_ns iw dev wlan1 link
```
预期看到：`Connected to 02:00:00:00:00:00`, `SSID: Hwsim-Lab-AP`, `rx bitrate: 54.0 MBit/s`。

## 步骤 5：跨命名空间配置 IP 并进行真无线链路 Ping 测试

```bash
# 1. 为 AP 分配 IP (默认命名空间)
sudo ip addr add 192.168.99.1/24 dev wlan0
sudo ip link set wlan0 up

# 2. 为 STA 分配 IP (sta_ns 命名空间)
sudo ip netns exec sta_ns ip addr add 192.168.99.2/24 dev wlan1
sudo ip netns exec sta_ns ip link set wlan1 up

# 3. 在终端中实时监听 AP 接口的数据包
# 若看到 ARP 请求与 ICMP 报文，证明流量切实穿过了 mac80211_hwsim 虚拟无线介质
sudo tcpdump -i wlan0 -nn -e icmp &
TCPDUMP_PID=$!

# 4. 从 sta_ns 命名空间向 AP 发起 Ping
sudo ip netns exec sta_ns ping -c 4 192.168.99.1

kill $TCPDUMP_PID 2>/dev/null || true
```

## 步骤 6：安全清理实验环境

使用记录的 PID 文件安全终止实验进程，避免使用危险的 `killall` 误杀系统其他无线服务：

```bash
# 终止实验进程
[ -f /tmp/hwsim-hostapd.pid ] && sudo kill $(cat /tmp/hwsim-hostapd.pid) 2>/dev/null || true
[ -f /tmp/hwsim-wpa.pid ] && sudo kill $(cat /tmp/hwsim-wpa.pid) 2>/dev/null || true

# 删除测试命名空间并卸载驱动
sudo ip netns del sta_ns 2>/dev/null || true
sudo modprobe -r mac80211_hwsim 2>/dev/null || true
rm -f /tmp/hwsim-*.conf /tmp/hwsim-*.pid
```

## 进阶挑战

1. **错误密码实验**：将 `/tmp/hwsim-wpa.conf` 中的密码改为 `wrongpass`，再次运行，观察 `wpa_supplicant` 日志：在 Association 成功后，四次握手因 MIC 校验失败被 AP 踢下线并抛出 `Deauth (reason 2: PREV_AUTH_NOT_VALID)`。
2. **虚拟 Monitor 抓包**：在加载驱动后，通过 `sudo iw phy phy0 interface add mon0 type monitor` 创建专用的虚拟监听接口，利用 Wireshark 捕获无损的 802.11 原始管理帧。


