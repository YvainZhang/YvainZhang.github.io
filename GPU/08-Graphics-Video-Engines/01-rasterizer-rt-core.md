# 01 光栅化硬件流水线与 RT Core 光线追踪引擎

## 1. 硬件光栅化流水线 (Rasterization Engine)

```mermaid
graph LR
    Triangles["三角形顶点 (Primitives)"] --> Setup["Triangle Setup / Slope Engine"]
    Setup --> CoarseRaster["粗光栅化 (Coarse Raster, 16x16 块判定)"]
    CoarseRaster --> FineRaster["细光栅化 (Fine Raster, 生成像素片段)"]
    FineRaster --> ZCull["Early-Z 深度剔除引擎"]
    ZCull --> PixelShader["分派至 SM 执行 Pixel Shader"]
```

---

## 2. RT Core (Ray Tracing Core) 硬件求交加速

光线追踪的核心算力开销在于遍历 BVH（层次包围盒）树与三角形几何求交：
- **硬件 BVH 遍历单元**：在片上由硬件状态机直接执行 BVH AABB 节点测试与子节点下钻，无需消耗 SM 的通用 ALU 算力。
- **Ray-Triangle 求交单元**：硬件单周期执行 Möller–Trumbore 光线-三角形相交计算，实现数倍于软件遍历的能效。
