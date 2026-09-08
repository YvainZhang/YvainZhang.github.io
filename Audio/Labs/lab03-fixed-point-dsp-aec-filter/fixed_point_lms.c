#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <stdbool.h>

#define FILTER_TAPS   32          // 自适应滤波器阶数
#define TOTAL_SAMPLES 2000        // 仿真音频采样点数
#define MU_Q31        0x0A3D70A4  // 教学步长约 0.08；稳定性还取决于输入统计量
#ifndef TARGET_ERLE_DB
#define TARGET_ERLE_DB 25.0
#endif

/**
 * @brief 合成 FIR 回声路径，不是实测房间冲激响应 (RIR)
 * 模拟扬声器发声到麦克风拾音的直达声与早期反射声学路径
 */
static const int32_t TRUE_RIR[FILTER_TAPS] = {
    0x30000000,  // 0: 直达声 (Direct Path, 约 0.375)
    0x18000000,  // 1: 早期反射 1
    0x0C000000,  // 2: 早期反射 2
    0x06000000,  // 3: 反射 3
    0x03000000,  // 4: 反射 4
    0x01800000,  // 5: 反射 5
    0x00C00000,  // 6: 反射 6
    0x00600000,  // 7: 反射 7
    // 其余高阶反射指数衰减
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0
};

/**
 * @brief 硬件级 32 位饱和加法 (Saturating Add)
 */
static inline int32_t qadd32(int32_t a, int32_t b) {
    int64_t res = (int64_t)a + (int64_t)b;
    if (res > 0x7FFFFFFF) return 0x7FFFFFFF;
    if (res < -0x80000000LL) return -0x80000000LL;
    return (int32_t)res;
}

/**
 * @brief 硬件级 32 位饱和减法 (Saturating Sub)
 */
static inline int32_t qsub32(int32_t a, int32_t b) {
    int64_t res = (int64_t)a - (int64_t)b;
    if (res > 0x7FFFFFFF) return 0x7FFFFFFF;
    if (res < -0x80000000LL) return -0x80000000LL;
    return (int32_t)res;
}

/**
 * @brief Q31 乘法：最近舍入，恰好半 LSB 时远离零，最后饱和。
 * 不依赖负数右移或超范围窄化。INT32_MIN * INT32_MIN 饱和为 INT32_MAX。
 */
static inline int32_t qmul32(int32_t a, int32_t b) {
    int64_t prod = (int64_t)a * (int64_t)b;
    int64_t rounded = prod >= 0 ? (prod + INT64_C(1073741824)) / INT64_C(2147483648)
                               : -((-prod + INT64_C(1073741824)) / INT64_C(2147483648));
    if (rounded > INT32_MAX) return INT32_MAX;
    if (rounded < INT32_MIN) return INT32_MIN;
    return (int32_t)rounded;
}

/* Each product is rounded/saturated to Q31 before accumulation. At 32 taps,
 * |sum| <= 32 * 2^31 fits int64_t. This is NOT a full-precision Q62 MAC. */
static int32_t q31_dot(const int32_t *x, const int32_t *w) {
    int64_t sum = 0;
    for (int i = 0; i < FILTER_TAPS; ++i) sum += qmul32(x[i], w[i]);
    if (sum > INT32_MAX) return INT32_MAX;
    if (sum < INT32_MIN) return INT32_MIN;
    return (int32_t)sum;
}

/**
 * @brief 合成线性 FIR 回声生成
 */
static int32_t acoustic_air_path(int32_t x_new, int32_t *air_buf) {
    for (int i = FILTER_TAPS - 1; i > 0; i--) {
        air_buf[i] = air_buf[i - 1];
    }
    air_buf[0] = x_new;

    return q31_dot(air_buf, TRUE_RIR);
}

/**
 * @brief 定点 LMS 自适应回声消除单步处理算子
 * @param x_ref 参考信号 (远端播放信号)
 * @param d_mic 麦克风拾音 (回声 + 近端声音)
 * @param x_buf 历史参考输入滑动窗
 * @param w_taps 自适应权重滤波器系数
 * @return int32_t 残余回声误差信号 e(n)
 */
