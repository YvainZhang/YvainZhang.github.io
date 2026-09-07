#include <iostream>
#include <cuda_runtime.h>

// Memory-Bound Kernel: Vector Add
__global__ void vector_add(const float* A, const float* B, float* C, int n) {
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (idx < n) {
        C[idx] = A[idx] + B[idx];
    }
}

// Compute-Bound Kernel: Heavy Math Loop
__global__ void heavy_math(float* A, int n) {
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (idx < n) {
        float val = A[idx];
        #pragma unroll 100
        for (int i = 0; i < 500; ++i) {
            val = val * 1.0001f + 0.0002f;
        }
        A[idx] = val;
    }
}

int main() {
    int n = 1 << 22; // 4M elements
    float *dA, *dB, *dC;
    cudaMalloc(&dA, n * sizeof(float));
    cudaMalloc(&dB, n * sizeof(float));
    cudaMalloc(&dC, n * sizeof(float));

    int blockSize = 256;
    int numBlocks = (n + blockSize - 1) / blockSize;

    vector_add<<<numBlocks, blockSize>>>(dA, dB, dC, n);
    heavy_math<<<numBlocks, blockSize>>>(dA, n);

    cudaDeviceSynchronize();
    cudaFree(dA);
    cudaFree(dB);
    cudaFree(dC);
    std::cout << "Profile target finished.\n";
    return 0;
}
