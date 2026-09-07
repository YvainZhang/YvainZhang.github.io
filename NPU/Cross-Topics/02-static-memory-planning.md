# 02 编译期静态内存分配算法

- **区间图着色算法（Interval Graph Coloring）**：编译器为每个张量标注 `[start_cycle, end_cycle]` 生命周期，将不重叠的张量放置在同一块物理 SRAM 偏移上，实现 0 内存碎片。
