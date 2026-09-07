# 02 空间架构与数据流拓扑 (Spatial Architecture)

## 1. 空间计算 (Spatial Computing) 微架构拓扑

```mermaid
graph TD
    subgraph Systolic2D["2D 脉动阵列空间数据流 (Weight-Stationary 模式)"]
        ActIn0["Act In 0 (Row 0)"] --> PE00["PE (0,0)<br/>W[0,0]"]
        PE00 -->|Act Out -> Act In| PE01["PE (0,1)<br/>W[0,1]"]
        PE01 -->|Act Out -> Act In| PE02["PE (0,2)<br/>W[0,2]"]
        
        ActIn1["Act In 1 (Row 1)"] --> PE10["PE (1,0)<br/>W[1,0]"]
        PE10 -->|Act Out -> Act In| PE11["PE (1,1)<br/>W[1,1]"]
        PE11 -->|Act Out -> Act In| PE12["PE (1,2)<br/>W[1,2]"]

        PE00 -->|Psum South| PE10
        PE01 -->|Psum South| PE11
        PE02 -->|Psum South| PE12
        
        PE10 --> Out0["Out Sum 0"]
        PE11 --> Out1["Out Sum 1"]
        PE12 --> Out2["Out Sum 2"]
    end
```

- **水平数据流（West $\rightarrow$ East）**：激活特征图沿行向东流动，每个时钟周期传递至下一个相邻 PE；
- **垂直数据流（North $\rightarrow$ South）**：部分和（Partial Sum）沿列向南累加流动，在底部流出最终矩阵乘结果。
