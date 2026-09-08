# 06 Linux 音频驱动开发规范

## 1. 硬件解决什么问题：高可靠音频驱动开发准则与防死锁红线

音频驱动既有严苛的纳秒级中断实时性，又包含毫秒级的 I2C 慢速总线控制和复杂的电源休眠恢复流程。
经验不足的驱动编写极易引发**内核死锁（Spinlock Deadlock）、睡眠中调度异常（Scheduling while atomic）以及休眠唤醒爆音**。

---

## 2. 音频驱动开发的四大工程红线

1. **中断上下文绝对禁止调用耗时操作**：在 DMA 中断服务例程（ISR）与 `trigger()` 回调中，严禁调用 `msleep()`、`mutex_lock()` 或任何可能引起休眠的函数。必须使用自旋锁 `spin_lock_irqsave()`，且临界区耗时应 $< 5\mu\text{s}$。
2. **I2C 寄存器缓存（Regmap Cache）**：Codec 芯片通常包含数百个寄存器。系统在运行时频繁读取寄存器状态，严禁每次都发起低速 I2C 物理传输。驱动**必须集成 Linux 内核的 `regmap` 框架**，启用内存镜像缓存（`REGCACHE_RBTREE` 或 `REGCACHE_FLAT`），将读取速度提升千倍以上。
3. **休眠唤醒（Suspend/Resume）完全对称性**：系统进入 `suspend` 时，必须由 Machine 驱动统一先静音功放、再关闭 Codec、最后停止 DMA；在 `resume` 时，**必须使用完全相反的倒序恢复执行**。
4. **环形缓冲指针对齐校验**：在暴露给 ALSA 核心的 `pointer()` 回调中，计算出的 `hw_ptr` **必须严格按音频帧大小（Frame Size = Channels * Bytes_per_sample）整除对齐**，返回非对齐的样点数会导致 ALSA 用户态崩溃。
