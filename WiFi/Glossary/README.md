# 术语表与缩写全景

Wi-Fi 跨越了应用软件、Linux 内核、总线驱动、固件 RTOS、硬件 MAC、基带 PHY 及射频射电多个学科。同一种机制在不同层级往往有不同的专业术语。本表按系统层次系统收录核心术语与工程边界。

---

## 1. 802.11 MAC 与空口接入 (Air Interface & MAC)

| 术语 | 英文全称 | 核心含义与系统边界 |
|---|---|---|
| **A-MPDU** | Aggregate MAC Protocol Data Unit | 聚合多个 MPDU，共享同一个 PHY Preamble，由 Block ACK 批量选择性确认，现代 Wi-Fi 高吞吐的核心。 |
| **A-MSDU** | Aggregate MAC Service Data Unit | 在 MAC 层内部将多个以太网帧（MSDU）封装进同一个 MPDU，降低 MAC Header 开销，共享单个 FCS 与 PN。 |
| **AIFS / AIFSN** | Arbitration Inter-Frame Space (Number) | EDCA 差异化信道竞争的基础等待时间，高优先级（如 VO）AIFSN 较小，更早启动退避。 |
| **BA / BAR** | Block ACK / Block ACK Request | 块确认与块确认请求。由位图（Bitmap）批量指示接收状态，推动发送与接收端的滑动窗口。 |
| **BSS / BSSID** | Basic Service Set (Identifier) | 基本服务集及其 MAC 地址标识（通常即为 AP 射频口 MAC）。 |
| **BSS Color** | BSS Coloring | 802.11ax 引入的 6-bit 标识，用于在空间复用中快速区分本 BSS 帧与邻居重叠 BSS (OBSS) 帧。 |
| **BSR / BSRP** | Buffer Status Report (Poll) | 上行 OFDMA 调度前，STA 向 AP 报告待发数据队列长度的机制及 AP 触发轮询帧。 |
| **CCA-ED / CS** | Clear Channel Assessment (Energy / Carrier) | 物理载波侦听：能量检测（非 802.11 宽带噪声）与前导码载波侦听（有效 802.11 信号）。 |
| **CWmin / CWmax** | Contention Window (Min / Max) | 退避争用窗口上下限。碰撞重传时 CW 指数翻倍退避，成功后重置回 CWmin。 |
| **DTIM / TIM** | Delivery Traffic Indication Message (Map) | AP 在 Beacon 中告知休眠 STA 是否有缓存单播（TIM）及多播/广播下发周期（DTIM）。 |
| **EDCA** | Enhanced Distributed Channel Access | 802.11e QoS 接入机制，划分为 VO、VI、BE、BK 四个 Access Category 进行优先级退避。 |
| **EOSP** | End of Service Period | U-APSD 省电服务周期结束标志位，指示本次突发下发已交付完毕。 |
| **NAV** | Network Allocation Vector | 虚拟载波侦听计时器。根据侦听到的帧时长字段（Duration）在本地倒计时，期间不发起竞争。 |
| **OBSS_PD** | Overlapping BSS Preamble Detection | 空间复用门限：若检测到的信号属于其他 BSS 且信号低于阈值，允许忽略并不触发退避。 |
| **Reorder Engine** | Reorder Engine & Buffer | 接收端按 Sequence Number (SN) 将乱序到达或重传补全的 MPDU 恢复为保序流的硬件/软件引擎。 |
| **SIFS / DIFS** | Short / DCF Inter-Frame Space | 短帧间间隔（SIFS，通常 10/16μs，用于 ACK/BA 等即时响应）与普通分布式帧间间隔（DIFS）。 |
| **TBTT** | Target Beacon Transmission Time | 目标信标发射时刻。AP 预定发射 Beacon 的周期性硬件时间基准。 |
| **TID** | Traffic Identifier | 流量分类标识符（0~15），映射 QoS 优先级、独立维护 Sequence Number 与 BA Session。 |
| **TXOP** | Transmission Opportunity | 一次竞争胜出后允许连续占用信道发送多帧的最大时间配额（期间帧间仅留 SIFS）。 |
| **UORA** | UL OFDMA Random Access | 802.11ax 上行随机接入：STA 在未被显式分配专用 RU 时，利用 OFDMA 退避竞争随机 RU。 |

