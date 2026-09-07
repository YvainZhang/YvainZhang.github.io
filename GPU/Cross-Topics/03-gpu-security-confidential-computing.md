# 03 机密计算与显存硬件加密

- **GPU TEE (Trusted Execution Environment)**：GPU 内部包含硬件安全引擎与安全启动（Secure Boot）。
- **硬件显存加密 (AES-XTS-256)**：所有从 GPU 内部流出至片外 HBM/GDDR 的数据全部经由硬件 Inline 引擎实时加密，防止物理插针侦听。
