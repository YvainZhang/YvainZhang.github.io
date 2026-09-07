# 01 PCIe Gen5 / Gen6 物理层与事务层协议

## 1. PCIe 协议代际演进与 GPU 瓶颈

| PCIe 版本 | 单 Lane 传输速率 (GT/s) | x16 双向总带宽 (GB/s) | 编码方式 (Encoding) | 调制技术 (Modulation) |
| :--- | :--- | :--- | :--- | :--- |
| **PCIe 4.0** | 16 GT/s | 64 GB/s | 128b/130b | NRZ |
| **PCIe 5.0** | 32 GT/s | 128 GB/s | 128b/130b | NRZ |
| **PCIe 6.0** | 64 GT/s | 256 GB/s | 1b/1b FLIT (256-byte) | **PAM4 (4电平脉冲幅度)** |

```text
PCIe 瓶颈分析:
对于 80GB HBM (3.35 TB/s 显存带宽) 的高端 GPU，PCIe 5.0 x16 (128 GB/s) 仅为显存带宽的 3.8%！
因此，多卡大模型训练必须跨越 PCIe 瓶颈，引入专有高速互联网络（NVLink）。
```
