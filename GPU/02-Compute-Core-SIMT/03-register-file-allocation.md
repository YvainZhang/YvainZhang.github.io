# 03 寄存器堆物理组织与 Register Spill

## 1. 庞大的片上寄存器堆 (Register File)

现代 GPU 的 SM 拥有惊人容量的寄存器堆（通常单个 SM 包含 64K 个 32-bit 寄存器，即 256KB SRAM，全芯片超过 30MB+ 寄存器）。
- 寄存器堆采用高度多 Bank 化的物理 SRAM 组织（如 16~32 Bank），每个周期为 32 个 Lane 同时提供 3 个源操作数（$32 	imes 3 	imes 4	ext{ Bytes} = 384	ext{ Bytes/cycle}$ 内部吞吐）。

---

## 2. Register Spill（寄存器溢出）与性能断崖

当编译器编译复杂 Kernel 时，若单个线程所需寄存器数量超过上限（如超过 255 个，或为了提升 SM Occupancy 限制每线程最多使用 32 个寄存器）：
1. 编译器会将多余的局部变量溢出（Spill）到 **Local Memory（局部内存）**。
2. **硬件本质**：Local Memory 在物理上并不存在独立片上 SRAM，而是**映射在外部物理显存 VRAM 中**（仅由 L1/L2 Cache 缓存）。
3. **性能影响**：发生 Register Spill 会瞬间导致大量的额外 L1/L2 读写流量，大幅增加 Warp Stall 周期，是性能优化的头号杀手。

```text
nvcc 编译输出提示:
ptxas info    : Used 128 registers, 2048 bytes smem, 384 bytes spill stores, 384 bytes spill loads
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              警告：出现 Spill Stores/Loads，表明局部变量溢出至显存，严重拖慢算子！
```
