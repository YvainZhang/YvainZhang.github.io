# 03 车规 ISO 26262 功能安全与双核锁步

- **Dual-Core Lockstep (DCLS)**：两个完全相同的 NPU 核心运行相同指令，硬件周期级比对输出；若不一致在 1 个时钟周期内触发安全岛（Safety Island）紧急制动。
