# 网卡/NVMe Ring 与 Scatter-Gather

## 网卡 RX Ring

RX Descriptor 常包含 Buffer DMA Address、Buffer Length、Packet Length、Checksum/VLAN 状态和 Ownership。软件维护 Clean/Next-to-use，硬件维护 Consumer/Head；双方通过 Doorbell 和 Completion 状态协调。

```text
             software posts buffers →
        +------+------+------+------+------+
ring    | HW   | HW   | DONE | CPU  | free |
        +------+------+------+------+------+
          ^              ^
       HW head       SW clean index
```

驱动补充 Buffer：分配 Page/SKB，Map 为 FROM_DEVICE，写 DMA Address，Barrier 后交 Ownership，最后批量更新 Tail。收包：观察 Completion，Barrier 后读长度/状态，Sync-for-CPU，构造 SKB；若 Page 可循环使用，则处理所有权后重新 Sync-for-device。

Ring Size 不是越大越好。大 Ring 能吸收短时突发，却增加内存占用和排队延迟；太小则软件稍迟就 Ring Empty。Interrupt Coalescing 与 NAPI Budget 共同决定吞吐和尾延迟。

## NVMe Submission/Completion Queue

NVMe SQE 通常 64 Byte，包含 Opcode、Command ID、Namespace、PRP/SGL 指针等；CQE 通常 16 Byte，包含 Result、SQ Head、SQ ID、Command ID、Status/Phase。Host 写 SQE、执行 Barrier、更新 Submission Queue Tail Doorbell；Controller 消费后写 CQE，并用 MSI-X 通知。

CQ 使用 Phase Tag 区分新旧 Wrap：初始化 Phase 为 1，Consumer 走完 Ring 后翻转期望 Phase。仅比较 Head/Tail 不足以在异步设备中可靠识别新 Completion。

## PRP 与 SGL

NVMe PRP1 指向首个数据页中的起始位置；跨第二页时 PRP2 可直接指第二页，再大则 PRP2 指向 PRP List。SGL 用 Descriptor 表示任意段，更适合复杂 Scatter-Gather。构造时要遵守 Controller Page Size、对齐和最大段限制。

## Queue Reset

超时后不能立即释放所有 Command Buffer。先停止提交，禁用/Reset Controller，确认 DMA Quiescent，再处理未完成 Command 并 Unmap。Completion 可能与 Reset 并发到达，Command ID 必须有 Generation 或状态机，防止旧 CQE 完成新请求。

## 字节序与结构布局

硬件 Descriptor 通常规定 Little-endian。C Bitfield 布局由 ABI/编译器决定，不适合直接映射硬件格式；使用固定宽度整数、Mask/Shift、`cpu_to_le*` 和 `static_assert(sizeof(...))`。Descriptor 地址与 Ring Base 的对齐也应静态和运行时双重检查。
