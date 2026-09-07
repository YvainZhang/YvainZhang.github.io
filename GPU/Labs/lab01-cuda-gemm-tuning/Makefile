NVCC = nvcc
NVCCFLAGS = -O3 -arch=native -std=c++17 --use_fast_math

TARGET = gemm_bench
SRCS = main.cu

all: $(TARGET)

$(TARGET): $(SRCS) gemm_kernels.cuh
	$(NVCC) $(NVCCFLAGS) $(SRCS) -o $(TARGET)

clean:
	rm -f $(TARGET)
