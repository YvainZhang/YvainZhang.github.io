# 03 PCIe ATS / PASID 与异构内存共享 (SVM/HMM)

## 1. PCIe ATS (Address Translation Services) 协议

在开放异构计算中，GPU 作为 PCIe 端点可直接向 Host CPU 的 IOMMU 请求地址转换：
- **ATS Request**：GPU 携带进程地址空间标识符（PASID）向 Host 发送虚拟地址转换请求。
- **ATS Completion**：Host IOMMU 查找 Host 页表，将对应的 Host 物理地址（HPA）返回给 GPU 端点。
- **PRI (Page Request Interface)**：当 Host 发生缺页时，GPU 通过 PRI 报文通知 Host 操作系统进行 Page-in 换页。

---

## 2. Linux HMM (Heterogeneous Memory Management)

Linux 内核主线通过 HMM 框架实现了系统级无缝内存共享：
- 驱动通过 `hmm_range_fault()` 将 CPU 进程的匿名虚拟内存页面安全镜像映射至 GPU 页表中，支持 C++ 原生指针与动态分配（`malloc` / `std::vector`）直接在 GPU 核心内解引用。
