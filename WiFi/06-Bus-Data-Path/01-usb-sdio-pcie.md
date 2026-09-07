# USB、SDIO 与 PCIe 数据路径

## USB

USB Wi-Fi 常用 Bulk Endpoint。Host 将一个或多个 Packet 封装进 URB，HCD 调度后才真正传输；完成回调表示 USB 事务结束，不代表 MAC 已获 ACK。优化抓手包括：

- 预提交足够 RX URB，避免设备有数据却无 Host buffer；
- TX/RX 聚合减少每次提交和回调开销；
- 将解析、协议栈处理与完成回调分层，避免回调上下文过重；
- 观察 URB 长度分布、inflight 数、完成间隔与错误码；
- 对齐 CPU affinity，减少跨核迁移与 Cache 抖动。

聚合并非越大越好。设单包固定成本为 `C`，聚合 `N` 个包可摊薄为 `C/N`；但等待凑包会增加排队时延，并扩大一次错误的影响面。需要针对吞吐与交互流量设置大小和时间双阈值。

## SDIO

SDIO 通常通过 CMD53 批量读写数据端口。关注 block size、对齐、host claim、IRQ/thread 调度和设备侧可用长度寄存器。频繁小事务会被命令开销吞噬；一次搬运过大又可能阻塞控制命令和高优先级事件。

## PCIe

PCIe 方案常用 Host/Device 共享的 DMA Ring。Producer/Consumer 指针更新需要明确内存顺序，Doorbell 之前确保 descriptor 和 payload 对设备可见；回收前确保完成状态已同步。还要处理 IOMMU mapping、MSI/MSI-X affinity 与 Function Level Reset。

## 通用守恒关系

无论哪种总线，都可以用相同计数建立第一层定位：

```text
Host enqueue
= bus submit + host-side pending + host drop

bus submit
= bus complete + bus inflight + bus error/cancel

device receive
= firmware consume + device queue + parse/drop
```

在固定时间窗取差分。第一处明显不守恒的位置，就是下一轮增加 Trace 的地方。

详细 USB 驱动案例可参考博客文章 [Wi-Fi USB 驱动架构与多核性能调优](/2025/07/13/wifi-usb-driver-performance-tuning/)。

## USB 请求的生命周期与取消

USB completion 回调处理 `status` 和 `actual_length`。成功 transport 仍需验证设备私有聚合格式；短包是否是合法边界取决于 endpoint/协议定义。错误回调不应继续解析未完成 payload。

`usb_unlink_urb()` 发起异步取消；`usb_kill_urb()` 等待终止且可能睡眠，不能在禁止睡眠的上下文使用。Disconnect 先阻止新 submit，再终止/等待在途请求，最后释放 callback 引用的私有对象。只释放 URB 对象不代表其 context 已无人访问。

RX completion 若把原 buffer 交给后续解析/网络栈，就不能立刻把同一内存重新提交给 Device。选择复制、交换新 Buffer 或引用计数方案时，要把 refill 的资源成本计入预算。参考 [Linux URB](https://cdn.kernel.org/doc/html/latest/driver-api/usb/URB.html)。

## 总线聚合解析算例

教学私有格式为 8 byte 子包头、2 byte length、8-byte 对齐。实际收到 104 byte，首包 payload=60，则占 `align8(8+60)=72`，还剩32。第二包若宣称 payload=40，就需要48 byte，必须拒绝，不能继续按分配 buffer 的容量读取。

`actual_length`、子包长度、聚合总长三者分别校验。带填充的传输字节不等于有效网络字节；performance counter 应标明口径。

## SDIO 的事务边界

CMD53 可按字节或 block 传输，地址可固定或递增；FIFO/数据端口通常需要匹配设备定义的地址模式。不能把连续内存操作直接套到固定 FIFO 地址。

Host claim 保证相关总线访问串行，但在持有期间执行大段 packet parsing 会推迟控制命令/其他 function。设计分批搬运、释放 host、再处理数据的边界时，还要确保设备 FIFO 长度和数据不会被另一消费者抢走。

需要校验设备报告长度、最大 host request、block 对齐和 padding。传输错误后的重试是否安全取决于 FIFO 是否已经部分消费，不能默认从头重发幂等。

## PCIe 的独立约束

设备通常经 DMA 地址读写 payload，MSI/MSI-X 通知 completion。描述符可见性、doorbell MMIO 顺序、DMA mask/IOMMU 和 Reset quiesce 都属于正确性条件。提高 PCIe 链路带宽不能修复 consumer index 未推进的问题。

PCIe low-power 状态、唤醒和共享 interconnect 延迟也会影响短包尾延迟。测量应区分 queue wait、Device DMA、MAC wait 和 interrupt coalescing。

## 三种总线的同口径对比

在同一 packet size/方向/聚合设置下，记录有效字节率、实际传输字节率、CPU time、请求延迟分布和在途容量。吞吐上限还受对端与空口约束；接口标称速率不是可直接交付应用的速率。

## 复习追问与答案

**URB 够大为什么还会断供？** 预提交数量、completion→refill 空隙或主控调度可能让 inflight 归零。

**SDIO 错误能直接重试吗？** 必须知道上次事务是否消费部分 FIFO；否则可能重复或错位。

**三种总线都需要 generation 吗？** 都有异步生命周期，但载体不同：共享 descriptor、URB context 或 FW message，需按 ABI 设计。
