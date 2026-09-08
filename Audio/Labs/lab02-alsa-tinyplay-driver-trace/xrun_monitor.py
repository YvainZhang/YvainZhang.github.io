#!/usr/bin/env python3
"""
ALSA PCM 环形缓冲水位与 XRUN 实时监控器
支持实时解析 /proc/asound/ 状态节点，并提供无 Linux 硬件时的回退模拟仿真模式。
"""
import os
import sys
import time
import re

def parse_proc_status(status_path):
    if not os.path.exists(status_path):
        return None

    data = {}
    with open(status_path, 'r') as f:
        for line in f:
            parts = line.strip().split(':')
            if len(parts) >= 2:
                key = parts[0].strip()
                val = parts[1].strip()
                data[key] = val
    return data

def render_watermark_bar(level, max_level=4096, width=24):
    ratio = max(0.0, min(1.0, level / float(max_level)))
    filled = int(round(ratio * width))
    bar = "█" * filled + "░" * (width - filled)
    pct = ratio * 100.0
    return f"[{bar}] {pct:5.1f}% ({level:5d}/{max_level})"

def run_monitor(card=0, device=0, subdevice=0, duration_sec=10.0):
    status_path = f"/proc/asound/card{card}/pcm{device}p/sub{subdevice}/status"
    hw_params_path = f"/proc/asound/card{card}/pcm{device}p/sub{subdevice}/hw_params"

    print("=================================================================")
    print("   Audio Lab 02: Linux ALSA RingBuffer & XRUN Live Monitor       ")
    print("=================================================================")
    print(f"Target Proc Node: {status_path}\n")

    if not os.path.exists(status_path):
        print(f"[Notice] Proc path {status_path} does not exist.")
        print("[Notice] Running in SIMULATION MODE to demonstrate ALSA RingBuffer & XRUN mechanics...\n")
        run_simulation()
        return

    buffer_size = 4096
    if os.path.exists(hw_params_path):
        with open(hw_params_path, 'r') as f:
            for line in f:
                if 'buffer_size' in line:
                    m = re.search(r'\d+', line)
                    if m:
                        buffer_size = int(m.group(0))

    start_time = time.time()
    while time.time() - start_time < duration_sec:
        info = parse_proc_status(status_path)
        if not info:
            print("Device is closed / idle.")
            time.sleep(0.5)
            continue

        state = info.get('state', 'UNKNOWN')
        hw_ptr = int(info.get('hw_ptr', '0'))
        appl_ptr = int(info.get('appl_ptr', '0'))
        buffered_frames = appl_ptr - hw_ptr

        bar_str = render_watermark_bar(buffered_frames, max_level=buffer_size)
        ts = time.strftime("%H:%M:%S")

        if state == "XRUN":
            print(f"[{ts}] !! ALSA STATE: XRUN DETECTED !! hw_ptr={hw_ptr}, appl_ptr={appl_ptr}, diff={buffered_frames}")
        else:
            print(f"[{ts}] State: {state:<8} | Watermark: {bar_str} | hw_ptr: {hw_ptr} | appl_ptr: {appl_ptr}")

        time.sleep(0.2)

def run_simulation():
    # 模拟 4096 帧缓冲，Period 为 1024 帧
    buffer_size = 4096
    period_size = 1024
    hw_ptr = 0
    appl_ptr = 2048 # 初始填充 2 个 Period
    sim_steps = [
        ("NORMAL_PLAYBACK", 8),
        ("CPU_STALL_INJECTION", 6), # 停止应用填充，模拟 CPU 调度打架
        ("XRUN_TRIGGERED", 4)
    ]

    print(f"Buffer Size: {buffer_size} frames | Period Size: {period_size} frames\n")

    for phase, steps in sim_steps:
        for i in range(steps):
            if phase == "NORMAL_PLAYBACK":
                hw_ptr += 256
                appl_ptr += 256 # 应用程序及时填充
                state = "RUNNING"
            elif phase == "CPU_STALL_INJECTION":
                hw_ptr += 256   # 硬件 DMA 持续抽水
                # appl_ptr 不动 (模拟用户态进程被挂起/饥饿)
                state = "RUNNING" if (appl_ptr - hw_ptr) > 0 else "XRUN"
            else:
                hw_ptr = hw_ptr # 硬件停转
                state = "XRUN"

            diff = max(0, appl_ptr - hw_ptr)
            bar_str = render_watermark_bar(diff, max_level=buffer_size)
            ts = time.strftime("%H:%M:%S")

            if state == "XRUN":
                print(f"[{ts}] !! [ALERT] Underrun Occurred! State=XRUN | Watermark: {bar_str} | hw_ptr={hw_ptr}, appl_ptr={appl_ptr}")
            else:
                print(f"[{ts}] Phase: {phase:<19} | State: {state:<7} | Watermark: {bar_str}")

            time.sleep(0.15)

if __name__ == "__main__":
    run_monitor()
