---
layout: post
title: "FFmpeg 源码编译与常用工程处理"
subtitle: "从 GPL/Non-Free 依赖配置、双遍响度均衡到 HLS 多码率切片脚本"
date: 2023-10-15
redirect_from:
  - /2022/03/11/ffmpeg-install-and-common-workflows/
author: Yvain Zhang
header-img: "img/post-bg-debug.png"
series: "技术"
tags:
  - 多媒体
  - FFmpeg
  - 源码编译
  - 工具链
---

在多媒体处理或嵌入式设备开发中，直接使用 Linux 发行版官方仓库（`apt install ffmpeg`）安装的预编译包有时无法满足特定需求。

常见原因包括：
1. **部分高质量编解码库未启用**：受开源许可证限制，官方二进制包通常默认未集成 `libfdk-aac`（Fraunhofer AAC 库）；
2. **硬件编解码支持不全**：未开启特定平台的硬件加速模块（如 VAAPI、NVENC 或 QSV）；
3. **定制化构建需求**：需要精简无用格式和滤镜以减小运行时动态库体积。

本文梳理 FFmpeg 源码编译的标准配置步骤，并提供日常高频音频处理与 HLS 切片脚本。

---

## 1. 源码编译与依赖配置

### 1.1 安装编译依赖 (Ubuntu / Debian)

> **关于 `libfdk-aac` 的说明**：由于 Fraunhofer FDK AAC 许可证与 GPL 冲突，在 Ubuntu 上需先启用 `multiverse` 软件源（Debian 上为 `non-free`），或从源码克隆编译 `fdk-aac`。若仅需常规 AAC 编码，可直接使用 FFmpeg 内置的 `-c:a aac` 编码器。

```bash
# 启用 multiverse 仓库 (Ubuntu)
sudo add-apt-repository multiverse
sudo apt update

# 基础编译工具
sudo apt install -y build-essential yasm nasm cmake git pkg-config

# 常用编解码库
sudo apt install -y \
    libx264-dev \
    libx265-dev \
    libfdk-aac-dev \
    libmp3lame-dev \
    libopus-dev \
    libvpx-dev \
    libssl-dev \
    libva-dev libdrm-dev
```

---

### 1.2 `./configure` 编译配置示例

```bash
git clone https://git.ffmpeg.org/ffmpeg.git -b release/6.1 --depth 1
cd ffmpeg

./configure \
    --prefix=/usr/local/ffmpeg \
    --enable-gpl \
    --enable-nonfree \
    --enable-version3 \
    --enable-shared \
    --enable-pic \
    --enable-pthreads \
    --enable-openssl \
    --enable-libx264 \
    --enable-libx265 \
    --enable-libfdk-aac \
    --enable-libmp3lame \
    --enable-libopus \
    --enable-libvpx \
    --enable-vaapi \
    --disable-debug

make -j$(nproc)
sudo make install

# 更新动态库寻址缓存
echo "/usr/local/ffmpeg/lib" | sudo tee /etc/ld.so.conf.d/ffmpeg.conf
sudo ldconfig
export PATH="/usr/local/ffmpeg/bin:$PATH"
```

---

## 2. 常用工程处理脚本

### 2.1 批量音频转 16kHz 16-bit 单声道 PCM

常用于语音识别（ASR）或算法评测前的数据标准化：

```bash
#!/bin/bash
for file in *.wav *.mp3 *.m4a *.aac; do
    [ -e "$file" ] || continue
    filename="${file%.*}"
    ffmpeg -y -i "$file" \
        -ac 1 \
        -ar 16000 \
        -f s16le \
        -acodec pcm_s16le \
        "${filename}_16k.pcm"
done
```

---

### 2.2 EBU R128 响度标准化 (单遍 vs 双遍)

#### 单遍动态调整 (适合实时流或快速处理)
```bash
ffmpeg -i input.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -b:a 128k output.m4a
```

#### 双遍精确标准化 (2-Pass Loudnorm，适合发布级音频)
1. **Pass 1: 扫描并输出实测统计 JSON**
   ```bash
   ffmpeg -i input.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null -
   ```
2. **Pass 2: 传入实测参数执行线性增益调整**
   ```bash
   ffmpeg -i input.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11:\
   measured_I=-23.5:\
   measured_TP=-3.2:\
   measured_LRA=8.4:\
   measured_thresh=-34.0:\
   offset=0.2:linear=true" -c:a aac -b:a 128k normalized.m4a
   ```

---

### 2.3 HLS 多码率自适应切片脚本

通过 `filter_complex` 同时生成 720p 与 1080p 两个变体流，并输出主播放列表（`master.m3u8`）：

```bash
#!/bin/bash
INPUT="input_1080p.mp4"
OUTDIR="hls_output"
mkdir -p "$OUTDIR"

ffmpeg -i "$INPUT" \
    -filter_complex \
    "[0:v]split=2[v1][v2]; \
     [v1]scale=w=1280:h=720[v1out]; \
     [v2]scale=w=1920:h=1080[v2out]; \
     [0:a]asplit=2[a1][a2]" \
    -map "[v1out]" -c:v:0 libx264 -b:v:0 1500k -maxrate:v:0 1800k -bufsize:v:0 3000k \
    -map "[v2out]" -c:v:1 libx264 -b:v:1 3500k -maxrate:v:1 4000k -bufsize:v:1 7000k \
    -map "[a1]" -c:a:0 aac -b:a:0 128k \
    -map "[a2]" -c:a:1 aac -b:a:1 192k \
    -f hls \
    -hls_time 6 \
    -hls_playlist_type vod \
    -hls_flags independent_segments \
    -master_pl_name master.m3u8 \
    -var_stream_map "v:0,a:0 v:1,a:1" \
    "$OUTDIR/stream_%v.m3u8"
```

---

## 3. 使用建议

1. **优先考虑 `-c copy`**：若仅调整封装格式、提取音轨或粗略截取，避免触发重编码以节约计算资源并保持原始音画质；
2. **明确输出参数**：转码前确认目标播放设备所支持的编码格式、最大码率与声道布局；
3. **定位问题善用帮助**：可通过 `ffmpeg -h encoder=libx264` 或 `ffmpeg -h filter=loudnorm` 查看当前版本支持的具体参数与默认值。
