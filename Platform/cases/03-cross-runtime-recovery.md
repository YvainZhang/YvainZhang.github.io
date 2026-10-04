# 恢复以后，旧回复怎样避免完成新请求

设备断连以后重新建立通道，新请求从 id=1 开始。旧通道的一条回复此时到达，如果只比较 id，就可能把新请求错误地标为完成。跨 Linux 和 FreeRTOS 的实现既要隔离旧会话，也要保留一致的业务终态。

本例采用同一纯 C core、Linux runtime，以及官方 FreeRTOS V11.1.0 POSIX port runtime。分层和运行命令见[双运行时教程](../design/03-linux-freertos.md)，源码和验证范围见[版本入口](../reference/source.md)。

## 用 generation 分隔两次会话

```text
旧请求 A：instance=7, generation=1, id=1
recover ：终结旧工作，generation=2，重建 backend
新请求 B：instance=7, generation=2, id=1
旧回复 A：仍属于 generation=1，不能完成 B
```

三元组里的 instance 区分多设备实例，generation 区分恢复边界，id 区分会话内请求。core 匹配完整身份；旧 generation 的回复计入旧会话观察，不能进入新请求终态路径。

## 恢复按照职责执行

| 阶段 | core 的责任 | runtime/backend 的责任 |
| --- | --- | --- |
| 发起 recover | 按当前状态处理恢复事件 | 关闭 admission，控制输入竞态 |
| 结束旧工作 | 旧 accepted 请求统一失败，清理数据 | 交付通知，关闭旧通道 |
| 建立新会话 | generation 增加，进入 STARTING | 重建设备执行对象与通信 |
| ready | 转入 READY | 发布状态，允许新工作 |
| 重建失败 | 进入 FAILED，保留明确状态 | 给出失败事件与诊断 |

本例 recover 由调用者显式发起，没有自动无限重试。timeout 与失败也不证明远端命令未执行；有副作用的业务还需要幂等标识和状态查询。

## 两端隔离旧工作的方法不同

Linux backend 是独立 exec 进程，经 seqpacket 通信。重建进程与 IPC 通道能隔离旧通信；core 仍检查完整身份，避免协议或未来实现依赖“旧回复绝不会到达”。

FreeRTOS backend 是 device task 与队列，旧排队回复可能仍被取出。core 的 generation 检查因此直接承担隔离职责。不能为了把两端包装成相同 API，省去其中一端仍需要的检查。

多实例回归还注入某个实例恢复失败，检查另一实例能继续工作。失败只影响对应对象和会话，不能通过共享全局 reset 误伤其他设备。

## 调度差异也要显式构造

FreeRTOS owner 优先级 3、device 优先级 2。高优先级 owner 可以在 device 的连续发送之间消费队列，所以“发送次数大于队列容量”无法保证测试触发队列满。

定向过载注入在短且有界的 80 次非阻塞发送期间控制调度，随后恢复。这让满队列和丢弃计数具有可重复的前提。注入中的调度控制限定在测试场景，生产方案继续依赖真实服务能力与背压。

## 复用的是可验证的结果

先按[环境准备](../guide/environment.md)取得并校验 FreeRTOS 依赖，再在无网络的专用工具容器项目根目录运行：

```sh
make -C platform core-test linux-test freertos-test
```

同一 core 向量在 FreeRTOS 实际任务中执行；runtime 回归覆盖旧代际、复制、队列满、恢复失败、多实例和停止。历史 2026-10-02/03 记录支持这些已执行功能路径。不同 runtime 的具体调度顺序可以不同，终态与守恒关系必须相同。

单 mutex 的优先级继承实验仅覆盖它自己的锁关系。POSIX port 依赖宿主 pthread，没有证明 MCU ISR、cache、DMA、最坏执行时间或硬件停止。换 MCU 后重新验证 port、中断、任务栈、内存与设备完成契约。

从一个旧回复问题，能够追到请求身份、恢复边界、实例隔离和平台机制差异。共同 core 让业务规则集中，独立 runtime 让各端退出责任可见。[交付责任](../design/04-reliability-delivery.md)
