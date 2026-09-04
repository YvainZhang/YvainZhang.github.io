# 实验 01：mac80211_hwsim 虚拟建链

## 目标

在不依赖真实射频硬件的环境中创建虚拟 Radio，观察 AP/STA 从接口创建到关联和 IP 连通的全过程。

## 环境

- 启用了 `mac80211_hwsim` 的 Linux 内核；
- `iw`、`hostapd`、`wpa_supplicant`；
- 建议使用可随时还原的虚拟机。

## 步骤

1. 加载两个虚拟 Radio：

   ```bash
   sudo modprobe mac80211_hwsim radios=2
   iw phy
   iw dev
   ```

2. 将一个接口交给 hostapd，另一个交给 wpa_supplicant。配置一个仅用于实验的 SSID 和密码，不复用真实凭据。
3. 另开终端记录事件：

   ```bash
   sudo iw event -t
   ```

4. 完成关联后，在隔离网段配置地址并互相 Ping。

## 观察

- `iw event -t` 中 scan、auth、assoc、connect/disconnect 的顺序；
- hostapd 与 supplicant 对同一握手的不同视角；
- `iw dev <ifname> link` 中 BSSID、频率和速率；
- 删除接口或停止 AP 时，断链事件与清理顺序。

## 扩展

故意使用错误密码、停止 hostapd、重复连接，确认失败状态是否能在有限时间内退出。hwsim 适合软件状态机实验，不代表真实射频、Firmware 或总线性能。
