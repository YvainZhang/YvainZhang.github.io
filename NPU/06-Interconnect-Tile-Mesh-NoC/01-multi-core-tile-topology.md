# 01 Multi-Core Tile 空间平铺与分布式 SRAM

## 1. Multi-Tile 空间平铺设计

单颗大算力云端 NPU 通常包含 16~64 个同构计算 Tile：
- **单个 Tile 组成**：1 个 2D 脉动阵列 + 1 个 VPU 向量引擎 + 2MB~8MB 独立 Scratchpad SRAM + 1 个 NoC 路由节点（Router）。
- **分布式 SRAM 统一编址 (NUMA-like)**：每个 Tile 可以直接访问本地 SRAM（超低延迟），亦可通过 NoC 访问其他远端 Tile 的 SRAM。

```mermaid
graph TD
    subgraph MeshTopology["4x4 2D Mesh NoC 拓扑"]
        T00["Tile(0,0)"] <--> T01["Tile(0,1)"] <--> T02["Tile(0,2)"] <--> T03["Tile(0,3)"]
        T10["Tile(1,0)"] <--> T11["Tile(1,1)"] <--> T12["Tile(1,2)"] <--> T13["Tile(1,3)"]
        T20["Tile(2,0)"] <--> T21["Tile(2,1)"] <--> T22["Tile(2,2)"] <--> T23["Tile(2,3)"]
        T30["Tile(3,0)"] <--> T31["Tile(3,1)"] <--> T32["Tile(3,2)"] <--> T33["Tile(3,3)"]
        
        T00 <--> T10 <--> T20 <--> T30
        T01 <--> T11 <--> T21 <--> T31
        T02 <--> T12 <--> T22 <--> T32
        T03 <--> T13 <--> T23 <--> T33
    end
```
