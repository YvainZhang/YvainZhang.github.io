# 01 计算图优化与算子融合 (Graph Optimization & Fusion)

## 1. 经典算子融合模式 (Operator Fusion)

算子融合是减少 DDR/HBM 访存次数、提升算力利用率的关键手段：
- **Conv + BatchNorm + ReLU 融合**：在编译期将 BatchNorm 参数直接数学折叠进卷积权重 $W$ 与偏置 $B$ 中，并在脉动阵列输出端由激活单元直接完成 ReLU，消除两次中间显存写回。
- **MatMul + Bias + GELU 融合**：矩阵乘计算结果在片内流水线直接加上 Bias 并执行 GELU 激活函数。

```mermaid
graph LR
    subgraph BeforeFusion["融合前 (需 3 次显存读写)"]
        Conv["Conv2D"] -->|写回 DDR| Mem1["DDR Buffer 1"]
        Mem1 -->|从 DDR 读取| BN["BatchNorm"]
        BN -->|写回 DDR| Mem2["DDR Buffer 2"]
        Mem2 -->|从 DDR 读取| Relu["ReLU"]
    end

    subgraph AfterFusion["融合后 (片内单次流水完成)"]
        FusedOp["Fused_Conv_BN_ReLU (片上流水一次完成)"]
    end
```
