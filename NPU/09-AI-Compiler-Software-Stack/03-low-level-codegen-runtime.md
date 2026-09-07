# 03 MLIR 方言转换与底层指令生成 (Codegen & Runtime)

## 1. MLIR 多级方言（Dialects）转换流水线

```text
[ PyTorch / ONNX 计算图 ]
        ↓ (Torch-MLIR 前端导入)
[ High-Level Dialect (tosa / linalg) ] : 执行图级优化、常量折叠与算子融合
        ↓ (Tiling & Bufferization Pass)
[ Mid-Level Dialect (memref / affine / vector) ] : 显式内存分配与循环切分
        ↓ (NPU Specific Dialect: 如 npu_dsa)
[ Low-Level Instruction Stream / Microcode ] : 生成含 VLIW 指令与 DMA 描述符的二进制模型包 (.bin/.om)
```
