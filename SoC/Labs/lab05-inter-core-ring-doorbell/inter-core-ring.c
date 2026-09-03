#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RING_SIZE 64U
#define MESSAGE_COUNT 100000U

struct ipc_ring {
    _Alignas(64) atomic_uint head;
    _Alignas(64) atomic_uint tail;
    _Alignas(64) uint32_t slots[RING_SIZE];
};

struct doorbell {
    pthread_mutex_t lock;
    pthread_cond_t condition;
    int pending;
};

static void fail_pthread(const char *operation, int error)
{
    fprintf(stderr, "%s: %s\n", operation, strerror(error));
    exit(EXIT_FAILURE);
}

struct context {
    struct ipc_ring ring;
    struct doorbell doorbell;
};

static void ring_doorbell(struct doorbell *doorbell)
{
    int error = pthread_mutex_lock(&doorbell->lock);
    if (error != 0)
        fail_pthread("pthread_mutex_lock", error);

    /* Repeated notifications merge while pending remains set. */
    doorbell->pending = 1;
    error = pthread_cond_signal(&doorbell->condition);
    if (error != 0)
        fail_pthread("pthread_cond_signal", error);

    error = pthread_mutex_unlock(&doorbell->lock);
    if (error != 0)
        fail_pthread("pthread_mutex_unlock", error);
}

static void wait_for_doorbell(struct doorbell *doorbell)
{
    int error = pthread_mutex_lock(&doorbell->lock);
    if (error != 0)
        fail_pthread("pthread_mutex_lock", error);

    while (!doorbell->pending) {
        error = pthread_cond_wait(&doorbell->condition, &doorbell->lock);
        if (error != 0)
            fail_pthread("pthread_cond_wait", error);
    }

    doorbell->pending = 0;
    error = pthread_mutex_unlock(&doorbell->lock);
    if (error != 0)
        fail_pthread("pthread_mutex_unlock", error);
}

static void *producer(void *argument)
{
    struct context *context = argument;

    for (uint32_t message = 1; message <= MESSAGE_COUNT; message++) {
        unsigned int head;
        unsigned int next;

        for (;;) {
            head = atomic_load_explicit(&context->ring.head,
                                        memory_order_relaxed);
            next = (head + 1U) % RING_SIZE;

            if (next != atomic_load_explicit(&context->ring.tail,
                                             memory_order_acquire))
                break;
        }

        context->ring.slots[head] = message;

        /* Publish the initialized slot before notifying the consumer. */
        atomic_store_explicit(&context->ring.head, next,
                              memory_order_release);
        ring_doorbell(&context->doorbell);
    }

    return NULL;
}

static void *consumer(void *argument)
{
    struct context *context = argument;
    uint32_t expected = 1;
    unsigned int received = 0;

    while (received < MESSAGE_COUNT) {
        wait_for_doorbell(&context->doorbell);

        /* One doorbell can represent multiple queued messages. */
        for (;;) {
            unsigned int tail = atomic_load_explicit(&context->ring.tail,
                                                     memory_order_relaxed);
            unsigned int head = atomic_load_explicit(&context->ring.head,
                                                     memory_order_acquire);

            if (tail == head)
                break;

            if (context->ring.slots[tail] != expected) {
                fprintf(stderr, "sequence error: expected=%u actual=%u\n",
                        expected, context->ring.slots[tail]);
                exit(EXIT_FAILURE);
            }

            expected++;
            received++;

            atomic_store_explicit(&context->ring.tail,
                                  (tail + 1U) % RING_SIZE,
                                  memory_order_release);
        }
    }

    printf("received=%u sequence-errors=0\n", received);
    return NULL;
}

int main(void)
{
    struct context context = { 0 };
    pthread_t producer_thread;
    pthread_t consumer_thread;
    int error;

    error = pthread_mutex_init(&context.doorbell.lock, NULL);
    if (error != 0)
        fail_pthread("pthread_mutex_init", error);

    error = pthread_cond_init(&context.doorbell.condition, NULL);
    if (error != 0)
        fail_pthread("pthread_cond_init", error);

    error = pthread_create(&consumer_thread, NULL, consumer, &context);
    if (error != 0)
        fail_pthread("pthread_create(consumer)", error);

    error = pthread_create(&producer_thread, NULL, producer, &context);
    if (error != 0)
        fail_pthread("pthread_create(producer)", error);

    error = pthread_join(producer_thread, NULL);
    if (error != 0)
        fail_pthread("pthread_join(producer)", error);

    error = pthread_join(consumer_thread, NULL);
    if (error != 0)
        fail_pthread("pthread_join(consumer)", error);

    error = pthread_cond_destroy(&context.doorbell.condition);
    if (error != 0)
        fail_pthread("pthread_cond_destroy", error);

    error = pthread_mutex_destroy(&context.doorbell.lock);
    if (error != 0)
        fail_pthread("pthread_mutex_destroy", error);

    return EXIT_SUCCESS;
}
