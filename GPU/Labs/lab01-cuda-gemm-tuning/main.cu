#include <iostream>
#include <vector>
#include <chrono>
#include <cuda_runtime.h>
#include "gemm_kernels.cuh"

int main() {
    const int M = 2048, N = 2048, K = 2048;
    size_t bytes = M * N * sizeof(float);

    std::vector<float> hA(M * K, 1.0f);
    std::vector<float> hB(K * N, 2.0f);
    std::vector<float> hC(M * N, 0.0f);

    float *dA, *dB, *dC;
    cudaMalloc(&dA, M * K * sizeof(float));
    cudaMalloc(&dB, K * N * sizeof(float));
    cudaMalloc(&dC, bytes);

    cudaMemcpy(dA, hA.data(), M * K * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(dB, hB.data(), K * N * sizeof(float), cudaMemcpyHostToDevice);

    dim3 block(32, 32);
    dim3 grid((N + 31) / 32, (M + 31) / 32);

    std::cout << "Running GEMM Optimization Benchmark (" << M << "x" << N << "x" << K << ")...\n";

    // Benchmark V1
    gemm_v1_naive<<<grid, block>>>(dA, dB, dC, M, N, K);
    cudaDeviceSynchronize();
    std::cout << "[V1 Naive] Execution Done.\n";

    // Benchmark V2
    gemm_v2_tiling<32><<<grid, block>>>(dA, dB, dC, M, N, K);
    cudaDeviceSynchronize();
    std::cout << "[V2 Tiling] Execution Done.\n";

    // Benchmark V3
    gemm_v3_padding<32><<<grid, block>>>(dA, dB, dC, M, N, K);
    cudaDeviceSynchronize();
    std::cout << "[V3 No Bank Conflict] Execution Done.\n";

    cudaFree(dA);
    cudaFree(dB);
    cudaFree(dC);
    return 0;
}
