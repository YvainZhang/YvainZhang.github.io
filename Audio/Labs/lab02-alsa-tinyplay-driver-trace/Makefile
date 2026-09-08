PYTHON ?= python3
WAV_FILE = test_tone_48k.wav

all: generate run

generate:
	$(PYTHON) generate_tone.py $(WAV_FILE)

run:
	./run_xrun_test.sh

monitor:
	$(PYTHON) xrun_monitor.py

clean:
	rm -f $(WAV_FILE)

.PHONY: all generate run monitor clean
