---
layout: post
title: "OGG 容器格式与流式复用机制"
subtitle: "从 OggS 页面结构、Lacing 变长分包、Granule 颗粒定位到 Opus/Vorbis 封装"
date: 2023-04-30
redirect_from:
  - /2021/11/30/ogg-container-basics/
  - /2021/11/14/ogg-container-basics/
author: Yvain Zhang
header-img: "img/post-bg-rwd.jpg"
series: "技术"
tags:
  - 多媒体
  - 音频
  - OGG
  - 容器封装
  - 编解码
---

**Ogg** 是由 Xiph.Org 基金会维护的开源多媒体容器格式（RFC 3533），广泛用于文件存储、HTTP 流式音频以及游戏音效引擎（封装 Opus / Vorbis 编码）。

与 MP4 依赖集中全局索引表（`moov`）的结构不同，Ogg 面向连续流式传输设计，采用 **Ogg Page（页面）** 串联机制，支持多逻辑流复用（Multiplexing）与断点重同步。解复用器通过维护分段状态机实现跨页 Packet 的重组还原。本文梳理 Ogg 页面头部结构、Lacing 变长分包算法以及 Granule 时间戳定位机制。

---

## 1. Ogg 流复用模型 (Logical Bitstreams)

在一个物理 Ogg 文件或网络流中，可以同时多路复用多个独立的**逻辑比特流（Logical Bitstream）**：

```
[ 物理 Ogg 数据流 ]
  ├── Page (Serial=101, Seq=0, BOS) ──> 音频头 (Opus Head / Vorbis)
  ├── Page (Serial=202, Seq=0, BOS) ──> 视频头 (Theora)
  ├── Page (Serial=101, Seq=1)       ──> 音频数据包
  ├── Page (Serial=202, Seq=1)       ──> 视频数据包
  └── Page (Serial=101, Seq=N, EOS)  ──> 音频流结束
```

- **逻辑流标识（Serial Number）**：每个逻辑流拥有唯一的 32 位序列号（如音频流 101，视频流 202），解复用器据此将页面派发给对应解码管道；
- **串联与链结（Chaining）**：多个 Ogg 文件可直接首尾相接拼接在一起（前一个流的 EOS 页紧接下一个流的 BOS 页），播放器可顺序连续解码。

---

## 2. 27 字节标准 Ogg Page 结构

Ogg 容器中的数据被划分为连续的 **Ogg Page**（单页最大载荷约 64 KB）：

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| capture_pattern: "OggS" (0x4F, 0x67, 0x67, 0x53)              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| version (0x00)| header_type   | granule_position              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| bitstream_serial_number                                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| page_sequence_number                                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| CRC_checksum (IEEE 802.3 32-bit CRC)                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| page_segments | segment_table (1 ~ 255 字节 Lacing Values)...  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| ... 数据载荷 (Payload: 由 segment_table 长度和决定)           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| 字段名称 | 字节大小 | 含义与作用 |
| :--- | :--- | :--- |
| **Capture Pattern** | 4 字节 | 固定为 ASCII `'O' 'g' 'g' 'S'`（`0x4F676753`），流同步定位标志。 |
| **Stream Version** | 1 字节 | 当前固定为 `0x00`。 |
| **Header Type** | 1 字节 | **标志位集合**：`0x01`=延续上一页（Continuation）；`0x02`=流开始首页（BOS）；`0x04`=流结束尾页（EOS）。 |
| **Granule Position** | 8 字节 (64-bit) | **时间戳**（由具体编解码器定义，如在 Opus 中为 PCM 采样总数，用于 Seek 定位）。 |
| **Serial Number** | 4 字节 | 该页所属逻辑比特流的唯一 ID。 |
| **Page Sequence No** | 4 字节 | 单调递增的页面计数器，用于检测网络丢包。 |
| **CRC32 Checksum** | 4 字节 | 页面数据校验和（多项式 `0x04C11DB7`）。 |
| **Page Segments** | 1 字节 | 标识后续 `segment_table` 中的字节数 $N$（取值 0~255）。 |
| **Segment Table** | $N$ 字节 | **Lacing 字节数组**，记录每个分段的长度（0~255）。 |

---

## 3. Lacing 变长分包机制 (Packet-to-Page Packing)

编解码器输出的是逻辑数据包（Packet，如一帧 Opus 压缩音频）。Ogg 通过 **Lacing Values** 将 Packet 映射进 Page 中：

```
[ 逻辑 Packet A: 500 字节 ] ──> 拆解为: [ 255 ] + [ 245 ]
[ 逻辑 Packet B: 100 字节 ] ──> 拆解为: [ 100 ]
[ 逻辑 Packet C: 510 字节 ] ──> 拆解为: [ 255 ] + [ 255 ] + [ 0 ] (恰好为255倍数时需追加0结尾)

Segment Table 写入: [ 255, 245, 100, 255, 255, 0 ]
```

### 解包规则
1. 解复用器顺序扫描 Segment Table，累加数值；
2. **遇到 `< 255` 的数值**时，标志当前 Packet 结束，将累加出的完整数据包提交给上层音频解码器；
3. **跨页处理**：若数据包在当前页写满（最后分段为 255），下一页的 `Header Type` 将置位 `0x01 (Continuation)` 继续接收剩余数据。

---

## 4. 常见音频载荷：Opus 与 Vorbis

1. **Ogg Opus (`.opus`)**：
   - 遵循 **RFC 7845** 规范；
   - 首页（BOS）包含 `'OpusHead'` 标识，声明声道数、Pre-skip（编码前置填充采样数）与原始采样率；
   - 第二页包含 `'OpusTags'`（VorbisComment 标签）；
   - 后续页面为 Opus 音频帧，Granule Position 以 **48 kHz 采样率下的 PCM 采样数** 递增。
2. **Ogg Vorbis (`.ogg`)**：
   - 包含 3 个头部包（Identification Header, Comment Header, Setup Header）；
   - 常用于游戏与开源生态中的免版税音频分发。

---

## 5. 总结

1. **流式设计**：基于 `OggS` 同步字与 27 字节轻量页头，支持网络切片中的断点重同步；
2. **时间戳抽象**：利用 64 位 `granule_position` 由底层编解码器自主维护采样时钟；
3. **分包开销低**：通过 Lacing 机制支持变长 Packet 的跨页拼接与边界识别。
