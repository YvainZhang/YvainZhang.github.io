"""CPU-only arithmetic tests; no hardware performance claims."""

import unittest

from npu_tiling_scheduler import calculate_npu_tiling, evaluate_tile


class TilingTests(unittest.TestCase):
    def test_documented_tail_case(self):
        result = evaluate_tile(130, 70, 129, (64, 64, 128))
        self.assertEqual(result["sram_bytes"], 65536)
        self.assertEqual(result["tile_calls"], 12)
        self.assertEqual(result["useful_macs"], 1173900)
        self.assertEqual(result["physical_macs"], 6291456)
        self.assertAlmostEqual(result["padding_efficiency"], 0.18658638, places=7)

    def test_exact_capacity(self):
        needed = evaluate_tile(16, 16, 16, (16, 16, 16))["sram_bytes"]
        self.assertIsNotNone(calculate_npu_tiling(16, 16, 16, needed, candidates=(16,)))
        self.assertIsNone(calculate_npu_tiling(16, 16, 16, needed - 1, candidates=(16,)))

    def test_accumulator_precision_is_counted(self):
        low = evaluate_tile(64, 64, 64, (64, 64, 64), acc_bytes=2)
        high = evaluate_tile(64, 64, 64, (64, 64, 64), acc_bytes=4)
        self.assertEqual(high["sram_bytes"] - low["sram_bytes"], 64 * 64 * 2)

    def test_shape_changes_selection(self):
        small = calculate_npu_tiling(16, 16, 16)
        large = calculate_npu_tiling(4096, 4096, 4096)
        self.assertEqual(small["tile"], [16, 16, 16])
        self.assertEqual(large["tile"], [128, 128, 128])
        self.assertEqual(large["padding_efficiency"], 1.0)

    def test_invalid_inputs(self):
        for value in (0, -1, 1.5, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_npu_tiling(value, 16, 16)
        with self.assertRaises(ValueError):
            calculate_npu_tiling(16, 16, 16, candidates=())
        with self.assertRaises(ValueError):
            evaluate_tile(16, 16, 16, (16, 16, 16), reserved_bytes=-1)

    def test_pipeline_example(self):
        tiles, load, compute = 8, 30, 50
        self.assertEqual(tiles * (load + compute), 640)
        self.assertEqual(load + compute + (tiles - 1) * max(load, compute), 430)

    def test_gpu_gemm_budget(self):
        m = n = k = 4096
        flops = 2 * m * n * k
        byte_count = 2 * (m * k + k * n + m * n)
        self.assertEqual(flops, 137438953472)
        self.assertEqual(byte_count, 100663296)
        self.assertAlmostEqual(flops / byte_count, 1365.33333333, places=6)


if __name__ == "__main__":
    unittest.main()
