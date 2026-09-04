# 案例：ADDBA 异常导致业务失败

## 现象

STA 已完成关联与安全握手，但 DHCP 偶发超时。抓包显示对端发送 ADDBA Request，STA 没有及时响应，之后数据行为异常。

## 不要直接跳到结论

“没有看到 ADDBA Response”可能表示 STA 没收到 Request、收到后被过滤、管理队列阻塞、Response 发送失败，或者抓包设备漏帧。需要对齐四个位置：空口、Firmware RX、BA 状态机和 Firmware/Host TX。

## 证据链

1. 用 Dialog Token、TID 和 Sequence 对齐 ADDBA Request。
2. 检查 RX descriptor、帧合法性和 Action Frame 分发计数。
3. 确认 BA Session 创建结果、window size 与失败 reason。
4. 检查 Response 是否进入管理 TX queue、是否获得 bus/hardware 资源。
5. 观察 DHCP Packet 是否被 reorder 等待或因队列状态丢弃。

## 可能根因

- Action Frame 被错误长度/类型校验丢弃；
- BA 状态仍残留于旧连接，拒绝新 session；
- 管理 TX 与数据 TX 共用资源且被流控阻塞；
- Response 已发送但抓包点不完整；
- reorder window 初始化错误，普通数据无法及时上送。

## 修复与回归

修复应针对明确状态转换，并增加 reason 计数。回归覆盖重连、AP 反复发起 ADDBA、不同 TID/window、DELBA、丢帧与重复 Action Frame，同时验证 DHCP、TCP 和休眠恢复。
