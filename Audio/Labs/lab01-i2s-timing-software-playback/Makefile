CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra -std=c99

TARGET = i2s_sim
VCD_FILE = i2s_trace.vcd

all: $(TARGET)

$(TARGET): i2s_simulator.c
	$(CC) $(CFLAGS) -o $@ $<

run: $(TARGET)
	./$(TARGET)

view: run
	@which gtkwave > /dev/null && gtkwave $(VCD_FILE) || echo "gtkwave not installed, but $(VCD_FILE) is generated."

clean:
	rm -f $(TARGET) $(VCD_FILE)

.PHONY: all run view clean
