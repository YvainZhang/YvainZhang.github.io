# 03 片上存储与双缓冲

本模块剖析 NPU 中由软件显式管理的片上存储体系——**Scratchpad Memory (SPM)**，以及隐藏数据搬运延迟的核心技术 **Ping-Pong 双缓冲（Double Buffering）**。

## 章节导航

1. [Scratchpad SRAM 物理架构与 Cache 本质区别](01-scratchpad-sram-architecture.md)
2. [Ping-Pong 双缓冲硬件设计与时序状态机](02-ping-pong-double-buffering.md)
3. [软件显式 Bank 冲突消除与高并行读写](03-software-managed-banking.md)
4. [片上存储工程问题排查与规避](04-sram-engineering-guide.md)
