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
