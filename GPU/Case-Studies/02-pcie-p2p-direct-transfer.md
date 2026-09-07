# 02 PCIe/NVLink P2P 跨卡零拷贝直接内存访问事务流

## 1. 全硬件事务流推演

1. **GPU 0 上的 SM** 发出对远端虚拟地址 `0x7fff_0000_1000` 的 Load 指令。
2. **GPU 0 MMU** 查找页表，发现该物理页属于 **GPU 1 的 BAR1 Aperture 物理地址**。
3. **GPU 0 Crossbar** 将请求路由至 PCIe / NVLink 控制器。
4. PCIe 控制器封装 **TLP (Transaction Layer Packet) Memory Read** 报文发送至 PCIe Switch。
5. PCIe Switch 直接将 TLP 转发至 **GPU 1**（无需经过 Host CPU）。
6. **GPU 1 PCIe 接收控制器** 校验 BAR 空间，直接通过 GPU 1 Crossbar 读取其板载 HBM 显存。
7. GPU 1 封装 **Completion with Data (CplD)** 报文返回 GPU 0，写入 GPU 0 寄存器。
