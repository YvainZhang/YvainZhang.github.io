# 04 ALU、FPU 与 Tensor Core 微架构

## 1. 混合计算流水线构成与吞吐量

现代 SM 内部集成了多种异构计算流水线，由 Warp Scheduler 按指令类型发射到不同物理流水线上：

```mermaid
graph TD
    Issue["Warp Issue Unit (每个周期分派 1~2 条指令)"]
    Issue --> FP32_Pipe["FP32 ALU 流水线 (每周期 16 FMA = 32 FLOPs)"]
    Issue --> INT32_Pipe["INT32 ALU 流水线 (地址计算与标量操作)"]
    Issue --> FP64_Pipe["FP64 双精度单元 (科学计算 DP 流水线)"]
    Issue --> SFU_Pipe["SFU 单元 (rsqrt, exp, log, sin/cos 逼近)"]
    Issue --> Tensor_Pipe["Tensor Core MMA 矩阵计算阵列 (Dense Matrix Multiply)"]

    FP32_Pipe --> RF_WB["写回寄存器堆 (Register File Write-Back)"]
    INT32_Pipe --> RF_WB
    FP64_Pipe --> RF_WB
    SFU_Pipe --> RF_WB
    Tensor_Pipe --> RF_WB
```

---

## 2. Tensor Core 硬件矩阵乘架构 (以 4 代 MMA 为例)

Tensor Core 突破了传统的 SIMT 标量发射，单个指令即可让整个 Warp 协同完成一个小矩阵乘法：
$$D = A \times B + C$$

```mermaid
graph LR
    subgraph WarpMMA["Warp 级协作 (16x16x16 MMA)"]
        MatrixA["Matrix A: 16x16 FP16/FP8 (沿 Row 切分给 32 Lane)"]
        MatrixB["Matrix B: 16x16 FP16/FP8 (沿 Col 切分给 32 Lane)"]
        MatrixC["Accumulator C: 16x16 FP32/FP16"]
        
        MAC_Array["Tensor Core 4x4 密集脉动乘加阵列"]
        
        MatrixA --> MAC_Array
        MatrixB --> MAC_Array
        MatrixC --> MAC_Array
        MAC_Array --> MatrixD["Output Matrix D: 16x16 FP32"]
    end
```

Tensor Core 的算力密度达到传统 FP32 ALU 的 8~16 倍，是现代 LLM 训练与推理最核心的算力来源。