---

## 2. 安全、握手与网络建链 (Security & Connection)

| 术语 | 英文全称 | 核心含义与系统边界 |
|---|---|---|
| **AKM** | Authentication and Key Management | 认证与密钥管理套件，协商具体认证机制（如 PSK、802.1X、SAE）。 |
| **Controlled Port** | Controlled Port State | 802.1X / WPA 安全受控端口，密钥未就绪前阻断普通数据，仅放行 EAPOL 报文。 |
| **EAPOL** | EAP over LAN | 在局域网链路上承载可扩展认证协议报文的载体，用于 WPA 4 次握手。 |
| **MIC** | Message Integrity Code | 报文完整性校验码，防止数据包内容被篡改，校验失败会触发重放告警或反制。 |
| **PMF** | Protected Management Frames (802.11w) | 受保护的管理帧，为 Deauth、Disassoc 和部分 Action 帧提供加密与防伪造保护。 |
| **PMK / PTK / GTK** | Pairwise Master / Transient / Group Key | 主密钥（PMK）、单播临时会话密钥（PTK，由 4 次握手生成）、组播密钥（GTK）。 |
| **PN** | Packet Number | CCMP/GCMP 加密中的单调递增报文序号，用于接收端防重放攻击 (Anti-Replay)。 |
| **SAE** | Simultaneous Authentication of Equals | WPA3-Personal 的对等实体同时认证协议，基于 Dragonfly 握手防御离线字典攻击。 |

---

## 3. 基带 PHY、射频与校准 (PHY & RF Calibration)

| 术语 | 英文全称 | 核心含义与系统边界 |
|---|---|---|
| **AGC** | Automatic Gain Control | 自动增益控制，在接收到信号前导码的几十微秒内调整 LNA 与数字衰减，使 ADC 不饱和。 |
| **CFO / SFO** | Carrier / Sampling Frequency Offset | 载波频偏（晶振偏差引起中频偏移）与采样频偏，基带必须实时估计并补偿。 |
| **CSI** | Channel State Information | 信道状态信息，描述多径信道各子载波的幅相衰减矩阵，用于波束成形与 MIMO 解调。 |
| **EVM** | Error Vector Magnitude | 误差矢量幅度，衡量发射机调制精度的核心指标，高阶调制（如 1024-QAM / 4096-QAM）要求极严苛。 |
| **GI / LTF** | Guard Interval / Long Training Field | 保护间隔（防多径符号间干扰 ISI，0.8/1.6/3.2μs）与长训练序列（信道估计参考）。 |
| **MCS** | Modulation and Coding Scheme | 调制编码策略索引（定义 QPSK/16QAM/64QAM/256QAM/1024QAM 及卷积码/LDPC 码率）。 |
| **NDP** | Null Data Packet | 无数据载荷的专用 PHY 探测包，AP 发送以引导 STA 测量信道并反馈 CSI。 |
| **NSS** | Number of Spatial Streams | 空间流数量。表示空口同时传输的独立空间数据流数，受限于天线通道数 $\min(N_{\text{TX}}, N_{\text{RX}})$。例如 2T2R 天线配置最高支持 2 空间流，但也可配置为单空间流辅以分集（STBC/波束成形）提升信噪比。 |
| **PAPR** | Peak-to-Average Power Ratio | 峰均比，OFDM 信号多载波叠加导致瞬时峰值极高，要求功放 (PA) 留足回退 (Backoff)。 |
| **RU** | Resource Unit | OFDMA 频域资源单元（26/52/106/242/484/996 tones），将 20/40/80/160MHz 频宽划分为子信道。 |
| **TX/RX Vector** | PHY Transmit / Receive Vector | MAC 与 PHY 之间的参数接口结构体，指示空口每一帧的 MCS、频宽、GI、编码、功率与天线掩码。 |

