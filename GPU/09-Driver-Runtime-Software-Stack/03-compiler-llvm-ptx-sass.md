# 03 LLVM 后端代码生成与 PTX 到 SASS 编译体系

## 1. 现代 GPU 编译工具链层次 (以 CUDA / NVCC 为例)

```text
[ CUDA C++ / Triton 源代码 ]
        ↓ (Clang / NVCC 前端)
[ LLVM IR (高层通用中间表示) ]
        ↓ (NVPTX 后端代码生成器)
[ PTX (Parallel Thread Execution - 虚拟机器指令集, 具备向前兼容性) ]
        ↓ (PTX JIT Compiler / ptxas 汇编器)
[ SASS (Streaming Assembler - 对应具体物理芯片微架构的真实机器二进制指令) ]
```

---

## 2. PTX 与 SASS 指令对照分析

| 语义 | 虚拟指令 (PTX) | 真实物理微架构指令 (SASS - Hopper/Blackwell) |
| :--- | :--- | :--- |
| **浮点乘加** | `fma.rn.f32 %f3, %f1, %f2, %f0;` | `FFMA R3, R1, R2, R0;` |
| **矩阵张量计算** | `mma.sync.aligned.m16n8k16.row.col ...` | `HMMA.16816.F32 R4, R8, R12, R16;` |
| **共享内存加载** | `ld.shared.f32 %f0, [%r1];` | `LDS.U.32 R0, [R1];` |
| **线程同步** | `bar.sync 0;` | `BAR.SYNC 0x0;` |
