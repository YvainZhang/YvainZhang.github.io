# 05 现场排错与调试案例 (Codecs & Streaming Case Studies)

## 案例一：非标 M4A 文件 `esds` 描述符畸变导致解封装器死循环与内存踩踏

### 1. 现象描述
在多媒体 SDK 稳定性自动化压测中，测试脚本向播放器投喂了 10,000 首网络随机采集的 M4A 音频文件。当播放到第 3421 首时，系统看门狗（WDT）突发超时复位。串口死前抓取到的任务调用栈显示，CPU 长期卡死在 `mp4_demuxer_parse_esds()` 函数中，且堆内存监控显示片内 RAM 出现了数十 KB 的内存踩踏。

### 2. 二进制解析与反汇编排查
使用十六进制编辑器打开故障 M4A 文件，直接定位到 `moov -> trak -> mdia -> minf -> stbl -> stsd -> mp4a -> esds` Box：

```
Offset(h)  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
00000120  00 00 00 34 65 73 64 73 00 00 00 00 03 80 80 80  ...4esds....???
00000130  22 00 01 00 04 80 80 80 14 40 15 00 00 00 00 01  "....@........
00000140  F4 00 00 01 F4 00 05 80 80 80 00 06 80 80 80 01  ?....?....?...
```

对比 ISO/IEC 14496-1 标准解析逻辑：
* `esds` 采用 ASN.1 风格的变长长度编码（Variable-length Tag/Length）。当最高位为 1 时，表示长度字节未结束（如 `0x80 0x80 0x80 0x22` 表示实际长度值解析需持续移位解码）。
* **代码缺陷追踪**：原厂驱动中解封装器代码在解析长度字段时，写了一个 `while (tag_byte & 0x80)` 循环，**但在读取数据流时没有检查剩余字节数是否越界**！
* 故障文件中的 `DecoderConfigDescriptor` 故意伪造了一个连续 8 个字节全为 `0x80` 的畸变数据段，导致解析函数在流中无限制往后读取，越过了当前 Box 边界，误将后面的音频样本数据当成 Descriptor 解析，陷入无限死循环并踩踏了相邻的堆内存。

### 3. 修复方案
为所有 ISOBMFF 解封装器强制增加 **绝对边界限制（Boundary Sentinel）**：
```c
/* 修复后的带边界防护描述符长度解析 */
static int mp4_read_descr_len(stream_reader_t *sr, uint32_t *len, uint32_t box_end)
{
    uint8_t b;
    uint8_t count = 0;
    *len = 0;
    do {
        if (sr->tell(sr) >= box_end || count++ >= 4) {
            /* 超过 Box 边界或长度字节超过 4 字节，断定为畸变数据，立即报错退出 */
            return -1;
        }
        b = sr->read_u8(sr);
        *len = (*len << 7) | (b & 0x7F);
    } while (b & 0x80);
    return 0;
}
```

---

## 案例二：WebSocket 网络下行分片丢失导致大模型语音出现“金属机械音”

### 1. 现象描述
在 ChatGPT 智能音箱项目中，当设备处于 WiFi 信号较弱的房间（丢包率约 5%~10%）进行连续语音对话时，音箱发出的回复声音频繁出现尖锐刺耳的“金属机器人声”，体验极差。

### 2. 全链路数据流抓包定位
1. 在端侧 WiFi 驱动层、WebSocket 层和 Opus 解码层分别进行时间戳打点和帧计数；
2. Wireshark 抓包表明：云端 TTS 下发的是 20ms 一帧的连续 Opus 语音包，每个包约为 40~60 字节；
3. **接收层检查**：TCP 提供可靠、有序的字节流，网络重传会增加等待，Socket 的一次读取也可能只返回部分 WebSocket 帧。应用需要自行保留未读完的数据，并区分 TCP 读边界和 WebSocket `FIN`/Continuation 的消息重组；TCP 重传本身不会把完整应用消息直接变成丢帧。[TCP 规范](https://www.rfc-editor.org/rfc/rfc9293.html)、[WebSocket 分片规则](https://www.rfc-editor.org/rfc/rfc6455.html#section-5.4)
4. **音频层检查**：若端侧解析器错误丢弃音频分片，或播放期限到达前数据仍未可用，应记录丢弃位置、包序号与解码调用。需要结合输出 PCM 判断伪影，不能仅凭“金属音”就认定解码器状态失锁。

### 3. 修复方案
1. **完善 WebSocket 分片组包状态机**：校验 `FIN` 位与操作码（Opcode `0x00` Continuation vs `0x02` Binary），完整重组后再交付上层；TCP 读边界与 WebSocket 帧边界需要分别处理。
2. **启用 Opus 丢包补偿（PLC, Packet Loss Concealment）机制**：
   确认缺失一帧或该帧无法在播放期限内使用时，可调用 `opus_decode(dec, NULL, 0, pcm_out, frame_size, 0)` 执行无包 PLC。最后参数是 `decode_fec`，`1` 请求解码带内 FEC，并非“声明丢失”。PLC 的 `frame_size` 要对应缺失时长的每声道样点数；本例为 20ms，还需检查返回值和输出容量。补偿后应比较输出与听感，PLC 不能保证消除所有伪影。[Xiph Opus 解码 API](https://www.opus-codec.org/docs/opus_api-1.6/group__opus__decoder.html)

---

## 案例三：AVS HTTP/2 客户端在双通道高并发下的锁死故障

### 1. 现象描述
在亚马逊 AVS 压力测试中，当音箱正在播放长达 1 小时的网络流媒体（Downchannel 持续传输音频），此时用户连续快速呼叫“Alexa”并发出查询天气的语音指令（Events Channel 持续上传 PCM），设备在第 3 次呼叫后瞬间停止响应，死锁卡死。

### 2. 根因分析
* 端侧系统基于同一个底层的 TLS/TCP socket 维护 HTTP/2 多路复用连接；
* 传输层使用了单一全局互斥锁 `tls_socket_mutex` 保护 socket 的 `send` 与 `recv`；
* `Streamer_Task` 在通过 Downchannel 接收音乐时，持有了 `tls_socket_mutex` 并阻塞在 `recv()` 等待网络数据；
* 当唤醒触发，高优先级的 `Audio_Record_Task` 试图通过 Events Channel 发射 `Recognize` 事件，调用 `send()` 请求同一个锁，被无限期挂起；
* 若 `recv()` 没有退出或超时机制，发送任务可能长期等待。应检查完整锁依赖，区分阻塞等待与循环等待造成的死锁。

### 3. 修复方案
1. **重新划分同步范围**：先核对 TLS 库的并发要求，避免持有全局状态锁等待网络。只有实现允许并发收发时，才考虑独立的 `tx_mutex` 与 `rx_mutex`；
2. **有界等待**：可以评估 500ms 超时，但应按请求类型和网络条件配置，同时提供取消、重连和线程退出路径。
