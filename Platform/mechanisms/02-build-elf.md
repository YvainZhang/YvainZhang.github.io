# 从 undefined reference 到 SDK 交付

头文件已经声明了 `lab_sum()`，为什么一个 `.c` 能编译，最终链接却报 `undefined reference`？这个小例子适合拆开构建过程，也能用来检查 SDK 是否真有清晰的公共边界。

先按[实验环境](../guide/environment.md)进入工具容器。以下路径均相对于[源码包](../reference/source.md)根目录。

## 声明和实现各完成什么

`labs/abi_main.c` 调用函数，`labs/abi_helper.h` 给出声明，`labs/abi_helper.c` 提供实现。预处理展开头文件后，编译器能检查调用形式；生成的对象文件仍可以保留尚未解决的符号引用。链接器再把引用与定义匹配。GCC 的 `-E`、`-S`、`-c` 分别用于在不同阶段停止。[GCC 构建阶段说明](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html)

```text
abi_main.c + abi_helper.h → abi_main.o（引用 lab_sum）
abi_helper.c             → abi_helper.o（定义 lab_sum）
两份对象加入链接         → link-symbols
```

在容器内执行下面的拆分实验，不修改原 Makefile：

```sh
mkdir -p build/elf-demo
cc -std=c11 -Wall -Wextra -c labs/abi_main.c -o build/elf-demo/main.o
cc -std=c11 -Wall -Wextra -c labs/abi_helper.c -o build/elf-demo/helper.o
nm build/elf-demo/main.o build/elf-demo/helper.o
cc build/elf-demo/main.o build/elf-demo/helper.o -o build/elf-demo/complete
./build/elf-demo/complete
```

`nm` 中，调用方的 `lab_sum` 应显示为未定义引用 `U`，实现对象中有代码符号 `T`。若仅把 `main.o` 加入最后一步，链接应失败。这一失败发生在链接阶段，不意味着调用方的声明检查没有工作。

## 看 ELF 时先回答三个问题

ELF 是 Linux 常用的对象与可执行文件格式。先运行仓库的构建，再查看它已经保存的头部：

```sh
make -C labs test
cat build/labs/elf-header.txt
readelf -l build/labs/link-symbols
```

在首期 aarch64/musl 环境中，重点观察：

| 字段 / 输出 | 要回答的问题 |
|---|---|
| Class、Data、Machine | 位宽、字节序、目标架构是否与运行环境一致？ |
| Type | 是可重定位对象、可执行文件，还是动态对象？默认工具链可能构建 PIE，勿固定期待 `EXEC`。 |
| Program Headers、INTERP | 装载器怎样映射运行段？动态程序要求哪个加载器路径？ |

ELF section 帮助编译、链接和调试；program segment 服务于装载。知道某个符号存在，还不足以证明目标机器上能运行：加载器、动态依赖和 ABI 也需要匹配。

## 静态库的链接顺序是依赖方向

实验会生成 `build/labs/libabi.a` 和 `libabi.so`。静态 archive 是一组对象的集合；共享库还参与运行时装载。它们都不能抹平 CPU、调用约定与 libc 的差异。

平台示例把实现分成 `libplatformlinux.a` 和 `libplatformcore.a`。Linux runtime 使用 core，因此公共 consumer 的链接形式为：

```sh
make -C platform public-test
```

对应 Makefile 命令包含 `-lplatformlinux -lplatformcore -pthread`。对于传统按从左到右处理的静态库链接，把提供依赖符号的库放在需要它的库之后。遇到循环依赖再审查模块关系或采用链接器组策略，不能靠反复追加库掩盖边界。

`platform/examples/public-consumer.c` 只包含 `sdk.h`，执行资源查询、启动和停止。这个消费者比仅在源码树内编译全部对象更接近交付检验：它能发现私有头依赖、缺失符号和未暴露的必要配置。

## 交叉编译要一起改变哪些东西

`CC` 是入口，完整目标还包括 CPU/ABI、sysroot、libc、编译选项和运行时 port。aarch64/musl 产物需要为 glibc、macOS 或 MCU 目标重新构建；更换 `CC` 的名字不证明其余依赖已经匹配。

这也是 core 与 runtime 分开交付的原因：core 保留协议与状态转换，Linux runtime 提供 pthread/epoll/backend，FreeRTOS runtime 依赖所选内核与 port。[Linux 与 FreeRTOS 边界](../design/03-linux-freertos.md)讨论这条依赖如何延伸到执行与退出。

链接通过后，还要验证[fd 与对象寿命](03-fd-lifetime.md)、[buffer 所有权](07-concurrency-ownership.md)及失败回滚。构建检查解决“哪些实现被组合”，运行契约解决“这些实现怎样合作”。
