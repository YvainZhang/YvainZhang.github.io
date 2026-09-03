# 调试、性能与工程案例

## 1. 建立分层证据链

核间通信问题应按以下顺序观察：

```text
业务事务 ID
→ 软件队列状态
→ Cache/Barrier 与所有权
→ Mailbox Pending/Mask/Ack
→ Interrupt Controller Route/Priority
→ 目标核异常入口
→ Remote Handler 与 Completion
→ NoC/IOMMU/ECC/RAS
```

不要从“没有收到回复”直接跳到“中断坏了”。请求可能根本没有发布成功，也可能已处理但 Completion 丢失。

## 2. 案例：偶发读取旧 Payload

### 现象

压力测试中，Consumer 看到 Producer Index 增加，但 Descriptor 的 Length 偶尔为零。

### 排查

1. 为 Index、Descriptor 写入和 Doorbell 加时间戳；
2. 观察到 Doorbell 先到达，Descriptor Cache Line 后写回；
3. 关闭 Cache 后故障消失，证明与可见性有关；
4. 核对共享区为 Non-coherent；
5. Producer 只 Clean 了 Index，没有 Clean Descriptor。

### 修复

按 `Descriptor/Payload Clean → Completion Barrier → Index Publish → Doorbell` 排序，并使用平台 Cache API 对齐维护范围。不能依赖延时或重复敲 Doorbell。

## 3. 案例：中断计数增加但队列不前进

可能原因：

- Mailbox 是共享中断，Handler 读错 Channel；
- Ack 顺序错误导致中断风暴，线程没有机会 Drain；
- Consumer 读取了旧 Producer Index；
- Descriptor Epoch 不匹配被全部丢弃；
- Remote 正在等待反向 Credit，形成协议死锁。

应同时记录 IRQ Count、Spurious Count、每次 Drain 数量、Head/Tail 和最后一个拒绝原因。

## 4. 案例：Remote 重启后随机完成错误请求

### 根因

旧会话的 Completion 在共享 Ring 中残留，Host 复用了相同 16 位 Sequence，新 Completion 与旧请求无法区分。

### 修复

- 增加 Epoch；
- Reset 时冻结队列并清空 Pending；
- 请求 ID 扩展为足够宽的单调编号；
- 旧 Epoch Completion 只计数并丢弃；
- 释放 Buffer 前确认 DMA 已 Quiescent。

## 5. 案例：强制复位 Remote 后 NoC Timeout

### 现象

Remote Watchdog 超时后，Host 立即 Assert Reset。随后其他 Master 访问同一 DDR Port 时出现 NoC Timeout；再次启动 Remote 也失败。问题只在高带宽压力下复现。

### 证据链

1. 复位前 Ring 已空，但 Remote DMA 的 Outstanding Read/Write Counter 不为零；
2. NoC Error Logger 指向 Remote 使用的 AXI ID；
3. IOMMU Fault Log 没有新 Fault，说明问题不只是地址映射；
4. Reset 后仍能看到未完成事务占用互联资源；
5. 把“等待 Master Idle/Isolation Ack”加入流程后，故障不再复现。

### 修复边界

- 正常停止使用软件 Quiesce，让 Remote 停止取新 Descriptor 并等待 Completion；
- 无响应恢复使用芯片规定的 Bus Isolation 或 Transaction Termination；
- 只有收到硬件完成状态后才 Assert Reset；
- 复位前保存 Outstanding、AXI ID、NoC Error 和 IOMMU Fault；
- 不把“撤销 IOMMU Mapping”当作排空事务，它最多让后续访问失败。

若硬件不支持隔离或安全终止，系统设计必须说明局部复位的限制，必要时升级为更大范围的 Reset Domain 恢复。

## 6. 延迟拆解

端到端延迟可拆为：

$$T = T_{enqueue}+T_{visibility}+T_{doorbell}+T_{irq}+T_{schedule}+T_{service}+T_{completion}$$

优化前先确定哪一项占主导：

- `T_visibility` 高：检查 Cache Clean 范围、共享区属性；
- `T_doorbell` 高：检查 CDC、Mailbox Busy 和电源唤醒；
- `T_irq` 高：检查 IRQ Mask、Priority、Affinity；
- `T_schedule` 高：使用专用线程、实时优先级或 Polling；
- `T_service` 高：优化 Remote 算法和内存访问；
- `T_completion` 高：批量返回或减少反向中断。

## 7. 吞吐模型

若每条消息大小为 $S$，批量为 $B$，每次通知固定成本为 $C_i$，每字节处理成本为 $C_b$：

$$C_{msg} \approx \frac{C_i}{B}+S\cdot C_b$$

增大 Batch 可摊薄中断成本，但增加排队延迟。工程上应绘制 Batch Size 对吞吐和 P99 延迟的曲线，而不是只追求峰值消息率。

## 8. 调试手段

- 共享 Trace Buffer：双方写固定长度事件，附带 Core ID、Epoch、Sequence；
- Mailbox 寄存器快照：Pending、Mask、Route、FIFO Level；
- GIC/IMSIC 状态：是否 Pending、Active、被 Priority Mask；
- IOMMU Fault Log：Stream ID、IOVA、访问类型；
- PMU/NoC Counter：互联拥塞、Remote Cache Miss、带宽；
- JTAG：暂停双方时注意会改变实时序列并可能触发 Watchdog；
- Fault Injection：丢一次 Doorbell、延迟 Completion、Remote Reset、Ring Full、损坏 Length。

## 9. 观测代码本身的风险

调试日志可能改变时序、Cache 布局和中断频率，使竞态消失。Trace 设计应：

- 使用每核独立 Ring，降低锁竞争；
- 固定长度、无动态分配；
- 支持采样和运行时开关；
- 崩溃时冻结并保留最后 N 条；
- 明确 Trace 的内存序，避免日志反过来成为隐藏屏障。
