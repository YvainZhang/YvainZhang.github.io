# 03 Linux 内核音频调试利器与 Trace

## 1. 硬件解决什么问题：内核运行状态黑盒透明化

在 Linux 系统运行中，内核空间发生的事情（DMA 跑到哪里了？FIFO 此时是否为空？哪个线程被延迟卡住了？）对外是隐蔽的。

熟练掌握 Linux 原生的内核音频洞察工具，是快速定位系统级音频 Bug 的核心内功。

---

## 2. 原厂排查四大命令利器

### 1. `/proc/asound` 状态大本营
```bash
# 查看所有注册声卡与芯片名称
cat /proc/asound/cards

# 实时查看正在运行的 PCM 硬件参数 (采样率/通道/缓冲区大小)
cat /proc/asound/card0/pcm0p/sub0/hw_params

# 查看当前声卡实时运行状态与指针位置 (诊断 XRUN 最直接手段)
cat /proc/asound/card0/pcm0p/sub0/status
# 输出包含:
# state: RUNNING
# hw_ptr: 485120
# appl_ptr: 488192  <-- 两者差值反映当前安全缓冲余量
```

### 2. `ftrace` 跟踪音频线程调度抖动
使用 Linux 原生 ftrace 追踪音频工作线程是否被其他高负载任务抢占：
```bash
# 进入 ftrace 目录
cd /sys/kernel/debug/tracing

# 跟踪调度器切换事件
echo 1 > events/sched/sched_switch/enable
echo 1 > events/sched/sched_wakeup/enable

# 过滤关注特定音频进程 (如 tinyplay 或 audio-hal)
echo $(pidof tinyplay) > set_ftrace_pid

# 开启跟踪
echo 1 > tracing
# ...复现一次断音...
echo 0 > tracing

# 查看追踪日志中发生切换的延迟空隙
cat trace | grep -E "prev_comm=tinyplay" | head -n 30
```

### 3. 用户态极简抓流与注入
在没有复杂播放器时，直接使用编译好的 `tinyplay` 和 `tinycap` 绕开上层框架，直接在底层读写声卡：
```bash
# 从麦克风录制 5 秒钟原始未压缩音频
tinycap /data/record_raw.wav -D 0 -d 0 -c 2 -r 48000 -b 16 -t 5

# 调整底层模拟增益与开关
tinymix
tinymix "DAC Playback Volume" 127
```
