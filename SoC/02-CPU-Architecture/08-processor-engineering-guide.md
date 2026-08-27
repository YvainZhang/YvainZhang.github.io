# 处理器架构与并发编程工程陷阱与实战避坑指南

## 1. 内存模型与并发编程核心陷阱

### 陷阱 1：弱内存序平台下的无锁发布失效
- **现象**：生产者线程填充数据缓冲区后置位 `flag = 1`；消费者线程检测到 `flag == 1` 时读取数据，偶尔读出全零或未初始化的垃圾数据。
- **根因**：在 ARM / RISC-V 弱内存序（Weak Memory Ordering）架构下，CPU 的 Store Buffer 允许普通写操作乱序重排，`flag = 1` 的写入先于数据缓冲区的写入刷新到全局内存。
- **规范规避**：使用 C11 / C++11 明确的 Acquire-Release 语义：
  ```c
  /* 生产者: Release 屏障发布 */
  atomic_store_explicit(&flag, 1, memory_order_release);

  /* 消费者: Acquire 屏障接收 */
  if (atomic_load_explicit(&flag, memory_order_acquire) == 1) {
      process(buffer); /* 保证能看到完整的数据 */
  }
  ```

### 陷阱 2：高并发原子争用下的活锁风暴（Live-lock Storm）
- **现象**：多核系统在 64 核心高并发抢占同一个自旋锁时，CPU 利用率 100%，但整体吞吐量跌至接近零。
- **根因**：基于 AArch64 `LDXR/STXR`、AArch32 `LDREX/STREX` 或 RISC-V `LR/SC` 的独占重试循环，在极度争用下会产生大量失败重试和 Cacheline 所有权迁移；系统可能长期消耗带宽处理一致性事务，而有效业务吞吐显著下降。
- **规范规避**：在支持 ARMv8.1+ 或 RISC-V A 扩展的硬件上，优先使用 **LSE（如 `LDADD`, `CAS`）/ AMO 单指令原子操作** 代替软件独占重试循环；在支持 CHI/AXI5 Far Atomic 的系统互联平台上，原子操作还可在互联端就地聚合执行以缓解总线争用。

---

## 2. 异常与特权级核心工程陷阱

### 陷阱 1：内核栈溢出引发的 Double Fault 级联死锁
- **现象**：内核在深层递归或大局部变量申请时触发 Data Abort，随后 CPU 彻底静默死机，无任何 Panic 打印。
- **根因**：当前内核栈（`SP_EL1`）已耗尽，触发 Data Abort 后硬件尝试将现场压入当前的 `SP_EL1` 栈中，瞬间再次触发第二个栈越界 Data Abort，硬件判定为不可恢复的 Double Fault 直接停止流水线。
- **规范规避**：在 Linux 内核配置中使能 `CONFIG_VMAP_STACK`，为每个 CPU 核心分配带保护页（Guard Page）的独立映射栈，并在异常入口检测栈指针合法性。

### 陷阱 2：自旋锁在中断上下文中未关中断导致单核死锁
- **现象**：驱动在获取普通 `spin_lock()` 后，同核心触发硬中断并再次尝试获取同一把锁，导致该核心永久死锁。
- **规范规避**：当自旋锁可能被当前核心的硬中断服务程序抢占访问时，线程上下文中获取锁必须使用 `spin_lock_irqsave(&lock, flags)` 或 `spin_lock_irq()` 禁用本地中断；若仅在跨核线程间竞争且不在中断上下文使用，则普通 `spin_lock()` 即可。

---

## 3. CPU 调试排查速查表

| 故障特征 | 典型根因 | 定位方法 |
| :--- | :--- | :--- |
| 次核启动超时 | 启动入口写回未刷 Cache 或 PSCI 未唤醒 | 读取次核 PC，检查 `SCR_EL3` 与 Mailbox |
| Data Abort on MMIO | 访问已关断电源域或时钟关闭的外设 | 检查 `ESR_EL1` DFSC 状态码与外设 PCLK |
| 多核死锁无响应 | 中断重入获取自旋锁或无序锁依赖 | 分析各核 Backtrace，构建 Wait-for Graph |
