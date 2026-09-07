import math

def calculate_npu_tiling(M, N, K, sram_capacity_bytes=1024*1024, elem_bytes=2):
    """
    为给定矩阵尺寸和片上 SRAM 容量计算最佳 Tm, Tn, Tk 切分
    Double Buffering 约束: 2 * (Tm*Tk + Tk*Tn + Tm*Tn) * elem_bytes <= sram_capacity_bytes
    """
    best_tiling = None
    max_mac_efficiency = 0.0

    for Tm in [16, 32, 64, 128]:
        for Tn in [16, 32, 64, 128]:
            for Tk in [16, 32, 64, 128]:
                needed_sram = 2 * (Tm * Tk + Tk * Tn + Tm * Tn) * elem_bytes
                if needed_sram <= sram_capacity_bytes:
                    efficiency = (Tm * Tn * Tk) / (needed_sram + 1e-5)
                    if efficiency > max_mac_efficiency:
                        max_mac_efficiency = efficiency
                        best_tiling = (Tm, Tn, Tk, needed_sram)

    return best_tiling

if __name__ == "__main__":
    M, N, K = 4096, 4096, 4096
    Tm, Tn, Tk, sram_used = calculate_npu_tiling(M, N, K)
    print(f"Matrix ({M}x{N}x{K}) Optimal Tiling: Tm={Tm}, Tn={Tn}, Tk={Tk}")
    print(f"SRAM Usage (Double Buffering): {sram_used / 1024:.2f} KB / 1024 KB")
