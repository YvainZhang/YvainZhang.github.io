#!/usr/bin/env bash
# =================================================================
#  Audio Lab 02: Linux ALSA 虚拟声卡与 XRUN 欠载自动化测试脚本
# =================================================================

set -e

WAV_FILE="test_tone_48k.wav"

echo "=== 步骤 1: 检查并生成 48kHz 正弦测试音频 ==="
python3 generate_tone.py "$WAV_FILE"

echo ""
echo "=== 步骤 2: 检查 Linux snd-dummy 驱动环境 ==="
if [ "$(uname)" != "Linux" ]; then
    echo "[Notice] 当前系统非 Linux ($(uname))，直接启动跨平台环形缓冲监控仿真器:"
    python3 xrun_monitor.py
    exit 0
fi

if ! lsmod | grep -q "snd_dummy"; then
    echo "[Info] 加载内核虚拟声卡模块: sudo modprobe snd-dummy"
    sudo modprobe snd-dummy || { echo "[Error] 无法加载虚拟声卡，停止测试"; exit 1; }
fi

echo ""
echo "=== 步骤 3: 寻找 dummy 声卡设备号 ==="
CARD_ID=$(cat /proc/asound/cards | grep -i "dummy" | awk '{print $1}' | head -n 1 || echo "")
if [ -z "$CARD_ID" ]; then
    echo "[Error] 未找到 dummy 虚拟声卡；禁止回退到可能连接扬声器的 Card 0"
    exit 1
fi

echo "使用声卡 Card: $CARD_ID"

echo ""
echo "=== 步骤 4: 后台启动 tinyplay / aplay 播放 ==="
if which tinyplay > /dev/null 2>&1; then
    tinyplay "$WAV_FILE" -D "$CARD_ID" -d 0 -p 128 -n 2 &
    PLAY_PID=$!
elif which aplay > /dev/null 2>&1; then
    aplay -D "hw:$CARD_ID,0" --period-size=128 --buffer-size=512 "$WAV_FILE" &
    PLAY_PID=$!
else
    echo "[Warn] 未安装 tinyplay 或 aplay，进入纯监控仿真模式"
    python3 xrun_monitor.py
    exit 0
fi

echo "播放器 PID: $PLAY_PID"
cleanup() {
    kill -CONT "$PLAY_PID" 2>/dev/null || true
    kill -TERM "$PLAY_PID" 2>/dev/null || true
    wait "$PLAY_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo ""
echo "=== 步骤 5: 启动实时水位监视 (持续 3 秒正常阶段) ==="
sleep 2

echo ""
echo "=== 步骤 6: 人为冻结播放进程 (SIGSTOP) 制造欠载饥饿 ==="
echo "发送 SIGSTOP 信号暂停进程 PID: $PLAY_PID"
kill -STOP "$PLAY_PID"

echo "等待 1.5 秒让硬件 DMA 耗尽环形缓冲区..."
sleep 1.5

echo ""
echo "=== 步骤 7: 检查内核 PCM 状态节点 ==="
STATUS_FILE="/proc/asound/card$CARD_ID/pcm0p/sub0/status"
if [ -f "$STATUS_FILE" ]; then
    cat "$STATUS_FILE"
    if grep -q 'state:.*XRUN' "$STATUS_FILE"; then
        echo "PASS: 本次观察到 XRUN；不代表真实 DMA 硬件测试"
    else
        echo "[Notice] 未观察到 XRUN，不判定复现成功"
    fi
fi

echo ""
echo "=== 步骤 8: 清理测试进程 ==="
echo "测试结束，由清理钩子恢复并终止本次播放器。"
