# 生产环境 Crashdump 转储流水线、Kdump 与 Ramoops 机制完全指南

## 1. Linux 内核崩溃转储（Kdump）两阶段内核架构

在企业级与生产环境中，当内核遭遇 Panic 崩溃时，**Kdump** 机制能够瞬间唤醒一个预先保留在独立内存中的第二内核（Capture Kernel），将崩溃前系统的完整物理内存转储为 `vmcore`：

```mermaid
flowchart TD
    subgraph Crash_Kernel_Flow ["Kdump 架构全景流程"]
        P1["1. 生产内核运行中 (Primary Production Kernel)"] --> Panic["触发严重未捕获异常: Kernel Panic!"]

        Panic --> Machine_Kexec["2. machine_kexec(): 绕过 BIOS/Bootloader, 瞬间跳转至预留 Crash 内存"]

        subgraph Reserved_Memory ["预留物理内存区域 (crashkernel=512M)"]
            Kexec_Kernel["3. 捕获内核启动 (Capture Kernel)\n• 运行在独立的物理内存空间\n• 不依赖原崩溃内核的任何页表与数据结构"]
        end

        Machine_Kexec --> Kexec_Kernel

        Kexec_Kernel --> Dump_Tool["4. makedumpfile 工具:\n• 访问 /proc/vmcore (读取主内核全部物理内存)\n• 过滤零页与缓存页, 压缩并持久化存储至 NVMe / 网络 NFS"]

        Dump_Tool --> Reboot["5. 自动重启恢复生产环境"]
    end
```

---

## 2. 嵌入式常开内存转储：`pstore / ramoops` 机制

在资源受限的嵌入式设备中（无法运行 Kdump），Linux 采用 **`pstore/ramoops`** 机制：

```mermaid
flowchart LR
    Panic_Event["内核 Panic / Oops"] --> Pstore_Driver["pstore 内核驱动\n(在异常处理最后阶段调用)"]

    Pstore_Driver --> AON_RAM["写入物理保留 RAM (Ramoops Area)\n(预留的 Persistent RAM 物理地址: no-map)"]

    AON_RAM --> Cold_Warm_Reset["硬件看门狗触发重启"]

    Cold_Warm_Reset --> Next_Boot["新内核启动, pstore 挂载至 /sys/fs/pstore/"]
    Next_Boot --> Read_Log["提取 dmesg-ramoops-0 还原崩溃前日志!"]
```

- **DTS 配置范例**：
  ```dts
  reserved-memory {
      ramoops: ramoops@88000000 {
          compatible = "ramoops";
          reg = <0x0 0x88000000 0x0 0x00100000>; /* 1MB 预留物理内存 */
          record-size = <0x20000>;              /* 128KB 崩溃日志块 */
          console-size = <0x20000>;             /* 控制台日志 */
          pmsg-size = <0x20000>;
      };
  };
  ```

---

## 3. 使用 GDB 与 Crash 工具实战反解 `vmcore`

```bash
# 启动 crash 调试工具分析崩溃现场
crash vmlinux vmcore

# 核心命令实战:
crash> bt           # 1. 打印崩溃现场的完整函数调用栈 (Backtrace)
crash> struct task_struct 0xffff800010203040 # 2. 检查引发崩溃的当前进程上下文
crash> log          # 3. 提取崩溃发生前 dmesg 环形缓冲区中的最后系统日志
crash> kmem -s      # 4. 检查 SLUB 内存分配器是否存在泄漏与破坏
crash> ps | grep D  # 5. 查找处于不可中断睡眠 (D 状态) 发生死锁的进程
```
