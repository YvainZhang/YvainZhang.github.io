# 04 芯片 RAS 与坏块自愈

- **ECC 保护**：SRAM 寄存器堆采用 SECDED（单错纠正双错检测），HBM 显存采用 On-Die ECC + Link ECC。
- **Row Remapping（行重映射）**：当检测到某 DRAM 行发生不可纠正物理故障时，固件在下次上电或运行时自动将该行重映射到硬件备用行（Spare Rows）。
