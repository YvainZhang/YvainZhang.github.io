# NPU / AI 芯片与 DSA 专业术语表

| 缩写 / 术语 | 英文全称 | 核心释义 |
| :--- | :--- | :--- |
| **DSA** | Domain-Specific Architecture | 专用领域架构，针对特定算法范式（如深度学习张量计算）量身定制的高能效芯片架构 |
| **Systolic Array** | 2D Systolic Array | 2D 脉动阵列，空间计算矩阵，操作数与部分和在相邻处理单元（PE）间如血液脉动般流水流动 |
| **PE** | Processing Element | 处理单元，脉动阵列的最小计算细胞，包含乘加器（MAC）、局部寄存器与传递锁存器 |
| **MAC** | Multiply-Accumulate Unit | 乘累加硬件单元，单周期内执行一次乘法并累加至累加器（$Acc = Acc + A \times B$） |
| **Accumulator** | Hardware Accumulator | 硬件累加寄存器，通常配置 32-bit 或更高位宽以防止多次低比特乘积累加溢出 |
| **WS** | Weight Stationary Mode | 权重驻留模式，模型权重提前锁存固定在 PE 内部，激活向东流动，部分和向南累加流出 |
| **OS** | Output Stationary Mode | 输出驻留模式，累加和固定在 PE 累加器中直至计算完成，输入与权重在阵列中流动 |
| **IS** | Input Stationary Mode | 输入驻留模式，输入激活值驻留在 PE 内部，权重流经阵列多次复用 |
| **VPU** | Vector Processing Unit | 向量处理单元，包含高位宽 SIMD 流水线，专用于加速 LayerNorm、Softmax、GELU 等 1D 算子 |
| **SFU** | Special Function Unit | 特殊函数单元，集成硬件查找表（LUT）与分段多项式插值，用于非线性激活函数逼近 |
| **LUT** | Look-Up Table | 片上硬件查找表，由双端口小 SRAM 构成，单周期完成复杂非线性函数区间采样 |
| **PLA** | Piecewise Linear Approximation | 分段线性逼近算法，硬件使用斜率与截距快速计算非线性激活值（$y = y_0 + k(x-x_0)$） |
| **SPM** | Scratchpad Memory (SRAM) | 暂存器存储，由软件显式编址的片上高速 SRAM，无 Tag 比对开销，确定性单周期访问 |
| **Double Buffering** | Ping-Pong Double Buffering | 双缓冲机制，分配两块对称 SRAM 缓冲区，DMA 搬运与阵列计算异步交替，100% 隐藏访存延迟 |
| **Bank Conflict** | SRAM Bank Conflict | 多个计算 Lane 或 DMA 端口同一周期访问 SRAM 同一 Bank 导致的硬件争用与等待 |
| **Quantization** | Neural Network Quantization | 神经网络量化，将高精度浮点（FP32/FP16）转换为低比特（INT8/FP8/INT4）以节省带宽与面积 |
| **PTQ** | Post-Training Quantization | 训练后量化，基于少量离线校准数据集计算 Tensor 动态范围与 Scale 缩放因子 |
| **QAT** | Quantization-Aware Training | 量化感知训练，在反向传播中使用伪量化（Fake-Quant）前向模拟硬件定点误差 |
| **INT8** | 8-bit Signed Integer | 8 位有符号整数，动态范围 $[-128, 127]$，端侧与传统 CNN 推理标准格式 |
| **FP8 E4M3** | FP8 (1-bit Sign, 4-bit Exp, 3-bit Mantissa) | 具备更高尾数位宽的 8 位浮点格式，适合大模型前向推理与激活计算 |
| **FP8 E5M2** | FP8 (1-bit Sign, 5-bit Exp, 2-bit Mantissa) | 具备更大动态范围的 8 位浮点格式，适合大模型反向传播梯度计算 |
| **BF16** | Brain Floating Point 16-bit | 16 位脑浮点，保留与 FP32 完全相同的 8 位指数位宽，消除梯度溢出下溢风险 |
| **Microscaling** | MXFP / Microscaling Formats | OCP 微缩量化标准，小粒度（如 32 个元素）共享单个 8-bit Scale 因子 + 细粒度低比特尾数 |
| **Outlier** | Activation Outlier Spike | 激活值异常离群值，注意力层出现的极值尖峰，需通过非对称量化或 SmoothQuant 处理 |
| **Stochastic Rounding** | Stochastic Rounding | 随机舍入，基于概率分布决定最低位进位，在大模型低比特训练中有效防止小梯度消失 |
| **Tensor DMA** | Multi-Dimensional Tensor DMA | 专有多维张量 DMA 搬运引擎，集成硬件多级计数器，支持 2D~5D 非连续张量跨步搬运 |
| **AGU** | Address Generation Unit | 硬件地址生成器，在 DMA 内部实时计算多维跨步物理地址，无需 CPU 频繁配置 |
| **Stride** | Memory Stride | 内存跨步，多维张量在物理内存中各维度之间的地址步长偏移行距 |
| **NC4HW4** | Channel-Aligned Block Format | 通道块对齐格式，将通道维度按 4/8/16 深度打包，匹配脉动阵列并行 MAC 连续读取 |
| **Transpose-on-the-fly**| Hardware Transpose-on-the-fly | 硬件实时转置，Tensor DMA 从 DDR 读入数据流经硬件流水线时零开销完成排布转换 |
| **Weight Decompression**| Hardware Weight Decompressor | 权重在线解压缩引擎，实时对 Huffman / Run-Length 压缩权重流解包，等效扩展外部带宽 |
| **2D Mesh NoC** | 2D Mesh Network-on-Chip | 二维网格片上网络，将芯片划分为规则多核 Tile，提供高扩展性分布式互联 |
| **Router** | NoC Router Node | 片上路由器，包含 5 个双向端口（东/西/南/北/本地）与交叉开关（Crossbar Switch） |
| **Virtual Channel** | NoC Virtual Channel (VC) | 虚通道，在同一物理链路中复用多个独立 FIFO 队列，消除队头阻塞（HOL Blocking） |
| **DOR** | Dimension-Order Routing (XY Routing)| 维序路由算法，数据包严格先沿 X 轴后沿 Y 轴单向传输，数学证明天然免疫死锁 |
| **Multicast** | Hardware Multicast Tree | 硬件多播，单一权重数据包在 NoC 路由器分支处由硬件自动复制下发给多个目标 Tile |
| **Credit Flow Control**| Credit-based Flow Control | 信用流控，下游节点向上游返还可用 Buffer 信用点数，实现绝对无溢出硬件流控 |
| **VLIW** | Very Long Instruction Word | 超长指令字，单个指令字封装多个 Slot，单周期并行发射至 DMA、脉动与 VPU 引擎 |
| **Task Queue** | Hardware Task Queue | 硬件任务队列，存放由编译器烘焙的模型算子执行描述符 |
| **Graph Engine** | Hardware Graph Execution Engine | 硬件图执行引擎，根据算子依赖关系自动流水级联调度，无需 OS 系统调用介入 |
| **Hardware Barrier** | Hardware Sync Barrier | 硬件同步栅障，不同执行引擎（DMA 与 PE）之间的高速硬件互锁寄存器 |
| **Event Register** | Hardware Event Register | 硬件事件寄存器，用于标记 DMA 传输完毕、脉动计算就绪与中断触发状态 |
| **Edge NPU** | Edge Inference NPU | 端侧推理 NPU，强调极致超低功耗（<5W）、定点量化与摄像头 ISP 零拷贝融合 |
| **Cloud NPU** | Cloud Training/Inference NPU | 云端算力 NPU，配备超大 HBM3e 显存、浮点训练支持与大规模 Chip-to-Chip 扩展接口 |
| **PPA** | Power, Performance, Area | 功耗、性能与芯片面积权衡金字塔指标 |
| **TOPS/W** | Tera-Operations Per Second per Watt | 算力能效比，每瓦特功耗所能提供的万亿次定点/浮点运算峰值 |
| **Graph IR** | High-Level Graph Intermediate Representation | 计算图高层中间表示（如 Relay、TorchDynamo Graph、MLIR TOSA/Linalg） |
| **Operator Fusion** | Operator Fusion Pass | 算子融合，将连续小算子合并为单个片上执行 Kernel，消除中间中间特征图显存读写 |
| **Constant Folding** | Constant Folding Pass | 常量折叠，编译期提前完成权重预处理（如 BatchNorm 参数融入卷积权重） |
| **Loop Tiling** | Loop Tiling / Blocking | 循环切块，将大矩阵切分为适合片上 SRAM 容量的最佳微小 Tile 块 |
| **Interval Graph Coloring**| Interval Graph Coloring | 区间图着色算法，根据 Tensor 生命周期重叠图，实现片上 SRAM 零碎片静态内存复用 |
| **MLIR** | Multi-Level Intermediate Representation | 多级中间表示框架，支持从计算图 Dialect 逐步降级为硬件特定 Microcode |
| **Dialect** | MLIR Dialect | MLIR 方言，特定抽象层级（TOSA、Linalg、Affine、MemRef、LLVM）的指令自闭环集合 |
| **Codegen** | Low-Level Code Generation | 底层代码生成，AI 编译器后端生成含硬件二进制指令与 DMA 描述符的离线模型包 |
| **Microcode** | NPU Microcode | NPU 底层微码，驱动硬件执行状态机与微指令发射的核心固件指令序列 |
| **MFU** | Model FLOPs Utilization | 模型浮点算力利用率，实际模型单步吞吐量占硬件理论峰值算力的比例 |
| **HFU** | Hardware FLOPs Utilization | 硬件浮点算力利用率，考虑反向传播激活值重计算后的实际硬件算力开销比例 |
| **Memory-Bound** | Memory-Bound Operator | 访存受限算子（如 LayerNorm、Softmax、GEMV），性能瓶颈在于外部内存读取带宽 |
| **Compute-Bound** | Compute-Bound Operator | 算力受限算子（如大尺寸 GEMM、密集 Conv），性能瓶颈在于 MAC 阵列物理峰值算力 |
| **Timeline Trace** | Timeline Trace Profiling | 时间线性能跟踪，可视化展示 DMA、脉动阵列与 VPU 在各个时隙的重叠度与气泡 |
| **MLPerf** | MLPerf Benchmark Suite | 工业界权威的 AI 硬件性能评测基准套件（涵盖 ResNet、BERT、LLaMA 等模型） |
| **Chip-to-Chip** | Chip-to-Chip Scale-Up Interconnect | 芯片间专有高速直连协议，通过超高速 SerDes 构建多卡统一虚拟内存超节点 |
| **HCCL** | Huawei Collective Communication Library | 昇腾 NPU 专用集合通信加速库，驱动片内 Ring 与跨节点树形通信加速引擎 |
| **2:4 Sparsity** | 2:4 Structured Sparsity | 2:4 结构化稀疏，连续 4 个权重中固定 2 个为零，硬件多路选择器单周期跳过零值 |
| **ISO 26262** | ISO 26262 Functional Safety Standard | 道路车辆功能安全标准，车规级 NPU 必须满足 ASIL-D 等级认证 |
| **Dual-Core Lockstep** | Dual-Core Lockstep (DCLS) | 双核锁步架构，两个 NPU 核心周期级同步运行同一指令，硬件比对逻辑检测单粒子翻转 |
| **Safety Island** | Hardware Safety Island | 硬件安全岛，运行隔离安全固件的独立高安全核，负责整车故障诊断与应急制动 |
| **eFuse** | Electronic Fuse Array | 片内一次性可编程电子熔丝阵列，用于固化芯片唯一根密钥与安全启动公钥哈希 |
| **NPU TEE** | NPU Trusted Execution Environment | NPU 可信执行环境，提供硬件安全启动与权重从内存载入时的实时 AES 硬件解密 |
