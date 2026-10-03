# 05 专用张量 DMA 引擎

本章介绍 **多维 Tensor DMA 引擎**：如何按 Stride 搬运张量、转换数据排布（NCHW $\leftrightarrow$ NC4HW4），以及在搬运过程中解压权重。

## 章节导航

1. [Tensor DMA 多维 Stride 寻址与硬件地址生成器](01-tensor-dma-multidim-stride.md)
2. [硬件数据排布格式转换 (NCHW 到 NC4HW4)](02-data-format-nchw-nc4hw4.md)
3. [权重在线解压缩硬件引擎](03-weight-decompression-engine.md)
4. [DMA 搬运工程问题排查与规避](04-dma-engineering-guide.md)
