# 09 场景与平台集成

单一 STA 是起点，不是产品全貌。P2P、SoftAP、STA+AP/P2P 并发、Android 生命周期和网络转发会引入多个虚拟接口、信道约束和策略竞争。

## 关键维度

- 角色：STA、AP/GO、P2P Client、Monitor。
- 并发：SCC、MCC 或多 PHY。
- 网络：桥接、NAT、DHCP、IPv6 与防火墙。
- 平台：HAL、supplicant/hostapd、权限、服务启动与电源策略。

继续阅读：[P2P、并发与 Android 集成](01-p2p-concurrency-android.md)。

## 本章检查点

- 能画出所有 VIF、MAC 地址、信道和 netdev 的映射。
- 区分无线角色建立成功与三层网络可用。
- 平台适配不通过硬编码绕开 capability/regulatory 边界。
