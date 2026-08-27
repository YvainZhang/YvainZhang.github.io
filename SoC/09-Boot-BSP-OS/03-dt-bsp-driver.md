# Device Tree 体系、Linux 驱动模型与 Platform 匹配机制完全指南

## 1. Device Tree 全生命周期：从源码 DTS 到内核 Device Node 树

在现代 ARM/RISC-V 架构中，设备树（Device Tree）用于解耦硬件描述与操作系统内核代码。其全生命周期处理流水线如下：

```mermaid
flowchart TD
    DTS["1. 硬件描述源文件: SoC dtsi + Board dts"] --> DTC["2. 设备树编译器 (DTC: Device Tree Compiler)"]
    DTC --> DTB["3. 平坦设备树二进制文件 (DTB: Flat Device Tree)\n• FDT Header (魔数 0xd00dfeed)\n• Memory Reservation Block\n• Structure Block (Token 流: OF_DT_BEGIN_NODE)\n• Strings Block (字符串池)"]

    DTB --> Bootloader["4. U-Boot 加载 DTB 并通过 x0/a1 传给 Linux Kernel"]

    subgraph Kernel_Init ["5. Linux 内核解析与设备实例化 (start_kernel)"]
        Early_Scan["early_init_dt_scan()\n早期扫描 bootargs 与 memory 节点"] --> Unflatten["unflatten_device_tree()\n在内存中将平坦二进制展开为树状拓扑 struct device_node"]
        Unflatten --> Populate["of_platform_default_populate()\n遍历树节点, 为包含 compatible 属性的节点创建 struct platform_device 并挂入 platform_bus_type"]
    end

    Bootloader --> Kernel_Init
```

---

## 2. Platform 驱动匹配算法与 Probe 执行全景图

Linux 内核总线驱动模型（Bus-Device-Driver Model）在设备或驱动注册时，自动触发匹配与探测流水线：

```mermaid
flowchart TD
    Reg["驱动或设备注册 (platform_driver_register)"] --> Match_Order

    subgraph Match_Order ["总线匹配五级优先级 (platform_match)"]
        M1["1. driver_override: 检查是否显式指定驱动覆盖"]
        M2["2. of_driver_match_device: 比对 DTS compatible 字符串 (最核心)"]
        M3["3. acpi_driver_match_device: 比对 ACPI 硬件 ID"]
        M4["4. platform_match_id: 比对 platform_device_id 表"]
        M5["5. 传统名字比对: strcmp(pdev->name, pdrv->driver.name)"]

        M1 --> M2 --> M3 --> M4 --> M5
    end

    M2 -->|匹配成功| Probe_Exec

    subgraph Probe_Exec ["标准 Probe 初始化资源序列"]
        S1["1. 映射 MMIO: devm_platform_ioremap_resource(pdev, 0)"]
        S2["2. 获取中断: platform_get_irq(pdev, 0)"]
        S3["3. 获取时钟与复位: devm_clk_get() / devm_reset_control_get()"]
        S4["4. 设置 DMA 掩码: dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64))"]
        S5["5. 注册中断与上层子系统: devm_request_irq() / register_netdev()"]

        S1 --> S2 --> S3 --> S4 --> S5
    end
```

---

## 3. 依赖反转与延迟探测（Deferred Probe）微架构机制

### 为什么需要 Deferred Probe？
在 Linux 内核启动过程中，驱动加载顺序通常是并发且不确定的。如果设备驱动 A（如网卡驱动）在 `probe()` 过程中需要请求 GPIO 控制器 B 提供的复位引脚，而 GPIO 驱动 B 此时尚未完成加载与注册，驱动 A 无法获取该资源。

```mermaid
sequenceDiagram
    participant PDev as 网卡平台设备 (Platform Device)
    participant Driver as 网卡驱动 probe()
    participant Core as Linux Driver Core
    participant GPIO as GPIO 控制器驱动

    PDev->>Driver: 触发第一次 probe()
    Driver->>Core: devm_gpiod_get(&pdev->dev, "reset")
    Core-->>Driver: 返回 -EPROBE_DEFER (GPIO Provider 尚未注册)
    Driver->>Core: 退出 probe 并返回 -EPROBE_DEFER
    Core->>Core: 将该网卡设备挂入 deferred_probe_pending_list 队列

    Note over GPIO: 稍后, GPIO 控制器驱动成功完成 probe()
    GPIO->>Core: 注册完成通知
    Core->>Core: 触发 driver_deferred_probe_trigger() 唤醒工作队列
    Core->>Driver: 重新对网卡设备发起第二次 probe() (成功获取 GPIO 资源并完成初始化!)
```

---

## 4. Device Tree 核心节点编写与语法约束

```dts
/* 典型 SoC 片上外设节点定义 */
uart0: serial@1c28000 {
    compatible = "ns16550a", "snps,dw-apb-uart"; /* 优先匹配具体厂商，次选通用驱动 */
    reg = <0x0 0x01c28000 0x0 0x1000>;         /* 64位基地址与 4KB 长度 */
    interrupts = <GIC_SPI 48 IRQ_TYPE_LEVEL_HIGH>;/* GIC SPI 中断号 48，高电平触发 */
    clocks = <&ccu CLK_BUS_UART0>, <&ccu CLK_UART0>;
    clock-names = "pclk", "sclk";
    resets = <&ccu RST_BUS_UART0>;
    pinctrl-names = "default";
    pinctrl-0 = <&uart0_pins>;
    status = "okay";                           /* 开启该设备 */
};
```

---

## 5. 常见设备树与驱动匹配故障排查手册

| 故障现象 | 硬件/DTS 语法根因 | 诊断手段与修复方法 |
| :--- | :--- | :--- |
| **设备节点未生成 `platform_device`** | 节点缺少 `compatible` 属性，或父节点为非总线节点且未声明 `simple-bus` | 检查节点是否包含合法的 `compatible`；若为子节点，确保父节点的 compatible 包含 `"simple-bus"` |
| **`reg` 地址解析错误导致访存崩溃** | 父节点的 `#address-cells` 与 `#size-cells` 与子节点 `reg` 数组的元组长度不匹配 | 检查父节点的 cells 声明（64位地址通常 `#address-cells = <2>`, `#size-cells = <2>`） |
| **驱动 Probe 永远不被调用** | DTS 中的 `compatible` 字符串与驱动源码中 `of_match_table` 存在大小写或下划线拼写差异 | 查看 `/sys/firmware/devicetree/base/` 确认加载的实际 DTS 内容；对比 `modinfo` 中的匹配表 |
| **系统无限死锁在 Deferred Probe** | 存在环形依赖（如 A 依赖 B 的 Clock，B 依赖 A 的 Regulator） | 启用内核调试参数 `initcall_debug`，查看 `deferred_probe` 循环超时警告 |
