NVCC = nvcc
NVCCFLAGS = -O3 -arch=native

all: profile_target

profile_target: profile_target.cu
	$(NVCC) $(NVCCFLAGS) profile_target.cu -o profile_target

clean:
	rm -f profile_target
