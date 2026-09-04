# P2P、并发与 Android 集成

## P2P 生命周期

Wi-Fi Direct 通常经历 Device Discovery、Service Discovery、GO Negotiation 或 Persistent Group 恢复、Provisioning、Group Formation 和 IP 配置。GO 承担类似 AP 的角色，Group Client 类似 STA，但发现阶段会在 Social Channels 监听与搜索。

详细流程可参考 [Wi-Fi P2P 架构与协议全流程](/2024/08/18/wifi-p2p-basics/)。

## SCC 与 MCC

- **SCC**：多个角色共用同一信道，切换成本低，但角色的信道选择互相约束。
- **MCC**：单 PHY 在多个信道间分时，灵活但会损失 airtime，并影响 Beacon、发现和尾延迟。
- **多 PHY**：可真正并行，但仍共享总线、电源与天线资源。

并发问题要记录每个角色的 channel context、驻留比例、Beacon deadline、NoA/CTWindow 和队列调度，不能只看“两个接口都 UP”。

## AP+STA 的三层路径

STA 上行与 SoftAP 下行之间可能经过 bridge 或 IP forwarding/NAT。无线双角色吞吐还会被同一 PHY 的收发 airtime 放大消耗。排查时把路径拆成：Client↔AP role、Linux forwarding、STA role↔Upstream AP 三段分别测量。

## Android 集成边界

Android Wi-Fi 路径随版本变化，但通用检查仍包括：

1. Kernel Driver 是否正确上报 wiphy capability 与 interface combinations；
2. HAL/服务是否能创建、删除和查询接口；
3. supplicant/hostapd 配置、权限与控制 socket 是否匹配；
4. Framework 状态是否与 cfg80211 event 对齐；
5. suspend/resume、飞行模式、热点与 P2P 切换是否完整释放旧状态。

适配层不应伪造硬件不支持的并发能力。错误能力声明通常不会立即失败，而会在特定角色切换、信道组合或恢复路径上暴露。
