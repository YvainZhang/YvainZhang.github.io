# Lab 04：Device Tree 与 Platform Driver

本实验展示最小节点与 Platform Driver 匹配。`demo-node.dts` 应合并到目标 QEMU Kernel 的 DTS 或作为 Overlay 使用；不同 Kernel 的 Overlay 流程不同。驱动只读取 `reg` 资源，不访问不存在的硬件。

```bash
make -C /path/to/kernel M=$PWD modules
dtc -I dts -O dtb -o demo-node.dtbo demo-node.dts
```

加载后 `dmesg` 应出现 Resource Base/Size。将 `compatible` 改错，Probe 不再发生；删掉 `reg`，Probe 返回资源错误。实验用于观察 OF Match、Platform Device 和 Resource 获取链。
