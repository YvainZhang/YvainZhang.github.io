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