---

## 4. Linux 内核软件栈、驱动与总线 (Linux Stack, Driver & Bus)

| 术语 | 英文全称 | 核心含义与系统边界 |
|---|---|---|
| **BQL** | Byte Queue Limits | Linux 驱动层防缓冲膨胀机制，动态调节硬件队列积压的字节数上限以降低延迟。 |
| **cfg80211** | Configuration 802.11 | Linux 内核无线配置框架，提供统一的 nl80211 接口并管理 wiphy、regulatory 与连接状态。 |
| **Coherent DMA** | Consistent / Coherent DMA Mapping | 硬件与 CPU 自动保持一致的 DMA 内存，用于描述符 Ring 和状态标志位，无需手动 Flush/Invalidate。 |
| **Credit Flow** | Credit-based Flow Control | 固件 $\leftrightarrow$ 驱动的令牌流控机制，固件释放 Buffer 后返还 Credit，驱动无 Credit 时停止发送队列。 |
| **FullMAC** | Full MAC Architecture | 大部分 MLME（扫描、关联、握手、加密、省电）由芯片固件承担的驱动架构。 |
| **Generation ID** | Context Generation Counter | 代际标识符，防止因异步延迟到达的旧事件/旧中断污染复位或重连后的新会话。 |
| **mac80211** | Generic SoftMAC 802.11 Framework | Linux 内核通用 SoftMAC 框架，驱动仅负责硬件收发，MLME 与帧生成由 mac80211 统一处理。 |
| **MCC / SCC** | Multi / Single Channel Concurrency | 多信道并发与同信道并发。MCC 需时分轮巡切频，存在切频停顿与丢信标开销；SCC 多个 VIF 工作在同一信道，免除了切频开销，但各角色仍共享同信道空口时间与硬件队列竞争。 |
| **MSI-X** | Extended Message Signaled Interrupts | PCIe 高性能中断机制，支持多向量中断分别绑定不同 CPU 核心处理 RX、TX 与事件。 |
| **NAPI** | New API (Linux Network Polling) | Linux 中断+轮询的收包优化机制，在高吞吐下关闭中断转为软中断轮询，避免中断风暴。 |
| **nl80211** | Netlink 802.11 | 用户态（wpa_supplicant / iw / NetworkManager）与内核 cfg80211 通信的通用 Netlink 协议族。 |
| **qdisc** | Queueing Discipline | Linux 网络栈排队规则（如 pfifo_fast, fq_codel, cake），负责多流排队调度与拥塞控制。 |
| **SKB** | Socket Buffer (`struct sk_buff`) | Linux 网络核心数据包载体，贯穿协议栈、驱动与 DMA 映射全流程。 |
| **SoftMAC** | Soft MAC Architecture | MAC 状态机和 802.11 帧头封装主要由 Host CPU (mac80211) 处理的架构。 |
| **Streaming DMA** | Streaming DMA Mapping | 面向高吞吐数据流的单向 DMA 映射（DMA_TO_DEVICE / DMA_FROM_DEVICE），需严格配合 sync API。 |
| **URB** | USB Request Block | Linux USB 子系统所有异步传输请求的基本载体。 |
| **VIF** | Virtual Interface | 虚拟网络接口（STA、AP、P2P_GO、P2P_CLIENT、Monitor），共享同一物理 Radio。 |
| **WoWLAN** | Wake on Wireless LAN | 无线网络唤醒，主机休眠时固件在后台保持链路并在匹配到特定帧时拉中断唤醒 Host。 |

---

调试工程记录时，建议始终标明：**术语所处层次**、**关联的 VIF / Peer / TID**、以及**硬件代际 / 时间戳基准**，避免在跨团队排查中因同名异义概念产生歧义。

