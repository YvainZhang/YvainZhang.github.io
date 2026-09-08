#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdbool.h>
#include <string.h>

/**
 * @brief I2S 传输格式枚举
 */
typedef enum {
    I2S_FORMAT_PHILIPS = 0,  // 标准 Philips I2S: LRCK 跳变后延迟 1 个 BCLK 周期输出 MSB
    I2S_FORMAT_LEFT_JUSTIFIED = 1 // 左对齐格式 (LJ): LRCK 跳变沿与 MSB 严格对齐
} i2s_format_t;

/**
 * @brief I2S 硬件发送状态机微架构模型
 */
typedef struct {
    uint32_t tx_shift_reg;
    int bit_count;          // 槽位剩余位数 (例如 32)
    bool lrck;              // 0: 左声道, 1: 右声道
    i2s_format_t format;
    bool delay_pending;     // 标准 I2S 延迟 1 拍状态位
} i2s_tx_hardware_t;

/**
 * @brief VCD (Value Change Dump) 波形记录器
 */
typedef struct {
    FILE *fp;
    uint64_t timestamp_ns;
} vcd_recorder_t;

static void vcd_init(vcd_recorder_t *rec, const char *filename) {
    rec->fp = fopen(filename, "w");
    if (!rec->fp) {
        perror("Failed to open VCD file");
        return;
    }
    rec->timestamp_ns = 0;

    fprintf(rec->fp, "$date\n   2026-09-08\n$end\n");
    fprintf(rec->fp, "$version\n   Audio-Atlas I2S VCD Generator v1.0\n$end\n");
    fprintf(rec->fp, "$timescale 1ns $end\n");
    fprintf(rec->fp, "$scope module i2s_bus $end\n");
    fprintf(rec->fp, "$var wire 1 ! bclk $end\n");
    fprintf(rec->fp, "$var wire 1 \" lrck $end\n");
    fprintf(rec->fp, "$var wire 1 # sdata $end\n");
    fprintf(rec->fp, "$upscope $end\n");
    fprintf(rec->fp, "$enddefinitions $end\n");
    fprintf(rec->fp, "$dumpvars\n0!\n0\"\n0#\n$end\n");
}

static void vcd_dump_step(vcd_recorder_t *rec, bool bclk, bool lrck, bool sdata) {
    if (!rec->fp) return;
    fprintf(rec->fp, "#%" PRIu64 "\n", rec->timestamp_ns);
    fprintf(rec->fp, "%d!\n", bclk ? 1 : 0);
    fprintf(rec->fp, "%d\"\n", lrck ? 1 : 0);
    fprintf(rec->fp, "%d#\n", sdata ? 1 : 0);
    rec->timestamp_ns += 160; // 假设 BCLK 约为 3.072MHz (半周期约 160ns)
}

static void vcd_close(vcd_recorder_t *rec) {
    if (rec->fp) {
        fclose(rec->fp);
        rec->fp = NULL;
    }
}

/**
 * @brief 单步时钟沿仿真步进
 */
void i2s_step(i2s_tx_hardware_t *dev, uint32_t left_sample, uint32_t right_sample,
              bool *bclk, bool *lrck, bool *sdata) {
    *bclk = !(*bclk);
    if (!(*bclk)) {
        /* WS changes every 32 bit clocks. In Philips format this edge still
         * carries the previous channel's LSB; the next edge carries the MSB. */
        if (dev->bit_count == 0) {
            if (dev->format == I2S_FORMAT_PHILIPS)
                *sdata = (dev->tx_shift_reg & UINT32_C(0x80000000)) != 0;
            dev->lrck = !dev->lrck;
            dev->tx_shift_reg = dev->lrck ? right_sample : left_sample;
        }
        if (dev->format == I2S_FORMAT_LEFT_JUSTIFIED || dev->bit_count != 0) {
            *sdata = (dev->tx_shift_reg & UINT32_C(0x80000000)) != 0;
            dev->tx_shift_reg <<= 1;
        }
        dev->bit_count = (dev->bit_count + 1) % 32;
    }
    *lrck = dev->lrck;
}

int main(void) {
    i2s_tx_hardware_t dev;
    memset(&dev, 0, sizeof(dev));
    dev.format = I2S_FORMAT_PHILIPS;
    dev.lrck = true; // 初始为右声道，首次进入会翻转为 0 (左声道)

    bool bclk = true, lrck = true, sdata = false;
    // 设定左右声道测试特征字
    uint32_t left = 0xA5A55A5A;  // 10100101 10100101 01011010 01011010
    uint32_t right = 0x12345678; // 00010010 00110100 01010110 01111000

    vcd_recorder_t vcd;
    vcd_init(&vcd, "i2s_trace.vcd");
    if (!vcd.fp) return 1;

    printf("=================================================================\n");
    printf("   Audio Lab 01: Standard I2S (Philips) Hardware Simulation      \n");
    printf("=================================================================\n");
    printf("Test Vectors: Left=0x%08X, Right=0x%08X\n\n", left, right);
    printf("Simulating 65 BCLK cycles including startup and the final right LSB...\n");
    printf("-----------------------------------------------------------------\n");
    printf(" Cycle | BCLK | LRCK(Channel) | SDATA | Event Description\n");
    printf("-----------------------------------------------------------------\n");

    // One startup bit plus 64 sample bits, with a falling then rising edge.
    for (int edge = 0; edge < 130; edge++) {
        i2s_step(&dev, left, right, &bclk, &lrck, &sdata);
        vcd_dump_step(&vcd, bclk, lrck, sdata);

        // 在 BCLK 上升沿（Slave 稳定采样点）打印系统状态
        if (bclk) {
            int cycle = edge / 2;
            const char *event = "";
            if (cycle == 0) event = "<-- LRCK 切换为左声道 (0), Philips 延迟拍 (空闲)";
            else if (cycle == 1) event = "<-- 左声道 MSB (Bit 31) 正式输出";
            else if (cycle == 32) event = "<-- WS 切换为右声道，此拍仍为左声道 LSB";
            else if (cycle == 33) event = "<-- 右声道 MSB (Bit 31) 正式输出";
            else if (cycle == 64) event = "<-- WS 切换为左声道，此拍仍为右声道 LSB";

            printf("  #%02d  |  %d   |    %d (%s)    |   %d   | %s\n",
                   cycle, bclk, lrck, lrck ? "Right" : "Left ", sdata, event);
        }
    }

    vcd_close(&vcd);
    printf("-----------------------------------------------------------------\n");
    printf("VCD trace successfully exported to: i2s_trace.vcd\n");
    printf("View waveforms using: gtkwave i2s_trace.vcd\n");
    return 0;
}
