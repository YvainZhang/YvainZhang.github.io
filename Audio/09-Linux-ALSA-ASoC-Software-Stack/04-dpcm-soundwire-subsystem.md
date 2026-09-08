# 04 DPCM 与 SoundWire 驱动子系统

## 1. 硬件解决什么问题：DSP 多路动态路由与 SoundWire 现代总线支持

随着现代智能设备普遍引入片上 Audio DSP，传统 ASoC“一个 CPU DAI 严格对应一个 Codec DAI”的点对点刚性模型无法满足复杂声学场景：
1. **DPCM（Dynamic PCM）前后端解耦**：应用程序看到的逻辑声卡是前端（Front-End, FE），而物理输出的 I2S 接口是后端（Back-End, BE）。DSP 内部可能将通话语音动态分发给蓝牙、扬声器或录音回环，前后端采样率各不相同。
2. **SoundWire 总线原生支持**：传统的 I2C+I2S 需要两个独立的驱动子系统。Linux 内核演进了专有的 **SoundWire 总线子系统（`drivers/soundwire/`）**，实现统一的从设备枚举、控制报文打通与多通道音频流绑定。

---

## 2. 硬件微架构与组成：DPCM 前后端架构拓扑

```mermaid
graph LR
    subgraph DPCM_Front_Ends["DPCM 虚拟前端 (Front-Ends, FE)"]
        FE_MEDIA["FE 0: 多媒体放音 (48kHz Stereo)"]
        FE_VOICE["FE 1: 语音通话下行 (16kHz Mono)"]
        FE_NAV["FE 2: 导航提示音 (44.1kHz Stereo)"]
    end

    subgraph DSP_Audio_Hub["Audio DSP 软件混音与动态路由交换矩阵"]
        MIXER_HUB["动态混音器 / ASRC / 声学路由"]
    end

    subgraph DPCM_Back_Ends["DPCM 物理后端 (Back-Ends, BE)"]
        BE_SPK["BE 0: I2S 物理主扬声器 (Smart PA)"]
        BE_BT["BE 1: PCM 物理蓝牙模组"]
        BE_HP["BE 2: SoundWire 耳机 Codec"]
    end

    FE_MEDIA --> MIXER_HUB
    FE_VOICE --> MIXER_HUB
    FE_NAV --> MIXER_HUB
    MIXER_HUB --> BE_SPK
    MIXER_HUB --> BE_BT
    MIXER_HUB --> BE_HP
```

---

## 3. 软件代码实现：Linux SoundWire 驱动注册规范

```c
// 现代 Linux SoundWire 从设备驱动驱动骨架
static struct sdw_driver my_sdw_codec_driver = {
    .driver = {
        .name = "my-soundwire-codec",
        .pm = &my_sdw_pm_ops,
    },
    .probe = my_sdw_codec_probe,
    .remove = my_sdw_codec_remove,
    .ops = &my_sdw_slave_ops,       // SoundWire 中断与状态回调
    .id_table = my_sdw_id_table,    // 厂商与设备识别码
};
module_sdw_driver(my_sdw_codec_driver);
```
