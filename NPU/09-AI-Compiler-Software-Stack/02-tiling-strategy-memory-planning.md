# 02 Tiling 切分策略与静态 SRAM 内存复用规划

## 1. 多级循环切块 (Loop Tiling) 空间约束模型

对于大矩阵乘法 $C(M, N) = A(M, K) \times B(K, N)$，设片上 Scratchpad SRAM 总容量为 $C_{SRAM}$（如 2MB）：

```mermaid
graph TD
    GlobalMat["全局 DRAM 大矩阵: A(4096, 4096), B(4096, 4096)"]
    GlobalMat -->|Loop Tiling 切分| Tiles["片上 Micro-Tiles: A_tile(Tm, Tk), B_tile(Tk, Tn)"]
    Tiles --> DoubleBuf["Ping-Pong 双缓冲分配 (SRAM 物理偏移)"]
    DoubleBuf --> ArrayCompute["2D 脉动阵列分块连续累加"]
```

### 1. 双缓冲容量不等式
$$\text{Memory Required} = 2 \times (T_m \times T_k + T_k \times T_n + T_m \times T_n) \times \text{Bytes\_per\_Elem} \le C_{SRAM}$$

### 2. 算力与搬运平衡约束方程
为了实现完全无气泡重叠，Tile 切分必须满足：
$$T_{DMA}(T_m, T_n, T_k) \le T_{Compute}(T_m, T_n, T_k)$$
$$\frac{(T_m \times T_k + T_k \times T_n) \times \text{Bytes\_per\_Elem}}{\text{DRAM Bandwidth}} \le \frac{2 \times T_m \times T_n \times T_k}{\text{Array Peak FLOPS}}$$

---

## 2. 静态内存区间图着色算法 (Interval Graph Coloring)

```mermaid
graph LR
    subgraph TensorLifetimes["张量生命周期区间 (Time Interval)"]
        T0["Tensor 0: [Cycle 0 -> 120]"]
        T1["Tensor 1: [Cycle 50 -> 200] (与 T0 重叠)"]
        T2["Tensor 2: [Cycle 130 -> 300] (与 T0 不重叠)"]
    end
    
    subgraph SRAM_Reuse["SRAM 物理内存复用"]
        BankA["SRAM 偏移 0x0000 -> 赋予 Tensor 0，随后原地复用给 Tensor 2"]
        BankB["SRAM 偏移 0x8000 -> 赋予 Tensor 1"]
    end
    
    T0 & T2 --> BankA
    T1 --> BankB
```

通过在编译期执行区间图着色，NPU 软件栈实现了 **100% 静态分配与 0 内存碎片**，消除了任何运行期 `malloc`/`free` 开销。
