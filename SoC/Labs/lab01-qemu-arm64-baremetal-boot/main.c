#include <stdint.h>

#define UART_BASE 0x09000000UL
#define UART_DR   (*(volatile uint32_t *)(UART_BASE + 0x00))
#define UART_FR   (*(volatile uint32_t *)(UART_BASE + 0x18))
#define UART_FR_TXFF (1u << 5)

static void uart_putc(char c)
{
    while (UART_FR & UART_FR_TXFF) { }
    UART_DR = (uint32_t)c;
}

void kernel_main(void)
{
    const char *s = "hello from qemu arm64\n";
    while (*s)
        uart_putc(*s++);
}
