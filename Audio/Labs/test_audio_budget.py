"""CPU-only checks for the documented PCM/clock model; no audio device access."""
import unittest


class AudioBudgetTests(unittest.TestCase):
    def test_pcm_memory_and_serial_clock_are_distinct(self):
        fs, channels, sample_bytes, slot_bits = 48000, 2, 4, 32
        self.assertEqual(fs * channels * sample_bytes, 384000)
        self.assertEqual(fs * channels * slot_bits, 3072000)
        self.assertEqual(fs * channels * 24, 2304000)

    def test_period_and_ring(self):
        self.assertEqual(240 * 2 * 4, 1920)
        self.assertEqual(240 * 4 * 2 * 4, 7680)
        self.assertAlmostEqual(240 / 48000, 0.005)
        self.assertAlmostEqual(960 / 48000, 0.020)
        self.assertEqual(48000 / 240, 200)

    def test_qos_and_period_sensitivity(self):
        for frames, budget in [(16, 283.333333), (32, 616.666667),
                               (64, 1283.333333), (128, 2616.666667)]:
            self.assertAlmostEqual(frames / 48000 * 1e6 - 50, budget, places=5)
        self.assertAlmostEqual(48000 / 16 * 30e-6 * 100, 9.0)
        self.assertAlmostEqual(48000 / 240 * 10e-6 * 100, 0.2)

    def test_battery_sensitivity(self):
        for wakes, expected in [(0, 133.81), (100, 133.01),
                                (1000, 126.24), (10000, 83.66)]:
            power = (804.4 + wakes * 0.3 * 15000 / 86400) / 0.85 + 76
            self.assertAlmostEqual(136800 / power, expected, places=2)
        for efficiency, expected in [(0.70, 110.99), (0.85, 133.01), (0.95, 147.38)]:
            power = (804.4 + 100 * 0.3 * 15000 / 86400) / efficiency + 76
            self.assertAlmostEqual(136800 / power, expected, places=2)

    def test_clock_drift(self):
        drift_frames_per_second = 48000 * 100 / 1000000
        self.assertAlmostEqual(drift_frames_per_second, 4.8)
        self.assertAlmostEqual(480 / drift_frames_per_second, 100)


if __name__ == '__main__':
    unittest.main()
