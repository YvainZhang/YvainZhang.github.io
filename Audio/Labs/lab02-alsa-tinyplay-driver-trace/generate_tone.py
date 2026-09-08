#!/usr/bin/env python3
"""
生成标准 16-bit 48kHz 双声道正弦波测试 WAV 文件
"""
import wave
import struct
import math
import sys

def generate_sine_wave(filename="test_tone_48k.wav", duration_sec=5.0, freq=1000.0, sample_rate=48000, amplitude=0.8):
    n_channels = 2
    sampwidth = 2 # 16-bit = 2 bytes
    n_samples = int(duration_sec * sample_rate)
    max_amp = int(32767 * amplitude)

    print(f"Generating {filename}: {duration_sec}s, {sample_rate}Hz, {n_channels} channels, {freq}Hz sine tone...")
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(n_channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(n_samples):
            # 左声道 1000Hz, 右声道 1000Hz (反相以形成立体声测试向量)
            val_l = int(max_amp * math.sin(2.0 * math.pi * freq * i / sample_rate))
            val_r = int(max_amp * math.cos(2.0 * math.pi * freq * i / sample_rate))
            frames.extend(struct.pack('<hh', val_l, val_r))

        wav_file.writeframes(frames)

    print(f"Generated {filename} successfully ({len(frames)} PCM bytes).")

if __name__ == "__main__":
    out_name = sys.argv[1] if len(sys.argv) > 1 else "test_tone_48k.wav"
    generate_sine_wave(out_name)
