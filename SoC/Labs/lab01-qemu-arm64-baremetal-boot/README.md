# Lab 01：QEMU ARM64 裸机启动与 UART

目标是在 QEMU `virt` 机器的 RAM 起始地址 `0x40000000` 运行最小 AArch64 镜像，通过 PL011 UART0（`0x09000000`）打印字符。QEMU `-kernel` 会把裸机镜像放到约定入口，本实验不模拟真实 BootROM。

依赖 `aarch64-none-elf-gcc` 或兼容裸机工具链、`qemu-system-aarch64`：

```bash
make CROSS_COMPILE=aarch64-none-elf-
qemu-system-aarch64 -M virt -cpu cortex-a53 -nographic -kernel build/hello.bin
```

预期输出为 `hello from qemu arm64`。随后可修改 `main.c`，读取 PL011 Flag Register，解释 TXFF 为何必须轮询。

## 文件结构

```text
lab01-qemu-arm64-baremetal-boot/
├── Makefile       # 交叉编译并生成 ELF/裸二进制镜像
├── linker.ld      # 指定入口地址与各段布局
├── start.S        # 设置栈并进入 C 入口
└── main.c         # PL011 UART 轮询发送
```

以下内容与目录中的独立源码文件保持一致；源码文件继续用于实际构建，README 中的副本用于讲解和在线阅读。

## 完整源码

### `Makefile`

```makefile
CROSS_COMPILE ?= aarch64-none-elf-
CC := $(CROSS_COMPILE)gcc
OBJCOPY := $(CROSS_COMPILE)objcopy
CFLAGS := -ffreestanding -fno-stack-protector -nostdlib -nostartfiles -Wall -Wextra -O2

all: build/hello.bin

build/hello.elf: start.S main.c linker.ld
	mkdir -p build
	$(CC) $(CFLAGS) -T linker.ld start.S main.c -o $@

build/hello.bin: build/hello.elf
	$(OBJCOPY) -O binary $< $@

clean:
	rm -rf build

.PHONY: all clean
```

构建首先生成带符号和段信息的 `hello.elf`，随后通过 `objcopy` 提取 QEMU 可以直接加载的裸二进制 `hello.bin`。

### `linker.ld`

```ld
ENTRY(_start)
SECTIONS {
    . = 0x40000000;
    .text : { KEEP(*(.text.boot)) *(.text*) }
    .rodata : { *(.rodata*) }
    .data : { *(.data*) }
    .bss (NOLOAD) : { *(.bss*) *(COMMON) }
}
```

`ENTRY(_start)` 指定程序入口；`KEEP(*(.text.boot))` 防止启动段被链接器垃圾回收；`.bss (NOLOAD)` 表示该段只占运行地址空间，不需要写入裸镜像。

### `start.S`

```asm
.section .text.boot
.global _start
_start:
    ldr x0, =stack_top
    mov sp, x0
    bl kernel_main
1:  wfe
    b 1b

.section .bss.stack, "aw", %nobits
.align 12
stack_bottom:
    .skip 16384
stack_top:
```

启动代码把栈指针设置到预留栈顶，然后调用 `kernel_main()`。如果 C 入口意外返回，CPU 会进入 `WFE` 等待循环，不再执行未知地址。

### `main.c`

```c
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
```

`volatile` 防止编译器缓存或消除 MMIO 访问。`UART_FR_TXFF` 为发送 FIFO 满标志；只有该位清零后，软件才能向 `UART_DR` 写入下一个字符。
