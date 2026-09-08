CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra -std=c99
PYTHON ?= python3

TARGET = lms_test
CSV_FILE = erle_data.csv

all: $(TARGET)

$(TARGET): fixed_point_lms.c
	$(CC) $(CFLAGS) -o $@ $< -lm

run: $(TARGET)
	./$(TARGET)
	$(PYTHON) plot_erle.py

plot:
	$(PYTHON) plot_erle.py

test: test_fixed_point.c fixed_point_lms.c
	$(CC) $(CFLAGS) -fsanitize=undefined -fno-sanitize-recover=undefined -o lms_unit_test test_fixed_point.c -lm
	./lms_unit_test

clean:
	rm -f $(TARGET) $(CSV_FILE) lms_unit_test

.PHONY: all run plot test clean
