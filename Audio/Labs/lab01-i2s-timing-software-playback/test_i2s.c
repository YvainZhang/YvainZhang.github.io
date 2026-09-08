/* Verify all 32 sample bits and WS cadence in both implemented formats. */
#include <assert.h>
#define main simulator_demo_main
#include "i2s_simulator.c"
#undef main

int main(void) {
    const uint32_t samples[2] = {UINT32_C(0xA5A55A5B), UINT32_C(0x92345679)};
    for (int format = 0; format <= 1; ++format) {
        i2s_tx_hardware_t dev = {0};
        dev.format = (i2s_format_t)format;
        dev.lrck = true;
        bool bclk = true, ws = true, data = false;
        for (int cycle = 0; cycle < 129; ++cycle) {
            i2s_step(&dev, samples[0], samples[1], &bclk, &ws, &data);
            assert(!bclk);
            assert(ws == (bool)((cycle / 32) % 2));
            int index = cycle - (format == I2S_FORMAT_PHILIPS ? 1 : 0);
            if (index >= 0) {
                bool expected = (samples[(index / 32) % 2] >> (31 - index % 32)) & 1U;
                assert(data == expected);
            }
            bool saved = data;
            i2s_step(&dev, samples[0], samples[1], &bclk, &ws, &data);
            assert(bclk && data == saved);
        }
    }
    puts("PASS: I2S/LJ sample bits, WS cadence and rising-edge stability");
    return 0;
}
