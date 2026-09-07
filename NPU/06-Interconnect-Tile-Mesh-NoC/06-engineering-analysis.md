# 06 片上 NoC Bisection 带宽与多播增益推导

## 1. 4x4 2D Mesh NoC 对分带宽 (Bisection Bandwidth)

对于规则的 $4 \times 4$ 2D Mesh 片上网络拓扑：
- **链路规格**：单向数据位宽 256-bit，双向 512-bit，工作频率 $f_{NoC} = 1.5\text{ GHz}$；
- **单物理链路双向带宽**：
  $$B_{link} = \frac{512\text{ bit} \times 1.5\text{ GHz}}{8\text{ bit/Byte}} = 96\text{ GB/s}$$
- **对分截面（Bisection Cut）**：将 16-Tile 网格对半切开，跨越 4 条双向物理链路：
  $$\text{Bisection Bandwidth} = 4 \times B_{link} = 4 \times 96\text{ GB/s} = \mathbf{384\text{ GB/s}}$$

```mermaid
graph TD
    subgraph MeshBisection["4x4 Mesh 对分截面剖析 (4 条切割链路)"]
        T01["Tile(0,1)"] <-->|Link 0 (96 GB/s)| T02["Tile(0,2)"]
        T11["Tile(1,1)"] <-->|Link 1 (96 GB/s)| T12["Tile(1,2)"]
        T21["Tile(2,1)"] <-->|Link 2 (96 GB/s)| T22["Tile(2,2)"]
        T31["Tile(3,1)"] <-->|Link 3 (96 GB/s)| T32["Tile(3,2)"]
    end
```

---

## 2. 硬件多播 (Multicast Tree) 相比单播的流量节省模型

在数据并行或大模型前向推理中，单个 64MB 权重块需同时广播分发至全部 16 个 Tile：
- **平均传输跳数（Average Hop Count）**：在 $4 \times 4$ 网格中，平均曼哈顿距离 $\bar{H} = \frac{2}{3} \times 4 \approx 2.67\text{ hops}$；
- **传统单播方式总流量 (Unicast Total Flit-Hops)**：
  $$\text{Traffic}_{unicast} = 15 \times 64\text{ MB} \times \bar{H} \approx 15 \times 64 \times 2.67 = \mathbf{2563.2\text{ MB}\cdot\text{hops}}$$
- **硬件多播树方式总流量 (Multicast Tree Flit-Hops)**：
  - 数据包仅在分支路由器复制，生成一棵覆盖 16 个节点的生成树（Spanning Tree），恰好占用 15 条物理链路：
  $$\text{Traffic}_{multicast} = 15\text{ links} \times 64\text{ MB} = \mathbf{960.0\text{ MB}\cdot\text{hops}}$$
- **网络能耗与拥塞节省率**：
  $$\text{Saving Ratio} = \frac{2563.2 - 960.0}{2563.2} = \mathbf{62.54\%}$$
