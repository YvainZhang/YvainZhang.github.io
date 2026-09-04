# 05 Host Driver 与 Firmware

FullMAC 和高卸载方案的关键不在某个私有命令格式，而在四类通用通道：Command、Event、TX Data、RX Data。每条通道都需要所有权、序号、超时、背压和恢复语义。

## 最小抽象

```text
Host                         Device
Command  ──────────────────→ Firmware state machine
Event    ←────────────────── async notification
TX Data  ──────────────────→ scheduler / MAC
RX Data  ←────────────────── reorder / decap
```

继续阅读：[命令、事件、数据与故障恢复](01-control-data-recovery.md)。

## 本章检查点

- 每个命令是否有 request ID、deadline 和取消语义？
- 每个 buffer 的所有权何时转移、何时归还？
- Chip Reset 后如何阻断旧事件并重建接口状态？
