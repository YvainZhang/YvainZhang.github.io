# 跨模块案例

案例不绑定特定厂商实现，重点展示怎样从现象建立跨层证据链。

1. [STA 从扫描到 DHCP](01-sta-connect-dhcp.md)：把“连接不上”拆成可判定的状态。
2. [USB RX 吞吐瓶颈](02-usb-rx-throughput.md)：用计数守恒定位 Host Interface 背压。
3. [ADDBA 异常导致业务失败](03-addba-failure.md)：从控制帧走到 reorder 与 DHCP。
4. [休眠唤醒后断流](04-resume-no-traffic.md)：对齐 Host、总线、Firmware 与 AP 状态。

每个案例都按现象、假设、最小证据、定位和回归组织。实际项目中应替换为目标平台的接口，并在分享前移除设备标识、内部地址与客户信息。
