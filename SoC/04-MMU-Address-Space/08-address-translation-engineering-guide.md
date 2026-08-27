# 地址翻译与 MMU/SMMU 子系统工程陷阱与实战避坑指南

## 1. 页表与 MMU 核心工程陷阱与规避

### 陷阱 1：修改页表未遵循 BBM（Break-Before-Make）导致 TLB 冲突
- **现象**：在将 2MB 大页拆分为 4KB 小页，或修改页表映射属性时，多核 CPU 随机触发 `TLB Conflict Abort` 崩溃或不可预期的数据错误。
- **根因**：ARM 架构规范将直接原地覆写有效描述符定义为 CONSTRAINED UNPREDICTABLE。微架构的不同级 TLB（Micro-TLB 与 Main TLB）可能同时命中重叠条目。
- **规范规避**：严格执行 5 步 BBM 序列：先写无效值（Invalid） $\to$ `DSB ISHST` $\to$ `TLBI VAAE1IS` $\to$ `DSB ISH + ISB` $\to$ 写新描述符。在支持 ARMv8.4-A `FEAT_BBM` 的核心上可按架构细则优化特定属性变更。

### 陷阱 2：MMIO 寄存器误配为 Normal Memory 导致硬件副作用紊乱
- **现象**：外设 FIFO 偶发丢数据，或者写寄存器时外设无响应。
- **根因**：DTS 或页表将 MMIO 区域配置为 `Normal Cacheable` 或 `Normal Non-Cacheable`，导致 CPU 乱序执行引擎对寄存器发起**投机性预读（Speculative Read）** 或 **写合并（Write Merging）**，触发只读/清除副作用。
- **规范规避**：所有外设 MMIO 必须使用 `Device-nGnRE` 或 `Device-nGnRnE` 属性映射（Linux 内核中必须严格通过 `ioremap()` 建立映射）。

---

## 2. SMMU / IOMMU 核心工程陷阱与规避

### 陷阱 1：DMA 进行中提前 Unmap 解除映射（IOMMU Fault）
- **现象**：系统在高并发压力测试下，dmesg 频繁刷屏 `arm-smmu-v3: Unhandled context fault: fsr=0x2`。
- **根因**：驱动在超时处理分支中，先调用了 `dma_unmap_single()` 释放了 IOVA 页表，但物理外设并未完全停止，外设发出的下一个 AXI 事务在 SMMU 端查表失败触发严重的中止。
- **规范规避**：必须严格遵循**先下发硬件停止命令 $\to$ 轮询确认外设空闲 $\to$ 最后调用 `dma_unmap_*`** 的生命周期规范。

### 陷阱 2：SMMU CMDQ 命令队列与 CPU 缓存不同步
- **现象**：向 SMMU 提交 `CMD_CFGI_STE` 或 `CMD_TLBI_NH_VA` 后，执行 `CMD_SYNC` 超时挂死。
- **根因**：SMMU 访问内存中的 Command Queue 时未配置为 Shareable WB，CPU 写入的命令尚未刷出 Cache，SMMU 硬件读到全零空命令导致队列卡死。
- **规范规避**：在 BSP 初始化时，确保 `SMMU_CBn_TCR` 及相关基地址寄存器的内存属性严格配置为 `Inner-Shareable Write-Back`。

---

## 3. 地址翻译与页表排查速查清单

- [ ] 动态修改页表时是否完整执行了 BBM（Break-Before-Make）5 步序列？
- [ ] 外设 MMIO 寄存器映射是否使用了 `Device-nGnRE` 或 `Device-nGnRnE` 属性？
- [ ] SMMU 驱动是否在停止外设物理 DMA 之后才解除 IOVA 映射？
