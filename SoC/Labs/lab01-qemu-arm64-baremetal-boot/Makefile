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
