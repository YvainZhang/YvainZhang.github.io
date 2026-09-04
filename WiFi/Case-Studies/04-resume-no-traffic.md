# 案例：休眠唤醒后断流

## 现象

系统 suspend/resume 后界面仍显示 Wi-Fi 已连接，但 Ping、ARP 或 TCP 均无响应；重新关闭再打开 Wi-Fi 可以恢复。

## 分层确认

| 层次 | Resume 后应验证 |
|---|---|
| Host | netdev queue、NAPI/work、Runtime PM 状态 |
| Bus | Function/Endpoint、IRQ、RX request/ring |
| Firmware | 心跳、VIF、key、BA、power state |
| Air/AP | STA 是否关联、PM bit、AP 缓存与下行帧 |
| Network | 地址、路由、ARP/ND、Socket |

## 常见路径

一个典型错误是：Host 恢复了 netdev，却没有重新提交 RX buffer；TX 仍可进入 Device，但 ACK、event 和下行数据无法返回。另一个错误是 Firmware 已丢失连接状态，而 Host 没收到 disconnect event，造成“逻辑已连接、物理已断开”。

## 定位步骤

1. 比较 suspend 前后的 bus inflight、Firmware generation 与 VIF 状态。
2. 主动发送一个带 Packet ID 的 ARP/Ping，追踪到空口或第一处消失点。
3. 检查 wake reason 和 resume 各阶段耗时，寻找超时后仍继续上报 ready 的路径。
4. 若恢复需要 reset，先保存 pending command、队列与 Firmware dump。

## 回归

覆盖空闲/有流量 suspend、不同 DTIM、AP 下行唤醒、反复休眠、USB autosuspend 与 system suspend 组合、P2P/SoftAP 并发。必须同时验证功耗与业务连续性。
