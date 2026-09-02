# Lab 04：Device Tree 与 Platform Driver

本实验展示最小节点与 Platform Driver 匹配。`demo-node.dts` 应合并到目标 QEMU Kernel 的 DTS 或作为 Overlay 使用；不同 Kernel 的 Overlay 流程不同。驱动只读取 `reg` 资源，不访问不存在的硬件。

```bash
make -C /path/to/kernel M=$PWD modules
dtc -I dts -O dtb -o demo-node.dtbo demo-node.dts
```

加载后 `dmesg` 应出现 Resource Base/Size。将 `compatible` 改错，Probe 不再发生；删掉 `reg`，Probe 返回资源错误。实验用于观察 OF Match、Platform Device 和 Resource 获取链。

## 匹配链路

```text
DT 节点 compatible
        │
        ▼
of_match_table 匹配
        │
        ▼
创建/绑定 platform_device
        │
        ▼
调用 demo_probe()
        │
        ▼
platform_get_resource() 读取 reg 资源
```

实验地址上没有真实 QEMU 设备，因此驱动只检查资源，不执行 `ioremap()`，也不读写 MMIO。

## 完整文件内容

### `Makefile`

```makefile
obj-m += demo_driver.o
```

该变量通知 Linux Kbuild 将 `demo_driver.c` 构建为可加载模块 `demo_driver.ko`。

### `demo-node.dts`

```dts
/dts-v1/;
/plugin/;

&{/} {
    demo@10000000 {
        compatible = "soc-kb,demo-device";
        reg = <0x0 0x10000000 0x0 0x1000>;
        status = "okay";
    };
};
```

`compatible` 是驱动匹配键；`reg` 描述起始地址 `0x10000000` 和大小 `0x1000`。四个 Cell 对应父节点常见的两个 Address Cell 和两个 Size Cell，实际项目必须服从目标父节点的 `#address-cells`、`#size-cells` 配置。

### `demo_driver.c`

```c
#include <linux/module.h>
#include <linux/of.h>
#include <linux/platform_device.h>

static int demo_probe(struct platform_device *pdev)
{
    struct resource *resource;
    resource_size_t size;

    /*
     * The example deliberately inspects the resource without mapping or
     * touching it: QEMU has no real device at this teaching address.
     */
    resource = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    if (!resource)
        return dev_err_probe(&pdev->dev, -EINVAL,
                             "missing MMIO resource\n");

    size = resource_size(resource);
    dev_info(&pdev->dev, "MMIO start=%pa size=%pa\n",
             &resource->start, &size);

    return 0;
}

static const struct of_device_id demo_match[] = {
    { .compatible = "soc-kb,demo-device" },
    { }
};
MODULE_DEVICE_TABLE(of, demo_match);

static struct platform_driver demo_driver = {
    .probe = demo_probe,
    .driver = {
        .name = "soc-kb-demo",
        .of_match_table = demo_match,
    },
};
module_platform_driver(demo_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("SoC knowledge-base Device Tree matching example");
```

`MODULE_DEVICE_TABLE()` 导出模块别名供自动加载使用；`module_platform_driver()` 展开为模块初始化和退出注册逻辑；`platform_get_resource()` 将设备树中的 `reg` 转换为内核 `struct resource`。

## 故障注入

1. 将 DTS 中的 `compatible` 改为其他字符串：节点无法与 `demo_match[]` 匹配，`probe()` 不会执行。
2. 删除 `reg`：匹配仍然成功，但 `platform_get_resource()` 返回空，日志出现 `missing MMIO resource`。
3. 将 `status` 改为 `disabled`：内核通常不会为该节点创建可绑定的 Platform Device。
