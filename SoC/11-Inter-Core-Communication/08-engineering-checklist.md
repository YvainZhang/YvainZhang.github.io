# 核间通信工程检查表

## 架构与地址

- [ ] 明确 SMP、AMP、异构加速或跨 Die 模式；
- [ ] 列出每个 Agent 使用的 VA、PA、IOVA、Device Address；
- [ ] 共享区已配置正确的安全域、防火墙、IOMMU/PMP 权限；
- [ ] 不在协议中交换仅对本地页表有效的裸指针；
- [ ] 跨核结构使用固定宽度字段并规定大小端、对齐与版本。

## Cache 与内存序

- [ ] 确认共享区是否处于同一硬件一致性域；
- [ ] Non-coherent 两侧均定义 Clean/Invalidate 的时机和范围；
- [ ] Producer 先完成 Payload，再以 Release 发布状态；
- [ ] Consumer 以 Acquire 观察状态后再读取 Payload；
- [ ] CPU、DMA、MMIO 分别使用正确的屏障/API；
- [ ] Producer/Consumer 字段避免共享 Cache Line；
- [ ] Cache 维护范围按平台 Line Size 向外对齐，且不会覆盖对端新数据。

## Queue 与协议

- [ ] Ring Full/Empty、Index 回绕和整数宽度定义清楚；
- [ ] SPSC、MPSC、MPMC 的 Producer/Consumer 数量与算法匹配；
- [ ] Descriptor 状态转换和所有权唯一；
- [ ] 每个请求有 Sequence/Cookie；
- [ ] 每次启动有 Epoch/Generation；
- [ ] Length、Offset、Opcode、Feature 都做边界检查；
- [ ] 超时、重试、取消、迟到 Completion 行为已定义；
- [ ] 重试型协议的业务操作具有幂等性或去重机制。

## 通知与中断

- [ ] 明确边沿/电平、W1C/Read-to-Clear、FIFO 深度；
- [ ] 中断只作提示，Handler 根据 Ring 状态 Drain；
- [ ] Clear、EOI、Unmask 顺序经过竞态分析；
- [ ] 目标核 Affinity、Priority、安全组和电源状态正确；
- [ ] 队列空转睡眠使用检查—Arm—复查协议；
- [ ] 中断合并参数同时满足吞吐与尾延迟目标。

## 生命周期

- [ ] 启动包含 Magic、ABI、Feature、Ready 和 Timeout；
- [ ] 停止先拒绝新请求，再 Drain、停止 DMA、屏蔽通知；
- [ ] Remote Reset 时旧请求全部按 Epoch 隔离；
- [ ] Runtime PM 能唤醒目标核或拒绝向掉电域写 Doorbell；
- [ ] Watchdog、Heartbeat 和业务进展分别监控；
- [ ] Crash Dump 包含 Build ID、寄存器、Ring 与 Fault 信息。

## 性能与验证

- [ ] 测量 P50/P99/P999，不只看平均值；
- [ ] 统计 Ring Occupancy、Full、Drop、Kick、Batch；
- [ ] 覆盖 Ring Full、Index Wrap、并发 Reset、Lost Doorbell；
- [ ] 覆盖 Non-coherent Cache 污染和错误维护范围；
- [ ] 验证低频、DVFS、深度休眠和高温降频场景；
- [ ] 使用协议状态和硬件计数器建立跨层证据链。

## 评审必须能回答的问题

1. 如果 Doorbell 永久丢失，队列如何重新获得进展？
2. 如果 Remote 在取走 Descriptor 后复位，Buffer 由谁回收？
3. 如果旧 Completion 在新会话到达，如何识别？
4. 如果双方 Cache Line 大小不同，按哪个粒度隔离？
5. 如果 Consumer 看到新 Head，什么保证 Slot 已可见？
6. 如果消息被重发，业务副作用会不会执行两次？
7. 如何证明 Timeout 是设备故障，而不是低功耗唤醒延迟？
8. 如何在不显著改变竞态时采集故障证据？

任何一个问题无法落到明确的状态、原语或寄存器，都说明协议设计仍不完整。
