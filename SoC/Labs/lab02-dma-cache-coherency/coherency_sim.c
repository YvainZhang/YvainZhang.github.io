#include <stdio.h>
#include <string.h>

struct buffer_view { char cpu_cache[64]; char memory[64]; int cpu_valid; };

static void clean_for_device(struct buffer_view *b) { memcpy(b->memory, b->cpu_cache, 64); }
static void invalidate_for_cpu(struct buffer_view *b) { memcpy(b->cpu_cache, b->memory, 64); b->cpu_valid = 1; }

int main(void)
{
    struct buffer_view b = { .cpu_cache = "old", .memory = "old", .cpu_valid = 1 };
    strcpy(b.cpu_cache, "cpu-new");
    printf("missing clean: device sees '%s'\n", b.memory);
    clean_for_device(&b);
    printf("after clean: device sees '%s'\n", b.memory);

    strcpy(b.memory, "device-new");
    printf("missing invalidate: CPU sees '%s'\n", b.cpu_cache);
    invalidate_for_cpu(&b);
    printf("after invalidate: CPU sees '%s'\n", b.cpu_cache);
    return 0;
}
