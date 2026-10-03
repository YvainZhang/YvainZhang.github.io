---
layout: post
title: "FLAC 无损音频格式与压缩原理"
subtitle: "文件结构、预测残差与 Golomb-Rice 编码"
date: 2022-12-11
redirect_from:
  - /2021/07/14/flac-format-and-lossless-compression/
  - /2021/05/23/flac-format-and-lossless-compression/
author: Yvain Zhang
header-img: "img/post-bg-os-metro.jpg"
series: "技术"
tags:
  - 多媒体
  - 音频
  - FLAC
  - 无损压缩
---

FLAC（Free Lossless Audio Codec，自由无损音频编解码器）是开源无损音频格式。它保存预测参数和残差，解码后可逐样点还原原始 PCM。压缩比例取决于音源，不能把某个比例当作所有文件的固定结果。

编码器需要选择预测方式和参数，解码器则按已给出的参数重建样点，计算量通常更小。嵌入式平台是否能实时解码，仍要结合采样率、位深、声道数和处理器性能评估。

---

## 1. FLAC 文件物理结构

标准的 FLAC 文件由 **4 字节魔数 + 若干 METADATA 元数据块 + 连续的音频数据帧（Audio Frames）** 构成：

```
+───────────+───────────────────────+───────────────────────+──────────────────────────────+
| 魔数 "fLaC"| METADATA: STREAMINFO  | 可选 METADATA 块序列   |       音频数据帧序列         |
| (4 字节)  | (必选首块，34 字节)   | (SEEKTABLE/PICTURE等) | [Frame 0][Frame 1]...[FrameN]|
+───────────+───────────────────────+───────────────────────+──────────────────────────────+
```

### 1.1 STREAMINFO（核心流属性块）

STREAMINFO 是紧随 `fLaC` 魔数后的第一个元数据块，记录全局解码所需的基础参数：
- **Block Size 范围**：最小与最大采样块大小（以 sample 为单位，常见 4096）；
- **Frame Size 范围**：最小与最大帧物理字节数；
- **音频参数**：采样率（20 bit）、声道数（3 bit）、量化位深（5 bit，支持 4~32 bit）；
- **总采样数（36 bit）**：记录整首音频的采样点总数，用于计算播放总时长；
- **原始 PCM MD5（128 bit）**：整首未压缩 PCM 数据的 MD5 校验和，用于在解码完成时校验数据完整性。

### 1.2 常用可选元数据块 (Metadata Blocks)
- **`SEEKTABLE`**：包含多个定位点（Seek Point），减少定位目标帧时的扫描量；
- **`VORBIS_COMMENT`**：UTF-8 键值对（`TITLE=...`, `ARTIST=...`），用于存储歌曲标签；
- **`CUESHEET`**：存储 CD 音轨目录与分轨索引；
- **`PICTURE`**：内嵌专辑封面图像。

---

## 2. FLAC 音频帧 (Frame) 与子帧 (Subframe)

FLAC 的音频数据按帧组织，每一帧独立自包含，帧内按声道划分为子帧（Subframe）：

```
+───────────────────────────────────────────────────────────+────────────────+
| 帧头 (Frame Header): 14b 同步字 0x3FFE + 块长/采样率/CRC-8 |  CRC-16 帧尾   |
+─────────────────────────────┬─────────────────────────────+────────────────+
| 子帧 0 (Left / Mid 声道)    | 子帧 1 (Right / Side 声道)  | (字节对齐补 0) |
+─────────────────────────────┴─────────────────────────────+────────────────+
```

---

## 3. FLAC 四大无损压缩阶段

常见的 FLAC 编码过程可以按下面几个步骤理解：

```mermaid
graph LR
    PCM[原始 PCM 样点] --> Stereo[1. 声道去相关: Mid/Side 变换]
    Stereo --> Predict[2. 信号预测: 定阶预测 / LPC 线性预测]
    Predict --> Residual[3. 残差计算: e_t = x_t - p_t]
    Residual --> Entropy[4. 熵编码: Golomb-Rice 变长编码]
    Entropy --> Bitstream[输出无损压缩比特流]
```

### 3.1 第一级：声道间去相关 (Mid/Side Stereo)
双声道音乐中，左右声道通常包含大量相似内容。FLAC 支持将左（L）右（R）声道转换为中间声道（Mid）与差异声道（Side）：
$$\text{Mid} = \frac{L + R}{2}, \quad \text{Side} = L - R$$
左右声道相关性较强时，差异声道的数值范围往往更小，后续编码可能需要更少的比特。

### 3.2 第二级与第三级：信号预测与残差计算
FLAC 提供四种子帧编码模式：
1. **Constant**：该声道所有样点为常量（如完全静音），仅用一个值表示；
2. **Verbatim**：纯裸流直通（不可预测的白噪声时使用）；
3. **Fixed Linear Predictor（固定多项式预测）**：
   使用 0~4 阶固定差分预测公式（如 1 阶 $p(t) = x(t-1)$，2 阶 $p(t) = 2x(t-1) - x(t-2)$），计算开销极低；
4. **LPC (Linear Predictive Coding, 自适应线性预测)**：
   编码器可用 Levinson-Durbin 等算法求取线性预测系数 $a_k$，并选择预测阶数：
   $$p(t) = \sum_{k=1}^{M} a_k \cdot x(t-k)$$
   预测值与实际值相减得到**残差信号（Residual Signal）**：
   $$e(t) = x(t) - p(t)$$

### 3.3 第四级：Golomb-Rice 残差熵编码
残差信号呈以 0 为中心的高度集中双指数分布（拉普拉斯分布）。FLAC 使用 **Golomb-Rice 编码**：
- 将残差值 $e$ 除以 $2^k$，商用一元码（Unary Code）表示，余数用 $k$ 位的二进制补码表示；
- 编码器调整参数 $k$，比较不同参数下的编码长度。

---

## 4. 总结

FLAC 的无损性来自残差保存和可逆重建，并不要求预测值完全准确。分析文件时先读取 `STREAMINFO`，确认采样参数和块长；实现解码器时还需要处理帧校验、定位以及整数运算范围。
