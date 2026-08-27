# 04 MMU 与地址空间

本模块讲清 VA 到 PA 的转换、页表和 TLB 的一致性，以及 MPU/IOMMU 如何把同一套“地址与权限”思想扩展到实时核和 DMA 设备。

1. [地址空间与多级页表](01-address-page-table.md)
2. [TLB、权限与内存属性](02-tlb-attributes.md)
3. [MPU、IOMMU/SMMU 与虚拟化](03-mpu-iommu.md)
4. [映射流程与 Fault 分析](04-mapping-fault.md)
5. [页表计算与失效推演](05-engineering-analysis.md)
6. [ARM 4 KiB 四级页表与内存属性](06-arm64-page-table-attributes.md)
7. [SMMU 嵌套翻译、ATS、PRI 与 PASID](07-smmu-ats-pasid.md)
8. [地址翻译工程问题与规避](08-address-translation-engineering-guide.md)
