#pragma once
#include <cuda_runtime.h>

// V1: Naive Global Memory Access (~10% Peak TFLOPS)
__global__ void gemm_v1_naive(const float* A, const float* B, float* C, int M, int N, int K) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < M && col < N) {
        float sum = 0.0f;
        for (int k = 0; k < K; ++k) {
            sum += A[row * K + k] * B[k * N + col];
        }
        C[row * N + col] = sum;
    }
}

// V2: Shared Memory Tiling (BLOCK_SIZE = 32, ~45% Peak TFLOPS)
template <int BLOCK_SIZE>
__global__ void gemm_v2_tiling(const float* A, const float* B, float* C, int M, int N, int K) {
    __shared__ float sA[BLOCK_SIZE][BLOCK_SIZE];
    __shared__ float sB[BLOCK_SIZE][BLOCK_SIZE];

    int row = blockIdx.y * BLOCK_SIZE + threadIdx.y;
    int col = blockIdx.x * BLOCK_SIZE + threadIdx.x;
    float sum = 0.0f;

    for (int bk = 0; bk < K; bk += BLOCK_SIZE) {
        if (row < M && (bk + threadIdx.x) < K)
            sA[threadIdx.y][threadIdx.x] = A[row * K + bk + threadIdx.x];
        else
            sA[threadIdx.y][threadIdx.x] = 0.0f;

        if ((bk + threadIdx.y) < K && col < N)
            sB[threadIdx.y][threadIdx.x] = B[(bk + threadIdx.y) * N + col];
        else
            sB[threadIdx.y][threadIdx.x] = 0.0f;

        __syncthreads();

        for (int k = 0; k < BLOCK_SIZE; ++k) {
            sum += sA[threadIdx.y][k] * sB[k][threadIdx.x];
        }
        __syncthreads();
    }

    if (row < M && col < N) {
        C[row * N + col] = sum;
    }
}

// V3: Bank Conflict Avoidance with Shared Memory Padding (~65% Peak TFLOPS)
template <int BLOCK_SIZE>
__global__ void gemm_v3_padding(const float* A, const float* B, float* C, int M, int N, int K) {
    // 增加 1 列 Padding 消除 32-Bank 冲突
    __shared__ float sA[BLOCK_SIZE][BLOCK_SIZE + 1];
    __shared__ float sB[BLOCK_SIZE][BLOCK_SIZE + 1];

    int row = blockIdx.y * BLOCK_SIZE + threadIdx.y;
    int col = blockIdx.x * BLOCK_SIZE + threadIdx.x;
    float sum = 0.0f;

    for (int bk = 0; bk < K; bk += BLOCK_SIZE) {
        sA[threadIdx.y][threadIdx.x] = (row < M && (bk + threadIdx.x) < K) ? A[row * K + bk + threadIdx.x] : 0.0f;
        sB[threadIdx.y][threadIdx.x] = ((bk + threadIdx.y) < K && col < N) ? B[(bk + threadIdx.y) * N + col] : 0.0f;
        __syncthreads();

        #pragma unroll
        for (int k = 0; k < BLOCK_SIZE; ++k) {
            sum += sA[threadIdx.y][k] * sB[k][threadIdx.x];
        }
        __syncthreads();
    }

    if (row < M && col < N) {
        C[row * N + col] = sum;
    }
}
