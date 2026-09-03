CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -pthread

all: inter-core-ring

inter-core-ring: inter-core-ring.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f inter-core-ring

.PHONY: all clean
