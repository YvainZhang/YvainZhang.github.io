# GPU 芯片与系统专业术语表

| 缩写 / 术语 | 英文全称 | 核心释义 |
| :--- | :--- | :--- |
| **SM** | Streaming Multiprocessor | 流式多处理器，GPU 核心计算引擎，包含 Warp 调度器、寄存器堆与算术流水线 |
| **CU** | Compute Unit | AMD GPU 架构中的核心计算单元，等效于 NVIDIA 的 SM |
| **SIMT** | Single Instruction, Multiple Threads | 单指令多线程执行模型，硬件将多线程聚合成 Warp 锁步执行 |
| **Warp** | Warp (32 Threads) | 硬件指令发射与调度的最小线程束（NVIDIA 32 线程，AMD Wavefront 32/64 线程） |
| **Warp Divergence** | Warp Branch Divergence | 分支分化，Warp 内部线程进入不同条件分支导致硬件串行执行与掩码屏蔽 |
| **ITS** | Independent Thread Scheduling | 独立线程调度，每个线程独立维护 PC 与调用栈，提升复杂控制流执行灵活性 |
| **Scoreboard** | Scoreboard Hazard Tracker | 硬件记分板，追踪寄存器 RAW 数据依赖与未就绪访存状态 |
| **Occupancy** | Warp Occupancy | SM 活跃 Warp 数量占硬件物理最大容量的百分比，评估延迟隐藏能力 |
| **Register Spill** | Register Spill to Local Memory | 寄存器溢出，局部变量超过寄存器上限被编译器迫降写回 Local Memory (显存) |
| **Local Memory** | Thread Local Memory | 逻辑上的每线程私有内存，物理上映射在外部显存中，由 L1/L2 缓存 |
| **Shared Memory** | Shared Memory (SRAM) | SM 内部由程序员显式控制的片上高速暂存 SRAM，供同一个 Block 线程共享 |
| **Bank Conflict** | Shared Memory Bank Conflict | 多个线程同时访问 Shared Memory 同一 Bank 的不同地址导致的串行访问延迟 |
| **Coalescing** | Global Memory Coalescing | 访存合并，将 Warp 内 32 个线程的连续显存访问合并为单次 128-byte 事务 |
| **Tensor Core** | Tensor Core (MMA Engine) | 专用于稠密矩阵乘累加（$D = A 	imes B + C$）的高吞吐硬件计算引擎 |
| **SFU** | Special Function Unit | 特殊函数单元，用于快速硬件逼近 `sin`、`cos`、`exp`、`rsqrt` 等非线性函数 |
| **HBM** | High Bandwidth Memory | 高带宽显存，通过 3D TSV 硅通孔垂直堆叠 DRAM Die，提供数 TB/s 极致带宽 |
| **CoWoS** | Chip-on-Wafer-on-Substrate | TSMC 2.5D 晶圆级封装技术，将 GPU 计算 Die 与 HBM 堆叠在中介层上 |
| **TSV** | Through-Silicon Via | 硅通孔，垂直穿透硅晶圆实现高密度芯片间电气互连的微通道 |
| **GDDR** | Graphics Double Data Rate SDRAM | 显存专用的高速板载表面贴装 DDR 颗粒（如 GDDR6X、GDDR7） |
| **PAM4** | 4-Level Pulse Amplitude Modulation | 4 电平脉冲幅度调制，单个时钟周期传输 2 个 bit，成倍提升高速 SerDes 速率 |
| **NoC** | Network on Chip | 片上网络，连接数百个 SM、L2 Cache 切片与显存控制器的全互联总线矩阵 |
| **Point of Coherence** | Point of Coherence (PoC) | 全系统数据达成一致性的体系结构汇聚点（GPU 中通常为全局统一 L2 Cache） |
| **Atomic RMW** | Atomic Read-Modify-Write | 硬件原子读改写操作，由 L2 Cache 控制器内部 ALU 直接执行以消除总线拥塞 |
| **MMU** | Memory Management Unit | GPU 内部硬件内存管理单元，负责虚拟地址（VA）到物理地址（PA）的翻译与保护 |
| **TLB** | Translation Lookaside Buffer | GPU 旁路快表，多级缓存虚拟页表项（Micro-TLB + Main-TLB） |
| **UVM** | Unified Virtual Memory | 统一虚拟内存，支持 CPU 与 GPU 共享单一连续指针空间并按需动态按页迁移 |
| **HMM** | Heterogeneous Memory Management | Linux 内核主线异构内存管理框架，支持 GPU 直接镜像访问 CPU 匿名内存页 |
| **ATS** | Address Translation Services | PCIe 硬件地址转换服务协议，允许 GPU 端点直接向 Host IOMMU 请求地址解析 |
| **PASID** | Process Address Space ID | PCIe 事务携带的进程地址空间标识符，实现多进程 GPU 虚拟内存安全隔离 |
| **PRI** | Page Request Interface | PCIe 缺页请求接口，允许 GPU 硬件触发 Host OS 缺页中断并将数据加载入内存 |
| **BAR** | Base Address Register | PCIe 配置空间基地址寄存器，将 GPU 寄存器（BAR0）与显存（BAR1）映射入 Host PA |
| **ReBAR** | Resizable BAR / Smart Access Memory | 可重设大小的 BAR，允许 Host CPU 64-bit 线性直通映射 GPU 全部物理显存 |
| **Doorbell** | Hardware Doorbell Register | 硬件门铃寄存器，软件写入新任务尾指针直接唤醒硬件取指，实现零系统调用提交 |
| **PushBuffer** | Command PushBuffer / Ring Buffer | 任务提交环形缓冲区，存放 UMD 打包的 GPU 机器指令与上下文参数 |
| **KMD** | Kernel Mode Driver | 内核态驱动，负责物理显存分配、中断注册、电源状态管理与 GPU 异常复位 |
| **UMD** | User Mode Driver | 用户态驱动（如 `libcuda.so`），负责算子编译、内存池化分配与 PushBuffer 组包 |
| **DRM** | Direct Rendering Manager | Linux 内核官方图形与算力驱动子系统框架 |
| **KMS** | Kernel Mode Setting | Linux DRM 中负责显示分辨率、图层合成与接口输出的模式设置子系统 |
| **GEM** | Graphics Execution Manager | Linux DRM 中的显存对象管理器，负责 Buffer 分配与跨进程共享 |
| **DMA-BUF** | DMA Buffer Sharing | Linux 内核跨驱动（GPU、网卡、VPU、Display）零拷贝共享物理内存的标准机制 |
| **PTX** | Parallel Thread Execution | GPU 虚拟机器指令集，由 NVCC 生成，具备跨 GPU 硬件代际的向前兼容性 |
| **SASS** | Streaming Assembler | 对应特定 GPU 物理微架构芯片的底层原生机器二进制指令集 |
| **NVLink** | NVIDIA High-Speed GPU Interconnect | GPU 专有片间高速互联协议，提供单卡 900GB/s~1.8TB/s 远超 PCIe 的点对点带宽 |
| **NVSwitch** | NVSwitch Fabric Chip | 独立的 NVLink 交叉交换芯片，构建 8 卡至数百卡无阻塞 Fat-Tree 互联网络 |
| **Infinity Fabric** | AMD Infinity Fabric | AMD 芯片内与芯片间统一高速相干互联架构 |
| **Copy Engine** | Copy Engine / DMA Engine | GPU 独立于计算核心的硬件 DMA 搬运引擎，支持 H2D、D2H、P2P 三向并发 |
| **GPUDirect RDMA** | GPUDirect Remote DMA | 允许 RDMA 网卡绕过 Host CPU 内存直接通过 PCIe P2P 读写 GPU 显存的零拷贝技术 |
| **GPUDirect Storage** | GPUDirect Storage (GDS) | 允许 NVMe SSD 绕过 Host 操作系统 Page Cache 直接与 GPU 显存通信的技术 |
| **CUDA Stream** | CUDA Stream | GPU 任务异步发射执行队列，不同非阻塞 Stream 在硬件级别并发重叠执行 |
| **CUDA Graph** | CUDA Graph | 预先烘焙算子依赖拓扑图，单次提交整张图消除 CPU Launch 驱动下发开销 |
| **DVFS** | Dynamic Voltage and Frequency Scaling | 动态电压与频率调节，根据负载毫秒级调控 Core Clock 与供电电压 |
| **AVFS** | Adaptive Voltage and Frequency Scaling | 自适应电压调节，片内集成环形振荡器按工艺角与温度实时校准最佳工作电压 |
| **PMU** | Power Management Unit | 片内独立运行的安全微控制器固件，监控电流/电压/温度并执行 PID 调频 |
| **Power Capping** | Dynamic Power Capping | 动态功耗封顶，严格限制芯片整卡功耗不超过设定阈值（如 300W）以防跳闸 |
| **TDP** | Thermal Design Power | 热设计功耗，散热系统所必须能够有效散发的最大持续发热量 |
| **Thermal Throttling** | Thermal Throttling Protection | 过温降频保护，当温度超过安全阈值（如 88°C）时强制降频降压防止烧毁 |
| **Rasterizer** | Hardware Rasterizer | 硬件光栅化器，将 3D 几何多边形顶点离散化为屏幕 2D 像素片段 |
| **RT Core** | Ray Tracing Core | 光线追踪核心，包含硬件 BVH 树遍历与 Ray-Triangle 相交测试加速电路 |
| **BVH** | Bounding Volume Hierarchy | 层次包围盒，用于加速 3D 场景中光线与物体相交查询的树状空间结构 |
| **NVENC / NVDEC** | Hardware Video Encoder / Decoder | 独立于 SM 核心的硬件音视频编解码器，支持 H.264/HEVC/AV1 格式硬解 |
| **Display Engine** | Display Engine / Controller | 显示引擎，负责 Framebuffer 扫描、色彩空间转换与 DP/HDMI 物理信号输出 |
| **DSC** | Display Stream Compression | 显示流无损压缩算法，在有限接口带宽下传输超高分辨率与超高刷新率画面 |
| **Roofline Model** | Roofline Performance Model | 理论性能评估模型，以算术强度判断算子瓶颈属于 Memory-Bound 还是 Compute-Bound |
| **Arithmetic Intensity** | Operational / Arithmetic Intensity | 算术强度，算子每访问 1 字节显存所执行的浮点运算次数（FLOPs/Byte） |
| **MFU** | Model FLOPs Utilization | 模型浮点算力利用率，实际吞吐算力占硬件理论峰值算力的百分比 |
| **HFU** | Hardware FLOPs Utilization | 硬件浮点算力利用率，计入重计算（Activation Recomputation）后的硬件利用率 |
| **Xid** | NVIDIA Driver Error Code | GPU 内核驱动向系统日志报告的硬件与系统级严重故障分类错误码 |
| **Hang** | GPU Engine Hang | GPU 硬件执行死锁或陷入无限循环，触发驱动 Watchdog 定时器超时复位 |
| **AER** | Advanced Error Reporting | PCIe 高级错误上报协议，精确定位 PCIe 物理层/数据链路层不可纠正错误 |
| **ECC** | Error-Correcting Code | 纠错码，SRAM 采用 SECDED 校验，HBM 采用 On-Die + Link ECC 保护 |
| **SECDED** | Single Error Correction, Double Error Detection | 单错纠正、双错检测硬件纠错电路 |
| **Row Remapping** | DRAM Row Remapping | 显存坏行重映射，硬件自动将发生故障的 DRAM 行替换为备用冗余行 |
| **NCCL** | NVIDIA Collective Communications Library | 多 GPU 分布式集合通信库，针对 NVLink 与 PCIe 深度优化 |
| **Ring AllReduce** | Ring AllReduce Algorithm | 环形集合通信算法，数据按 Ring 传递 $2(N-1)$ 步完成跨卡规约与广播 |
| **Tree AllReduce** | Double Binary Tree AllReduce | 双二叉树通信算法，在小数据量下将通信跳数降至 $2\log_2 N$，降低时延 |
| **TP** | Tensor Parallelism | 张量模型并行（如 Megatron-LM），将单个矩阵权重切分在同机多卡间计算 |
| **PP** | Pipeline Parallelism | 流水线模型并行，将模型不同网络层按顺序切分在跨节点 GPU 上执行（1F1B） |
| **DP** | Data Parallelism | 数据并行，不同 GPU 处理不同 Batch 数据，反向传播聚合梯度（DDP / FSDP） |
| **ZeRO** | Zero Redundancy Optimizer | 零冗余优化器，将模型参数、梯度和优化器状态分片消除冗余（ZeRO-1/2/3） |
| **RoCEv2** | RDMA over Converged Ethernet v2 | 基于标准三层 UDP/IP 以太网运行的无损远程直接内存访问协议 |
| **PFC** | Priority-based Flow Control | 基于优先级的以太网流控机制，在队列接近溢出时向上游发送 Pause 帧实现无丢包 |
| **ECN** | Explicit Congestion Notification | 显式拥塞通知，交换机在队列排队时打标 IP 包头，触发源端主动降速 |
| **InfiniBand** | InfiniBand (IB) | 专用超高性能无损集群互联网络架构，支持端到端纳秒级硬件 RDMA 与 SHARP 算网融合 |
| **SHARP** | Scalable Hierarchical Aggregation and Reduction Protocol | 可扩展分层聚合协议，由 InfiniBand 交换机直接在网络芯片内执行 AllReduce 规约 |
| **SR-IOV** | Single Root I/O Virtualization | 单根 I/O 虚拟化，硬件直接将单个物理 GPU 虚拟化为多个独立 PCIe 虚拟功能 (VF) |
| **MIG** | Multi-Instance GPU | 多实例 GPU，在物理层面对 SM、L2 Cache 和 HBM 控制器进行物理硬件级硬隔离 |
| **TEE** | Trusted Execution Environment | 可信执行环境，在 GPU 内部提供硬件级机密计算隔离与显存实时加密 |
