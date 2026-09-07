# 01 GPU 硬件虚拟化（SR-IOV、vGPU 与 MIG 算力隔离）

- **SR-IOV**：硬件层面将单个物理 GPU 虚拟出多个 PCIe 物理功能（VF），直接直通给 VM。
- **MIG (Multi-Instance GPU)**：在物理硬件上对 GPC、SM、L2 Cache 切片与 HBM 控制器进行**完全物理级硬件硬隔离**，不同实例之间绝无 QoS 干扰。
