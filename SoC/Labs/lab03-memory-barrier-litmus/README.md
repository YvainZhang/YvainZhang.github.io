# Lab 03：弱内存序 Litmus Test

`store-buffering.c` 反复运行两个线程：`x=1; r0=y` 与 `y=1; r1=x`，统计二者都读到 0。结果依 CPU、编译器和运行时间，QEMU TCG 也可能不复现；“没有观察到”不等于架构禁止。

```bash
cc -O2 -pthread store-buffering.c -o store-buffering
./store-buffering
```

再编译顺序一致版本比较：

```bash
cc -O2 -pthread -DUSE_SEQ_CST store-buffering.c -o store-buffering-sc
./store-buffering-sc
```

更严谨的 ISA Litmus 应使用 herd7/LKMM 等模型工具；本程序主要展示实验方法和 C11 原子语义。
