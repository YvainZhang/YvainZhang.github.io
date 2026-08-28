---
layout: post
title: "MP3 格式解析与解码流程"
subtitle: "从 ID3 标签、32位帧头、位库技术到 IMDCT 解码管线"
date: 2022-09-04
redirect_from:
  - /2021/03/26/mp3-format-and-decoding/
  - /2021/04/10/mp3-format-and-decoding/
author: Yvain Zhang
header-img: "img/post-bg-rwd.jpg"
series: "技术"
tags:
  - 多媒体
  - 音频
  - MP3
  - 编解码
---

MP3（全称 **MPEG-1 Audio Layer III** 或 **MPEG-2 Audio Layer III**，标准编号 ISO/IEC 11172-3 / 13818-3）是广泛应用的感知音频有损压缩格式之一。

在播放器开发或音频驱动调试中，理解 MP3 的关键点包括：**帧同步字定位、变长帧长计算公式、位库（Bit Reservoir）以及从频域到时域的 IMDCT 还原流程**。

---

## 1. MP3 文件整体结构

标准的 MP3 文件由三大部分构成：

```
+───────────────────────+──────────────────────────────+───────────────────────+
|   ID3v2 标签 (文件头)  |      音频数据帧序列 (Frames)   |   ID3v1 标签 (文件尾) |
| (变长，存歌名/封面等)  | [Frame 0][Frame 1]...[Frame N]|  (固定 128 字节，兼容)|
+───────────────────────+──────────────────────────────+───────────────────────+
```

### 1.1 ID3v1（尾部固定 128 字节）
- 位于文件末尾 128 字节，以 ASCII 字符 `TAG` 开头，字段长度固定（标题 30B、艺术家 30B、专辑 30B、年份 4B、流派 1B）。ID3v1.1 借用评论字段末尾存储音轨号。

### 1.2 ID3v2（头部可扩展标签）
- 位于文件开头，常见版本为 ID3v2.3 / ID3v2.4。采用“Frame Header + Frame Body”的键值结构（如 `TIT2` 为标题、`TPE1` 为艺术家、`APIC` 为内嵌封面图片），大小通过 Syncsafe 整数（每个字节仅使用低 7 位，防止与音频同步字冲突）表示。纯音频解码器通常直接跳过 ID3v2 头部定位首个音频帧。

---

## 2. MP3 音频帧结构与 32-bit 帧头解析

MP3 音频数据由连续的音频帧（Frame）组成。在 MPEG-1 Layer 3 下，每个音频帧解码后输出 **1152 个 PCM 采样点**（包含 2 个 Granule，每个 576 样本）。

```
+─────────────────────+─────────────────────+─────────────────────+─────────────────────+
|   帧头 (Header)     |  CRC 校验 (可选)    |   边信息 (Side Info)|   主数据 (Main Data)|
|      (4 字节)       |      (2 字节)       |   (17 或 32 字节)   | (哈夫曼编码频谱数据)|
+─────────────────────+─────────────────────+─────────────────────+─────────────────────+
```

### 2.1 32-bit 帧头位域分布

```
 31             21 20 19 18 17 16 15  12 11 10 9  8  7 6 5 4 3 2 1 0
+-----------------+-----+-----+--+------+-----+--+--+---+---+---+---+
| 同步字 (11/12b) | Ver |Layer| P|Bitrate| Freq|Pd|Pr|ChM|Ext|C|H|E|
+-----------------+-----+-----+--+------+-----+--+--+---+---+---+---+
```

- **同步字（Syncword, bit 31~21）**：连续 11 或 12 个 `1`（`0xFFE` 或 `0xFFF`），用于数据流中定位帧边界；
- **MPEG Version (bit 20, 19)**：`00`=MPEG-2.5, `10`=MPEG-2, `11`=MPEG-1；
- **Layer (bit 18, 17)**：`01`=Layer III (MP3), `10`=Layer II, `11`=Layer I；
- **Protection (bit 16)**：`0`=包含 16-bit CRC 校验字段，`1`=无 CRC；
- **Bitrate Index (bit 15~12)**：码率查表索引（如 128 kbps, 192 kbps, 320 kbps 等）；
- **Sampling Frequency (bit 11, 10)**：采样率查表索引（`00`=44.1kHz, `01`=48kHz, `10`=32kHz）；
- **Padding bit (bit 9)**：填充位。若置 1，本帧长度增加 1 字节（用于调整采样率与码率非整数倍时的平均速率）；
- **Channel Mode (bit 7, 6)**：`00`=立体声 Stereo, `01`=联合立体声 Joint Stereo, `10`=双声道 Dual Channel, `11`=单声道 Mono。

---

### 2.2 变长帧长度计算公式

播放器顺序读取 MP3 流时，每解析完一个 4 字节帧头，即可算出当前帧在物理文件中的字节数：

$$\text{Frame Length (Bytes)} = \left\lfloor \frac{144 \times \text{Bitrate (bps)}}{\text{Sample Rate (Hz)}} \right\rfloor + \text{Padding}$$

> **示例**：码率 128 kbps、采样率 44.1 kHz、`Padding = 0` 时：
> $$\text{Length} = \left\lfloor \frac{144 \times 128000}{44100} \right\rfloor + 0 = 417\text{ 字节}$$

---

## 3. 位库技术 (Bit Reservoir)

在恒定码率（CBR）下，各帧分配到的字节大小是固定的。但音频信号的复杂度随时间剧烈变化（平缓单音所需比特少，交响乐突发瞬态所需比特多）。

```
Frame N-1 (平缓信号, 消耗少) ──> 将剩余未用的比特借存至【位库 Bit Reservoir】
                                               │
                                               ▼
Frame N   (复杂瞬态, 需求大) <── 从位库借入额外比特, 突破 CBR 单帧容量限制
```

- **主数据负偏移（`main_data_begin`）**：
  边信息（Side Info）中包含一个 9-bit 字段 `main_data_begin`，指示当前帧的哈夫曼主数据向前回退了多少字节。解码器在解析当前帧时，必须从滑动历史缓冲区中提取对应偏移的数据。

---

## 4. MP3 完整解码流水线

```mermaid
graph TD
    Bitstream[MP3 比特流] --> Sync[同步字 0xFFE 定位 & 帧头解析]
    Sync --> SideInfo[解析边信息 main_data_begin & 比例因子]
    SideInfo --> Reservoir[位库拼接重组 Main Data]
    Reservoir --> Huffman[哈夫曼熵解码 576 频域系数]
    Huffman --> Dequant[非线性反量化 xr = sign * |ix|^(4/3) * 2^(gain)]
    Dequant --> Stereo[立体声联合解码 MS / Intensity Stereo]
    Stereo --> IMDCT[IMDCT 频域到时域变换 36/12点]
    IMDCT --> Synthesis[多相综合滤波器组 Polyphase Filterbank 32子带]
    Synthesis --> PCM[输出 16-bit PCM 采样点]
```

1. **反量化（Dequantization）**：将哈夫曼解码出的整数系数还原为浮点频域谱线；
2. **IMDCT 逆变换**：结合长窗（高频分辨率，平稳信号）与短窗（高时间分辨率，突发瞬态，抑制预回声）将频域变换回时域子带样点；
3. **多相滤波合成**：将 32 个子带信号重构合成连续的 PCM 波形。

---

## 5. 总结

1. **帧独立性**：每帧包含完整 32 位同步头，支持从任意位置开始 Seek 与重同步；
2. **帧长可算**：依据比特率、采样率与 Padding 标志即可计算单帧跨度；
3. **位库弹性**：通过 `main_data_begin` 实现 CBR 框架下的局部动态比特借调。
