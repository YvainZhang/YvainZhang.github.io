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

## 发现接口与业务接口不要混用

P2P Device发现和协商不一定与最终GO/Client数据接口同生命周期。记录设备身份、发现MAC、group接口、BSSID、角色和generation，避免group删除后发现事件引用已销毁netdev。

Service Discovery是可选流程，不是每次建组都必须执行。Persistent Group恢复也可能跳过部分普通协商；需根据实际路径查GO negotiation/invitation和provisioning状态。

## 同Radio转发的airtime算例

教学场景：无线Client→本机SoftAP→同Radio STA→上游AP，有效单跳服务率分别为R1和R2。若两个链路共享不能同时工作的Radio，忽略其他开销：

```text
每bit耗时 ≈ 1/R1 + 1/R2
端到端上界 ≈ 1 / (1/R1 + 1/R2)
```

R1=R2=300 Mbit/s时上界约150 Mbit/s，仍未扣竞争、切信道、重试和CPU forwarding成本。“两个接口各能300”不意味着转发也300。

## 三地址STA不自动支持透明桥接

普通三地址STA链路不能任意承载下游多个源MAC的透明二层桥接。是否可bridge需要对端/本端四地址、WDS或具体代理机制支持；常见热点共享使用路由/NAT。将bridge配置成功当作无线桥接能力证明会导致单向流量或地址学习问题。

IPv6转发/前缀与DHCP/RA策略也需独立确认，不能只验证IPv4 NAT。

## Android能力与生命周期

HAL描述接口组合，Framework依据可用模式选择STA/AP/P2P等；Kernel wiphy/FW能力还需一致。接口数量、并发类型、信道数、桥接AP和独立Radio能力是不同层次约束。

AOSP资料会随版本变化，适配时记录Android分支及HAL版本，不复制其他版本的属性名。参考 [AOSP STA/AP concurrency](https://source.android.com/docs/core/connect/wifi-sta-ap-concurrency) 与 [Wi-Fi HAL](https://source.android.com/docs/core/connect/wifi-hal)。

## 复习追问与答案

**Group formed为什么还不能传数据？** 安全、IP、路由、防火墙、并发信道和队列都可能尚未就绪。

**热点开启就掉STA一定是驱动bug吗？** 可能是能力组合限制或平台模式切换策略，应对齐HAL选择与底层事件。

**如何减少排查维度？** 先分别测两条无线链路，再测本机转发，最后测并发组合及省电切换。
