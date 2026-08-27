# Lab 01：QEMU ARM64 裸机启动与 UART

目标是在 QEMU `virt` 机器的 RAM 起始地址 `0x40000000` 运行最小 AArch64 镜像，通过 PL011 UART0（`0x09000000`）打印字符。QEMU `-kernel` 会把裸机镜像放到约定入口，本实验不模拟真实 BootROM。

依赖 `aarch64-none-elf-gcc` 或兼容裸机工具链、`qemu-system-aarch64`：

```bash
make CROSS_COMPILE=aarch64-none-elf-
qemu-system-aarch64 -M virt -cpu cortex-a53 -nographic -kernel build/hello.bin
```

预期输出为 `hello from qemu arm64`。随后可修改 `main.c`，读取 PL011 Flag Register，解释 TXFF 为何必须轮询。