int32_t lms_step(int32_t x_ref, int32_t d_mic, int32_t *x_buf, int32_t *w_taps) {
    // 1. 滑动参考信号历史缓冲区
    for (int i = FILTER_TAPS - 1; i > 0; i--) {
        x_buf[i] = x_buf[i - 1];
    }
    x_buf[0] = x_ref;

    // 2. 逐乘积舍入的 Q31 点积，64-bit 存储扩展后的 Q31 和。
    int32_t d_hat = q31_dot(x_buf, w_taps);

    // 3. 计算误差信号 e(n) = d(n) - d_hat(n)
    int32_t err = qsub32(d_mic, d_hat);

    // 4. 权重自适应梯度更新: w[i] = w[i] + mu * e(n) * x[n-i]
    int32_t step_factor = qmul32(MU_Q31, err);
    for (int i = 0; i < FILTER_TAPS; i++) {
        int32_t delta = qmul32(step_factor, x_buf[i]);
        w_taps[i] = qadd32(w_taps[i], delta);
    }

    return err;
}

int main(void) {
    int32_t air_buf[FILTER_TAPS] = {0};
    int32_t dsp_x_buf[FILTER_TAPS] = {0};
    int32_t dsp_w_taps[FILTER_TAPS] = {0};

    FILE *csv_fp = fopen("erle_data.csv", "w");
    if (!csv_fp) { perror("erle_data.csv"); return EXIT_FAILURE; }
    fprintf(csv_fp, "sample,mic_power,err_power,erle_db\n");

    printf("=================================================================\n");
    printf("   Audio Lab 03: Fixed-point Q31 LMS Acoustic Echo Cancellation  \n");
    printf("=================================================================\n");
    printf("Filter Configuration: %d Taps, Mu: 0x%08X (Q31)\n", FILTER_TAPS, MU_Q31);
    printf("Synthetic single-talk FIR model, not a room measurement...\n");
    printf("-----------------------------------------------------------------\n");
    printf(" Sample |  Mic Energy   | Residual Error | ERLE (Echo Reduction) \n");
    printf("-----------------------------------------------------------------\n");

    double smooth_mic_pwr = 1.0;
    double smooth_err_pwr = 1.0;

    uint32_t rng = UINT32_C(42); // 固定算法，避免不同 libc 的 rand() 序列差异

    for (int n = 0; n < TOTAL_SAMPLES; n++) {
        // 合成伪随机激励，不声称具有真实语音统计特性。只对无符号数移位。
        rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
        int32_t x_ref = ((int32_t)(rng % UINT32_C(40000)) - 20000) * INT32_C(32768);

        // 经合成 FIR 路径产生回声 d(n)
        int32_t echo = acoustic_air_path(x_ref, air_buf);
        int32_t d_mic = echo; // 单讲环境：麦克风仅拾取扬声器回声

        // 运行定点 LMS 回声消除算子
        int32_t err = lms_step(x_ref, d_mic, dsp_x_buf, dsp_w_taps);

        // 平滑能量统计并计算 ERLE: 10 * log10(P_mic / P_error)
        double cur_mic = (double)d_mic * (double)d_mic;
        double cur_err = (double)err * (double)err;
        smooth_mic_pwr = 0.98 * smooth_mic_pwr + 0.02 * cur_mic;
        smooth_err_pwr = 0.98 * smooth_err_pwr + 0.02 * cur_err;

        double erle_db = 0.0;
        if (smooth_err_pwr > 1e-6) {
            erle_db = 10.0 * log10(smooth_mic_pwr / smooth_err_pwr);
        }

        if (n % 10 == 0 || n == TOTAL_SAMPLES - 1) {
            fprintf(csv_fp, "%d,%.0f,%.0f,%.2f\n", n, smooth_mic_pwr, smooth_err_pwr, erle_db);
        }

        if (n % 200 == 0 || n == TOTAL_SAMPLES - 1) {
            printf(" #%04d  | %12.0f  | %14.0f |     %6.2f dB\n",
                   n, smooth_mic_pwr, smooth_err_pwr, erle_db);
        }
    }

    int io_error = ferror(csv_fp);
    if (fclose(csv_fp) != 0) io_error = 1;
    if (io_error) { fprintf(stderr, "CSV write failed\n"); return EXIT_FAILURE; }

    printf("-----------------------------------------------------------------\n");
    printf("Verification Summary:\n");
    printf("Final Echo Power: %.0f  --> Final Residual Power: %.0f\n",
           smooth_mic_pwr, smooth_err_pwr);
    double final_erle = 10.0 * log10(smooth_mic_pwr / smooth_err_pwr);
    bool passed = isfinite(final_erle) && final_erle >= TARGET_ERLE_DB;
    printf("Final ERLE: %.2f dB (Target: >= %.1f dB -> %s)\n",
           final_erle, TARGET_ERLE_DB, passed ? "PASS" : "FAIL");
    printf("Convergence data written to: erle_data.csv\n");

    return passed ? EXIT_SUCCESS : EXIT_FAILURE;
}
