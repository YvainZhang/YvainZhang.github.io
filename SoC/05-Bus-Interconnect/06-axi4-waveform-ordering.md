# AXI4 五通道时序与乱序

## 写事务：地址和数据没有固定先后

下面的波形中 AW 在 T1 完成，W 在 T2/T3 完成，B 在 T5 返回。`VALID && READY` 的周期才发生 Transfer。

```text
cycle     T0  T1  T2  T3  T4  T5
AWVALID    1   1   0   0   0   0
AWREADY    0   1   1   1   1   1    AW handshake @T1
WVALID     0   0   1   1   0   0
WREADY     1   1   1   1   1   1    W beats @T2,T3
WLAST      0   0   0   1   0   0
BVALID     0   0   0   0   1   1
BREADY     1   1   1   1   0   1    B handshake @T5
```

Source Assert VALID 后必须保持地址/数据/控制稳定，不能因为 READY 低而撤销。Slave 可以先接收 W 再接收 AW，因此内部要能关联或缓存；AXI4 写数据本身不带 WID，同一 Master 的写数据顺序受更严格约束。

## 读事务与 Backpressure

```text
cycle     T0  T1  T2  T3  T4  T5
ARVALID    1   1   0   0   0   0
ARREADY    0   1   0   0   0   0
RVALID     0   0   1   1   1   1
RREADY     1   1   1   0   0   1
RLAST      0   0   0   0   0   1
```

T3/T4 的 RREADY=0 使 Slave 保持 RDATA、RID、RRESP、RLAST 稳定。若 Slave 在此期间改变 RDATA，是协议违例。Backpressure 可沿 NoC 传播并填满上游 Buffer，因此性能计数要观察持续时间而非单个周期。

## ID 与乱序完成

Master 发出 `ARID=3` 的慢 DDR 读，随后发出 `ARID=7` 的片上 SRAM 读；互联可以先返回 ID7，再返回 ID3。Master 用 RID 重组到对应请求。对同一 ID，返回顺序受规范约束；不同 ID 允许更大自由度。

Reordering Buffer 深度限制有效 Outstanding。Master 宣称支持 32 个事务，但下游 Bridge 只能容纳 4 个时，第 5 个地址就会受到 Backpressure。评估端到端能力要取路径上最窄环节，并区分读、写地址、写数据和响应各自容量。

## 4 KiB 边界

AXI Burst 不能跨越 4 KiB 地址边界。起始 `0x0FF0`、每 Beat 8 B、4 Beats 会覆盖到 `0x100F`，属于非法 Burst，Master 必须拆成两次。DMA Descriptor 若允许任意地址长度，硬件或驱动要负责切分。

## Exclusive Access

Exclusive Read 建立监视，Exclusive Write 仅在监视仍有效时返回成功。总线 `EXOKAY` 与 CPU 原子语义相关，但并非所有 Slave 支持；对 Device Register 使用 Exclusive 还受架构属性限制。原子系统设计应确认 CPU、互联和 Target 整条路径都支持。
