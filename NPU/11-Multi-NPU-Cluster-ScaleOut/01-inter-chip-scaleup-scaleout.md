# 01 Chip-to-Chip 专有高速互联拓扑与网络协议

## 1. Scale-Up 专有高速直连

云端多 NPU 服务器（如 8-NPU 或 16-NPU 模组）采用芯片直连专有高速口（如 100Gbps+ PAM4 SerDes）：
- **全互联拓扑 (Full-Mesh / Ring)**：8 卡内部通过 2D-Torus 或全互联直连，单芯片双向互联带宽达数百 GB/s。
- **直接内存访问 (Remote Memory Direct Access)**：支持跨芯片直接向对端 NPU 的片上 SRAM 或 HBM 发起零拷贝读写。
