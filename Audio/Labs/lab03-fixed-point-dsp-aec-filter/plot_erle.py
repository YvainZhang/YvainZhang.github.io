#!/usr/bin/env python3
"""
解析 erle_data.csv 并在终端直接绘制 ASCII 收敛曲线
"""
import os
import sys

def plot_ascii_erle(csv_path="erle_data.csv", width=60, height=15):
    if not os.path.exists(csv_path):
        print(f"File {csv_path} not found. Run ./lms_test first.")
        return

    samples = []
    erles = []
    with open(csv_path, 'r') as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                samples.append(int(parts[0]))
                erles.append(float(parts[3]))

    if not erles:
        print("No valid data found in CSV.")
        return

    min_val = min(erles)
    max_val = max(erles)

    print("\n=================================================================")
    print("   Lab 03: LMS Acoustic Echo Cancellation Convergence Curve    ")
    print("=================================================================")
    print(f"Total Samples: {len(samples)*10} | ERLE Range: {min_val:.1f} dB ~ {max_val:.1f} dB\n")

    # 绘制 ASCII 字符图
    grid = [[" " for _ in range(width)] for _ in range(height)]

    for col in range(width):
        idx = int(col * (len(erles) - 1) / (width - 1))
        val = erles[idx]
        norm = (val - min_val) / (max_val - min_val + 1e-6)
        row = height - 1 - int(norm * (height - 1))
        grid[row][col] = "█"

    for r in range(height):
        db_level = max_val - r * (max_val - min_val) / (height - 1)
        row_str = "".join(grid[r])
        print(f"{db_level:5.1f} dB | {row_str}")

    print(" " * 8 + "+" + "-" * width)
    print(" " * 9 + "0" + " " * (width - 12) + f"{samples[-1]} samples\n")
    print(f"Convergence Result: Rapid climb from {min_val:.1f} dB to {max_val:.1f} dB!")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "erle_data.csv"
    plot_ascii_erle(path)
