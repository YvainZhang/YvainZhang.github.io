# 01 Wi-Fi 系统架构

这一模块建立共同坐标：谁负责控制面，谁搬运数据，谁维护连接状态，以及问题发生时证据会留在哪一层。

## 核心模型

| 平面 | 主要内容 | 常见实体 |
|---|---|---|
| 控制面 | 扫描、建链、密钥、信道、功耗与恢复 | supplicant、cfg80211、Driver、Firmware |
| 数据面 | Packet、802.11 Frame、聚合、队列与流控 | TCP/IP、netdev、总线、MAC/PHY |
| 管理面 | 配置、统计、日志、dump 和版本能力 | nl80211、debugfs、vendor command、trace |

## Host 与 Device 的责任边界

- **SoftMAC**：mac80211 参与较多 MAC 管理与数据处理，Driver 负责硬件操作。
- **FullMAC**：建链与多数 MAC 状态机下沉到 Firmware，Host 通过命令/事件控制。
- **混合卸载**：现实产品常介于两者之间，必须以实际命令、事件和数据格式确认边界。

继续阅读：[一次数据传输的端到端路径](01-end-to-end-data-path.md)。

## 本章检查点

- 能画出产品真实的 Host/Firmware 分工图。
- 能分别指出控制命令、异步事件、TX 与 RX 的入口。
- 能解释“关联成功”“接口 UP”“获得 IP”和“业务可用”不是同一个状态。
