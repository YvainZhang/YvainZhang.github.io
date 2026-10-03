# 08 ALSA 环形缓冲与时延模型推演

## 1. 硬件解决什么问题：环形缓冲区水位推进与数学时延模型

在 ALSA 的环形缓冲机制中，`appl_ptr`（应用指针）随应用写入推进，`hw_ptr`（硬件指针）随 DMA 消费推进。应用通常成块写入，硬件则按采样时钟持续消费。

两者之间的距离直接决定了**音频的系统滞后时延（Playback Latency）**。

---

## 2. 环形缓冲水位数学关系推演

```mermaid
graph LR
    subgraph Ring_Buffer_Math["ALSA 环形缓冲区指针分布"]
        HW["硬件播放指针 hw_ptr (由 DMA 中断更新)"]
        APPL["应用写入指针 appl_ptr (由用户态 write 更新)"]
        DIFF["当前未消费音频缓冲量 Delta = appl_ptr - hw_ptr"]
    end
    HW --> DIFF
    APPL --> DIFF
```

### 关键时延公式推导
设采样率为 $f_s$（样点/秒），环形缓冲区总样点数为 $B_{\text{size}}$（Buffer Size），单个 Period 样点数为 $P_{\text{size}}$。
1. **最小系统固有硬件缓冲延迟（Minimum Latency）**：
   当应用态保持缓冲内始终维持至少一个周期的安全数据，防止 DMA 饥饿：
   $$t_{\text{latency, min}} = \frac{P_{\text{size}}}{f_s}$$
2. **最大系统滞后延迟（Maximum Latency）**：
   当应用态将整个环形缓冲区填满时：
   $$t_{\text{latency, max}} = \frac{B_{\text{size}}}{f_s}$$

---

## 3. 典型系统参数量化对比推演表

设采样率 $f_s = 48000\text{ Hz}$：

| 调度策略模式 | Period Size | Buffer Size | 典型 Period 中断周期 | 系统音频端到端缓冲时延 |
| :--- | :--- | :--- | :--- | :--- |
| **超低延迟 (Low Latency / Pro Audio)** | 64 样点 | 128 样点 | **$1.33\text{ ms}$** | **$2.67\text{ ms}$** |
| **标准交互 (Interactive / Game)** | 192 样点 | 768 样点 | **$4.00\text{ ms}$** | **$16.00\text{ ms}$** |
| **常规多媒体 (Standard Linux)** | 1024 样点 | 4096 样点 | **$21.33\text{ ms}$** | **$85.33\text{ ms}$** |
| **深度节能 (Audio Offload / Music)** | 4096 样点 | 32768 样点 | **$85.33\text{ ms}$** | **$682.67\text{ ms}$** |

---

## 4. 架构设计指导准则

推论：
1. **低延迟需要更小的供数间隔**：以 $5\text{ ms}$、$< 256$ 样点和约 2.6 毫秒的配置范围为例，应用需要检查每次唤醒时还剩多少数据，以及计算和调度消耗多少时间。2ms 的抖动是否引起 Underrun，取决于当时缓冲余量。
2. **专业实时系统的系统优化组合拳**：在追求低延迟时，调小 ALSA 参数后，应测量唤醒和执行延迟，再评估 **`PREEMPT_RT`** 与 **`SCHED_FIFO`** 等策略。线程优先级需与中断、驱动和其他实时任务一起安排，不能把 90 以上作为通用配置。
