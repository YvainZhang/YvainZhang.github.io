# 03 流式语音交互：协议适配、取消与并发安全

## 1. 先区分通用架构与产品 API

ASR → LLM → TTS 级联可以逐段流式，也可以整体请求响应；是否支持打断取决于软件设计，不由“传统/现代”标签决定。端到端语音模型是另一种路径，不能把所有服务都描述成相同的级联实现。

本章定义的是**教学播放器架构**，不是 ChatGPT 客户端协议或某厂商可直接调用的 API。TTFA、插话检测和最终静音时间必须独立测量；600 ms、50 ms 等数值只能是明确条件下的设计目标，不是通用保证。

以 OpenAI Realtime 为例，其 WebSocket 接口使用事件协议，音频的编码与封装要按官方会话配置，不能把本文原先自定义的二进制 Opus 分片与消息名当作官方接口。[官方 WebSocket 指南](https://developers.openai.com/api/docs/guides/realtime-websocket)

## 2. 三个独立标识

| 标识 | 用途 | 错误做法 |
| --- | --- | --- |
| connection/session | 连接与鉴权生命周期 | 重连后复用所有旧响应对象 |
| response/stream ID | 区分一条服务端回复 | 把旧回复尾包误当新回复开头 |
| local generation | 区分本地取消前后的资源代际 | 仅将 ring 指针归零，允许旧回调继续写 |

网络适配层解析服务端消息，再转换为内部 `AudioChunk(response_id, generation, sequence, format, payload)`。这是内部数据结构，不是线上 JSON schema。重连、断流、重复分片和晚到包都应有显式处理策略。

## 3. 谁拥有资源

网络线程只负责校验和投递；解码线程拥有解码器；播放线程/驱动拥有 PCM 与 DMA；控制线程协调启停。共享数据通过目标平台的锁、原子变量和事件传递，单纯写一个 bool 不能替代内存同步。

SPSC 队列只保证约定的单生产者/单消费者操作安全，**不保证第三个线程可以随时 reset**。即使本核关中断，其他核仍可能读写队列，解码器也可能处于调用栈中。

## 4. 取消状态机与不变量

采用 LISTENING → PLAYING → STOPPING → QUIESCENT → LISTENING，任一步失败进入 ERROR。只允许控制线程执行迁移，重复取消必须幂等。

1. 在控制同步域内进入 STOPPING，关闭旧代际的入队与新 DMA 提交，推进 generation。已在途工作仍持有旧代际引用，不能立即释放。
2. 将远端 cancel 请求交给协议适配层；本地静音不能等待网络往返。远端停止生成、端侧停止播放、会话内容对齐是三个动作。
3. 由音频所有者在仍能输出时执行有界淡出或硬件 mute。先停 DMA 再“播放淡出”没有可执行的数据通路；硬件故障时使用器件允许的安全 mute 路径。
4. 通知网络生产者、解码消费者停止旧代际工作；在锁外等待各自确认，并等待其引用释放。等待期间不能持有回调退出必需的锁。
5. 请求驱动停止并同步 DMA/完成回调。超时转 ERROR，保留或隔离仍可能被访问的资源，不提前宣布 READY，也不强制释放。
6. 只有全部 worker 已静止、DMA 已静止且旧引用为零，才进入 QUIESCENT，重置队列和解码器，再建立新会话基线。

以下是**状态约束伪代码**，函数不是公开 SDK：
```text
controller.cancel():
    with control_lock:
        if state == STOPPING: return existing_cancel_ticket
        if state != PLAYING: return no_op_or_error
        state = STOPPING
        old_generation = generation
        generation += 1
        close_admission(old_generation)
    enqueue_remote_cancel(response_id)       # 不在控制锁内等待网络
    if not await_audio_owner_mute(old_generation, mute_deadline):
        enter_error_and_request_safe_stop()  # 不再尝试通过已停止 DMA 淡出
        return failure
    request_workers_stop(old_generation)
    request_dma_stop(old_generation)
    if not await_quiescent(old_generation, deadline):
        state = ERROR                       # 不 reset，不释放旧资源
        return failure
    reset_owned_objects_in_quiescent_state()
    state = LISTENING
```

`await_quiescent` 必须覆盖“已取出但尚未处理”的任务，不能仅检查队列为空。worker 检查 generation 与资源引用的获取需构成同一同步契约，避免检查后对象即被销毁的竞态。

## 5. 取消后仍收到旧音频

到达的旧 response ID/代际音频直接丢弃，不重新打开已取消的 decoder，也不让旧 EOS 终止新会话。服务端回复已生成但客户端未播完时，还应按所选协议对齐实际播放位置。

OpenAI Realtime 的取消与音频截断是不同事件；WebSocket 客户端需管理自己的播放缓冲，不能将仅用于 WebRTC/SIP 的输出缓冲事件套用到 WebSocket。接入时核对 [官方会话与打断指南](https://developers.openai.com/api/docs/guides/realtime-conversations)，并将官方 ID 映射为内部 ID。本章不提供固定型号、鉴权密钥或延迟保证。

## 6. 延迟分解与网络策略

`T_barge_in = 检测窗口 + 控制排队 + mute 生效`；资源清理完成时间可以更晚，应另外记录。TTFA 则包括采集/提交、服务端处理、网络、解码预缓冲与音频排队。统计中位数和 P95/P99，并记录误触发和漏检，不只给最短一次。

Jitter buffer 依据到达间隔、播放水位与欠载风险调整；60–100 ms 只是候选区间，需按产品容限测试。PLC 能减轻部分缺失帧影响，但不能保证无失真，更不能修复任意长 TCP 阻塞。采样率漂移控制与包到达抖动控制应分开。

## 7. 取消的最低测试集

| 注入条件 | 必须成立的结果 |
| --- | --- |
| 生产者已经取到旧 chunk 后取消 | 不再发布到新代际；引用最终释放 |
| 解码器正在计算时取消 | 不并发 reset；等待 owner 确认 |
| DMA 完成迟到 | 不标记新任务完成，不访问已释放内存 |
| mute 或 stop 超时 | 保持 ERROR/隔离态，不提前 READY |
| 取消重复触发、重连、旧 EOS | 幂等处理，不跨会话污染 |
| 取消与新回复同时到达 | 新回复等待新基线建立或被明确拒绝 |

使用调度屏障主动放大竞态窗口，辅以目标线程检测工具和驱动 trace。伪代码审查不能替代并发测试，更不代表某款 RTOS 或声卡的实现已经通过。
