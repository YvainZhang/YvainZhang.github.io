# 可复现实战代码实验（Audio Labs）

本目录包含三个紧扣芯片微架构、Linux 内核音频驱动与定点 DSP 声学算法的可编译、可复现实战工程实验：

验证边界：Lab 01 的 I2S/LJ 位序与槽宽有 CPU 回归测试，不实现右对齐或真实电气时序；Lab 02 需要 Linux 虚拟声卡，不能用软件模拟输出代替实测；Lab 03 是待目标平台进一步验证的教学 LMS 模型，不代表产品级 AEC。另可运行 `python3 -B Audio/Labs/test_audio_budget.py` 检查 PCM/时钟预算。

---

## 实验体系全景图

```
+---------------------------------------------------------------------------------+
|                               Audio Labs 进阶路线                               |
+---------------------------------------------------------------------------------+
| [Lab 01: 硬件协议层]                                                            |
|  I2S 移位微架构与 VCD 波形导出                                                   |
|  - 纯 C 演示标准 I2S / 左对齐的数字位序模型                                      |
|  - 输出标准 VCD (Value Change Dump) 数字波形并在 GTKWave 中查看高低电平跳变     |
+---------------------------------------+-----------------------------------------+
                                        |
                                        v
+---------------------------------------+-----------------------------------------+
| [Lab 02: 内核驱动层]                                                            |
|  Linux ALSA 环形缓冲与 XRUN 欠载实战                                            |
|  - 挂载 Linux snd-dummy 虚拟声卡驱动与 TinyALSA 流式播放                        |
|  - 实时解析 /proc/asound 硬件指针 (hw_ptr) 与应用指针 (appl_ptr) 动态差值       |
|  - 编写自动化注入脚本人为制造调度饥饿，捕获 XRUN 现场与内核水位告警             |
+---------------------------------------+-----------------------------------------+
                                        |
                                        v
+---------------------------------------+-----------------------------------------+
| [Lab 03: 声学算法层]                                                            |
|  定点 DSP Q31 LMS 回声消除算子与 ERLE 收敛评测                                  |
|  - 纯整型 Q31 饱和乘加器模拟音频 DSP 运算行为                                   |
|  - 注入真实 16 抽头声学房间冲激响应 (RIR) 与近端语音扰动                        |
|  - 实时计算 ERLE (回声回损增益 dB) 并输出自适应滤波器收敛曲线                   |
+---------------------------------------------------------------------------------+
```

---

## 实验环境与工具链依赖

| 工具 / 库 | 最低版本要求 | 用途说明 | 安装命令（Ubuntu/Debian 或 macOS） |
| :--- | :--- | :--- | :--- |
| **GCC / Clang** | C99 兼容 | 编译 Lab 01、Lab 03 的 C 语言仿真程序 | `sudo apt install build-essential` / Xcode CLT |
| **Make** | GNU Make 3.8+ | 一键编译与自动化测试执行 | 系统自带 |
| **Python 3** | Python 3.8+ | 生成精密测试音频与动态监控数据解析 | `python3 --version` |
| **GTKWave** | 3.3+ | 查看 Lab 01 生成的 `i2s_trace.vcd` 逻辑波形 | `sudo apt install gtkwave` / `brew install --cask gtkwave` |
| **ALSA 工具栈** | alsa-utils / tinyalsa | Lab 02 驱动与播放测试工具 | `sudo apt install alsa-utils libasound2-dev` |

---

## 实验索引与目录结构

1. [Lab 01: I2S 协议时序仿真与软件音频波形生成](lab01-i2s-timing-software-playback/README.md)
   - 核心代码：`i2s_simulator.c`、`Makefile`
   - 生成目标：`i2s_sim` 执行文件、`i2s_trace.vcd` 逻辑分析仪波形
2. [Lab 02: Linux ALSA 虚拟声卡驱动与 TinyALSA 环形缓冲跟踪](lab02-alsa-tinyplay-driver-trace/README.md)
   - 核心代码：`generate_tone.py`、`xrun_monitor.py`、`run_xrun_test.sh`、`Makefile`
   - 测试目标：捕获 DMA 环形缓冲水位推进并触发并分析 XRUN
3. [Lab 03: 定点 DSP 算子实现——LMS 自适应回声消除滤波](lab03-fixed-point-dsp-aec-filter/README.md)
   - 核心代码：`fixed_point_lms.c`、`plot_erle.py`、`Makefile`
   - 验证目标：验证 Q31 定点 LMS 算法在声学回声消除中的收敛性能，达成 ERLE $> 25\text{ dB}$
