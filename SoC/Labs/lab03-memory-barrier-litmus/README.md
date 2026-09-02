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

## 测试结构

每次迭代开始前，主线程把 `x`、`y` 和完成计数器清零，然后通过 `go` 同时释放两个工作线程：

```text
Thread 0                         Thread 1
atomic_store(x, 1)               atomic_store(y, 1)
r0 = atomic_load(y)              r1 = atomic_load(x)
             \                    /
              \── 检查 r0=0 且 r1=0 ──/
```

`go` 和 `done` 用于组织实验轮次，不是被测试的数据变量。被测试的 Store/Load 使用 `TEST_ORDER`，以便在 Relaxed 与 Sequentially Consistent 两种模式间切换。

## 完整源码：`store-buffering.c`

```c
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>

#define N 1000000
#ifdef USE_SEQ_CST
#define TEST_ORDER memory_order_seq_cst
#else
#define TEST_ORDER memory_order_relaxed
#endif

static atomic_int x, y, go, done;
static int r0, r1;

static void wait_for_iteration(int iteration)
{
    while (atomic_load_explicit(&go, memory_order_acquire) < iteration) {
        /* Busy-wait only to keep the two test operations close together. */
    }
}

static void mark_iteration_done(void)
{
    atomic_fetch_add_explicit(&done, 1, memory_order_release);
}

static void *thread_zero(void *unused)
{
    (void)unused;

    for (int iteration = 1; iteration <= N; iteration++) {
        wait_for_iteration(iteration);

        atomic_store_explicit(&x, 1, TEST_ORDER);
        r0 = atomic_load_explicit(&y, TEST_ORDER);

        mark_iteration_done();
    }

    return NULL;
}

static void *thread_one(void *unused)
{
    (void)unused;

    for (int iteration = 1; iteration <= N; iteration++) {
        wait_for_iteration(iteration);

        atomic_store_explicit(&y, 1, TEST_ORDER);
        r1 = atomic_load_explicit(&x, TEST_ORDER);

        mark_iteration_done();
    }

    return NULL;
}

int main(void)
{
    pthread_t threads[2];
    unsigned long both_zero = 0;

    pthread_create(&threads[0], NULL, thread_zero, NULL);
    pthread_create(&threads[1], NULL, thread_one, NULL);

    for (int iteration = 1; iteration <= N; iteration++) {
        atomic_store_explicit(&x, 0, memory_order_relaxed);
        atomic_store_explicit(&y, 0, memory_order_relaxed);
        atomic_store_explicit(&done, 0, memory_order_relaxed);

        /* Release both workers for exactly this iteration. */
        atomic_store_explicit(&go, iteration, memory_order_release);

        while (atomic_load_explicit(&done, memory_order_acquire) != 2) {
            /* Wait until both result registers have been written. */
        }

        if (r0 == 0 && r1 == 0)
            both_zero++;
    }

    pthread_join(threads[0], NULL);
    pthread_join(threads[1], NULL);

    printf("both-zero=%lu/%d\n", both_zero, N);
    return 0;
}
```

输出格式如下，具体次数依处理器、编译器和运行环境而变化：

```text
both-zero=<观察次数>/1000000
```

即使 Relaxed 版本输出为零，也只能说明本次运行没有观察到目标结果，不能据此证明该结果被 C11 或目标 ISA 禁止。
