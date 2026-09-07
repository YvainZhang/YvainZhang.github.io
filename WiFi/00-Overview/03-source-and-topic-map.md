# 资料整合、正文索引与参考边界

本库将两份整理材料的主题分配到专题正文，保留模块概览作为入口。正文中的算例与示意日志是教学模型，不作为特定产品实测或个人项目经历；真实经验应以对应项目记录、代码与可公开证据另外证明。

## 从知识全景到正文

| 原始主题组 | 正文入口 | 应能展开的细节 |
|---|---|---|
| Host Driver / OS | [Linux 数据面](../04-Linux-Stack/03-qos-qdisc-driver-flow-control.md) | SKB、DSCP/TID/AC、qdisc、NAPI、所有权 |
| Host-Device Interface | [总线](../06-Bus-Data-Path/01-usb-sdio-pcie.md)、[DMA](../06-Bus-Data-Path/02-ring-dma-memory-ordering.md) | URB/CMD53/Ring、sync、SG、Credit |
| Firmware | [ABI](../05-Driver-Firmware/02-host-device-abi.md)、[状态机](../05-Driver-Firmware/03-firmware-state-machines.md) | boot、TLV、deadline、task、event、watchdog |
| Hardware MAC | [实时路径](../02-80211-MAC/02-hardware-mac-realtime-path.md) | parser、Context、SIFS、TSF/TBTT、原子更新 |
| PHY Baseband | [同步与MIMO](../11-PHY-RF-Calibration/03-sync-channel-coding-mimo.md) | CFO/SFO、估计、LLR、FEC、CSI |
| RF / Analog | [指标与校准](../11-PHY-RF-Calibration/02-rf-calibration-metrics.md) | EVM、噪声预算、PA、FEM、线损、OTP |
| Wi-Fi 6 / HE | [OFDMA/Trigger](../02-80211-MAC/03-he-ofdma-trigger-path.md)、[省电](../08-Power/01-power-state-machine.md) | RU、HE PPDU、UORA/BSR、Color/OBSS_PD、TWT |
| 多角色/多频段 | [资源与并发](../09-Scenarios-Integration/02-concurrency-coexistence.md) | SCC/MCC、厂商术语、Radio、PTA与deadline |
| 通用协议与安全 | [MAC](../02-80211-MAC/01-mac-air-interface.md)、[WPA/漫游](../03-Connection-Security/03-wpa-roam-port-state.md) | 地址、管理帧、PMF、AKM、11k/v/r |
| 性能指标 | [预算](../07-Performance/03-throughput-budget-model.md)、[Rate Control](../07-Performance/02-rate-control-link-adaptation.md) | airtime、Goodput、CPU/PPS、重试与统计口径 |
| 验证/Bring-up | [模型到Silicon](../12-Validation-Productization/01-validation-bringup.md) | bit-true、定点、UVM、FPGA、分层loopback |
| 认证/量产 | [测试与追溯](../12-Validation-Productization/02-certification-production.md) | DFS状态、限值版本、校准、guard band、工站相关性 |
| 现场问题与学习路线 | [证据链](../10-Debug-Recovery/01-evidence-workflow.md)、[复习图谱](02-interview-review-map.md) | 因果、时钟误差、单包映射、回归 |

## 从 Host–Device TRX 材料到实现

| 原始章节范围 | 整合位置 | 复习时的具体任务 |
|---|---|---|
| 1–3：分层、术语、TX | [端到端数据包](../01-System-Architecture/01-end-to-end-data-path.md) | 算每层长度，标记每次所有权转移 |
| 4、6–7：HE插入点与EDCA/TB对比 | [HE响应](../02-80211-MAC/03-he-ofdma-trigger-path.md) | 解释谁选择RU，谁执行微秒级响应 |
| 5：RX | [PHY Vector](../11-PHY-RF-Calibration/01-phy-tx-rx-vector.md)、[SKB/NAPI](../04-Linux-Stack/02-skb-netdev-napi.md) | 从detect追到Host refill与Socket |
| 8、19：shared memory、ring、offload | [DMA Ring](../06-Bus-Data-Path/02-ring-dma-memory-ordering.md) | 分清coherent控制区与streaming payload |
| 9–12：逐步TRX与观测图 | [所有权](../01-System-Architecture/03-state-ownership-and-lifetime.md)、[Trace](../10-Debug-Recovery/02-multi-source-trace.md) | 串起cookie、transfer、MPDU与PPDU |
| 13–14：数据单位和接入 | [EDCA/聚合/Retry](../02-80211-MAC/05-edca-aggregation-retry.md) | 推导AIFS、聚合收益与重传代价 |
| 15–16：建链与安全 | [生命周期](../03-Connection-Security/01-connection-lifecycle.md)、[Key/PN](../03-Connection-Security/02-key-pn-replay.md) | 区分关联、握手、端口与IP |
| 17：BA与reorder | [窗口演算](../02-80211-MAC/04-blockack-reorder-engine.md) | 手算4095→0、缺口、BAR与timer |
| 18：HE特性 | [OFDMA](../02-80211-MAC/03-he-ofdma-trigger-path.md)、[基带](../11-PHY-RF-Calibration/03-sync-channel-coding-mimo.md) | 连接RU、Vector、编码与接收失败 |
| 20：速率控制 | [链路自适应](../07-Performance/02-rate-control-link-adaptation.md) | 用概率与airtime比较候选rate |
| 21：功耗与调度 | [PS/TWT](../08-Power/01-power-state-machine.md)、[WoWLAN](../08-Power/02-wowlan-suspend-resume.md) | 算节能临界点，追踪唤醒事务 |
| 22–23：指标与记忆框架 | [复习图谱](02-interview-review-map.md)、[掌握标准](01-knowledge-system.md) | 用证据回答连续追问 |
| 24–25：并发与整合 | [并发资源](../09-Scenarios-Integration/02-concurrency-coexistence.md) | 推导dwell和共享资源上限 |

## 一手资料与版本

- [Linux 6.12 cfg80211](https://docs.kernel.org/6.12/driver-api/80211/cfg80211.html)：配置对象、操作与通知语义。
- [Linux 6.12 mac80211](https://docs.kernel.org/6.12/driver-api/80211/mac80211.html)：SoftMAC边界、TX/RX状态与卸载接口。
- [Linux 6.12 NAPI](https://docs.kernel.org/6.12/networking/napi.html)：budget、调度、完成和生命周期条件。
- [Linux 6.12 DMA](https://docs.kernel.org/6.12/core-api/dma-api-howto.html)：映射、地址、SG、一致性与所有权。
- [Linux 6.12 Softnet Driver Issues](https://docs.kernel.org/6.12/networking/driver.html)：SKB与netdev流控。
- [wpa_supplicant](https://w1.fi/wpa_supplicant/)：认证与安全状态背景，具体行为还需对应源码版本。
- [MathWorks Packet Recovery](https://www.mathworks.com/help/wlan/gs/packet-recovery.html)：可执行PHY阶段模型，不是芯片延迟测量。
- [AOSP Wi-Fi HAL](https://source.android.com/docs/core/connect/wifi-hal)：平台能力与接口组合，适配应锁定Android分支。

IEEE工作组讨论邮件可解释设计背景，但不替代已发布标准中的规范条款。涉及地区法规、认证版本、私有ABI和厂商能力时，应保留明确的适用边界，不能从本库通用模型推导某个产品的合规或全部实现细节。
