#include <assert.h>
#include <limits.h>
#define main lms_demo_main
#include "fixed_point_lms.c"
#undef main

static int32_t reference_mul(int32_t a, int32_t b) {
    long double value = roundl((long double)a * b / 2147483648.0L);
    if (value > INT32_MAX) return INT32_MAX;
    if (value < INT32_MIN) return INT32_MIN;
    return (int32_t)value;
}

int main(void) {
    const int32_t values[] = {INT32_MIN, INT32_MIN + 1, -1073741824, -1,
                             0, 1, 1073741824, INT32_MAX - 1, INT32_MAX};
    for (size_t i = 0; i < sizeof(values)/sizeof(values[0]); ++i)
        for (size_t j = 0; j < sizeof(values)/sizeof(values[0]); ++j)
            assert(qmul32(values[i], values[j]) == reference_mul(values[i], values[j]));
    assert(qmul32(INT32_MIN, INT32_MIN) == INT32_MAX);
    assert(qmul32(1, 1073741824) == 1);
    assert(qmul32(-1, 1073741824) == -1);
    assert(qadd32(INT32_MAX, 1) == INT32_MAX);
    assert(qsub32(INT32_MIN, 1) == INT32_MIN);
    int32_t x[FILTER_TAPS], w[FILTER_TAPS], history[FILTER_TAPS] = {0};
    for (int i = 0; i < FILTER_TAPS; ++i) { x[i] = INT32_MIN; w[i] = INT32_MIN; }
    assert(q31_dot(x, w) == INT32_MAX);
    for (int i = 0; i < FILTER_TAPS; ++i) w[i] = INT32_MAX;
    assert(q31_dot(x, w) == INT32_MIN);
    for (int i = 0; i < FILTER_TAPS; ++i) w[i] = 0;
    for (int i = 0; i < 100; ++i) assert(lms_step(0, 0, history, w) == 0);
    for (int i = 0; i < FILTER_TAPS; ++i) assert(w[i] == 0);
    puts("PASS: Q31 boundaries, half-way rounding, saturated dot and silence");
    return 0;
}
