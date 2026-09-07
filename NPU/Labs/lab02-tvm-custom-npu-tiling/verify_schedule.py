from npu_tiling_scheduler import calculate_npu_tiling

def test_schedule():
    result = calculate_npu_tiling(2048, 2048, 2048)
    assert result is not None
    assert result["sram_bytes"] <= 1024 * 1024
    assert result["padding_efficiency"] == 1.0
    print("PASS: teaching model capacity and tail checks (not hardware timing)")

if __name__ == "__main__":
    test_schedule()
