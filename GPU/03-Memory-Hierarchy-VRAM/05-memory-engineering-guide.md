# 05 存储系统工程问题排查与规避

## 1. 显存系统常见故障与调优清单

| 故障现象 | 根因诊断 | 推荐解决方案 |
| :--- | :--- | :--- |
| **Shared Memory Bank Conflict** | 二维数组按列访问或步长为 32 的倍数 | 二维数组填充 Padding（如 `float s[32][33]` 消除 32-stride 冲突） |
| **显存带宽打不满 (< 50% Peak)** | 访存未对齐，触发非合并访存 (Uncoalesced Access) | 使用 `float4` / `int4` 向量化加载，保证 128-bit 对齐 |
| **XID 48 / ECC Single-bit Error** | HBM 颗粒遭受宇宙射线或工作温度过高 | 开启硬件 ECC 自动纠错，记录告警日志并监控翻转频次 |
| **XID 63 / Row Remapping Exhausted** | HBM 坏行过多，硬件可用备用行已耗尽 | 标记该 GPU 硬件降级或申请 RMA 更换物理卡 |

---

## 2. Shared Memory Padding 消除 32-Bank 冲突代码实战

```cuda
// 存在 32-Way 严重冲突的代码 (stride = 32)
__shared__ float tile[32][32]; 
float val = tile[threadIdx.x][threadIdx.y]; // 所有线程映射到同一个 Bank 0！

// 优化后：增加 1 列 Padding 消除冲突
__shared__ float tile_padded[32][32 + 1]; 
float val_opt = tile_padded[threadIdx.x][threadIdx.y]; // 完美错开 32 个 Bank！
```
