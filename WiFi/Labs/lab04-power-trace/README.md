# 实验 04：Linux 电源事件观测

## 目标

观察 Wi-Fi Runtime PM 或 system suspend 前后的事件顺序、唤醒来源与数据恢复时间。

## 安全边界

不同设备的 sysfs 和 debug 接口不同。本实验只给出只读观察方法；启用 autosuspend 或触发 system suspend 前，应确认测试机不会承载远程会话和重要任务。

## 只读快照

```bash
iw dev
iw dev IFNAME link
ip -s link show IFNAME
cat /sys/kernel/debug/wakeup_sources
```

debugfs 通常需要 root 且路径随内核变化。记录 suspend 前后相同字段，并同时运行带时间戳的 `iw event -t`。

## Trace

若内核启用了 power tracepoint，可使用 trace-cmd：

```bash
sudo trace-cmd record -e power -e irq -e workqueue sleep 20
sudo trace-cmd report
```

在 trace 期间制造一小段可识别流量，观察 Runtime PM、IRQ、workqueue 与网络事件的相对顺序。

## 结果

记录：进入/退出时间、wake source、第一条控制命令成功时间、第一包 TX/RX 时间、是否保留关联/IP，以及恢复失败时的 Driver/Firmware 状态。一次“成功唤醒”必须包含业务恢复，而不只是设备电源状态变为 active。
