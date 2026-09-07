# 03 NVSwitch 交换架构与超节点拓扑

## 1. 8-GPU Full-Mesh 与 NVSwitch 架构

在 8 卡服务器内部，若采用全互联（Full-Mesh），需要 $8 	imes 7 / 2 = 28$ 组点对点链路，布线极其复杂。
- **NVSwitch 解决方案**：引入独立的 NVSwitch 交换芯片（单芯片具备数十个 NVLink 端口与几 TB/s 交叉交换能力）。
- **拓扑结构**：8 颗 GPU 均直接连接至 4~6 颗 NVSwitch 芯片，构成无阻塞的 **Crossbar 胖树（Fat-Tree）网络**，实现任意卡间等带宽、单跳（Single-Hop）超低延迟直连。

```mermaid
graph TB
    subgraph NVSwitch_Layer["NVSwitch 交换层 (Crossbar Fabric)"]
        SW0["NVSwitch 0"]
        SW1["NVSwitch 1"]
        SW2["NVSwitch 2"]
        SW3["NVSwitch 3"]
    end

    subgraph GPU_Layer["GPU 计算层 (8-GPU Node)"]
        GPU0["GPU 0"]
        GPU1["GPU 1"]
        GPU2["GPU 2"]
        GPU3["GPU 3"]
        GPU4["GPU 4"]
        GPU5["GPU 5"]
        GPU6["GPU 6"]
        GPU7["GPU 7"]
    end

    GPU0 <--> SW0 & SW1 & SW2 & SW3
    GPU1 <--> SW0 & SW1 & SW2 & SW3
    GPU7 <--> SW0 & SW1 & SW2 & SW3
```
