from npu_tiling_scheduler import calculate_npu_tiling

def test_schedule():
    Tm, Tn, Tk, sram = calculate_npu_tiling(2048, 2048, 2048)
    assert sram <= 1024 * 1024
    print("✅ NPU Tiling Schedule Verified Successfully!")

if __name__ == "__main__":
    test_schedule()
