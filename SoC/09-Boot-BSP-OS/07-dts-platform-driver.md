# DTS 语法、OF 解析与 Platform Driver

## 节点与属性

```dts
uart0: serial@11000000 {
    compatible = "acme,a1-uart", "ns16550a";
    reg = <0x0 0x11000000 0x0 0x1000>;
    interrupts = <GIC_SPI 40 IRQ_TYPE_LEVEL_HIGH>;
    clocks = <&cru CLK_UART0_BUS>, <&cru CLK_UART0_CORE>;
    clock-names = "bus", "core";
    resets = <&cru RST_UART0>;
    status = "okay";
};
```

`#address-cells/#size-cells` 决定 `reg` 中地址和长度各占多少 Cell；上例各 2 个 Cell，表示 64-bit。Interrupt Specifier 的 Cell 数由 Interrupt Parent 决定，不能脱离 Binding 猜测。

Phandle 把 Consumer 指向 Provider。Clock 的最后一个 Cell 是 Provider 自定义 ID；Reset、DMA、IOMMU 也采用类似模式。Pin Control 通常用 `pinctrl-0` 和 `pinctrl-names` 引用状态。

## 匹配与 Probe

```c
static const struct of_device_id a1_uart_of_match[] = {
    { .compatible = "acme,a1-uart", .data = &a1_soc_data },
    { }
};
MODULE_DEVICE_TABLE(of, a1_uart_of_match);

static struct platform_driver a1_uart_driver = {
    .probe = a1_uart_probe,
    .remove = a1_uart_remove,
    .driver = {
        .name = "a1-uart",
        .of_match_table = a1_uart_of_match,
    },
};
module_platform_driver(a1_uart_driver);
```

Driver Core 用 OF Match Table 匹配节点并创建 Platform Device。Probe 中使用 `devm_platform_ioremap_resource()`、`platform_get_irq()`、`devm_clk_get()` 等取得资源。Provider 未就绪可能返回 `-EPROBE_DEFER`，驱动应原样传播，而不是转换成永久失败。

OF 常用解析接口包括 `of_property_read_u32()`、`of_parse_phandle()` 和 `of_device_get_match_data()`；能用通用子系统取得的资源，不应自行解析寄存器控制 Clock/Reset。

## Schema

YAML Binding 约束 `compatible`、必需属性、Cell 数和额外属性。`make dt_binding_check` 检查 Schema，`make dtbs_check` 用它验证 DTS。编译器只检查语法和 Phandle，不知道一个设备是否漏写 Clock。
