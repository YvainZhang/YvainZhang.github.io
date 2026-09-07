import numpy as np

def symmetric_int8_quantize(tensor):
    """对称 INT8 训练后量化 (PTQ)"""
    abs_max = np.max(np.abs(tensor))
    scale = abs_max / 127.0
    quantized = np.clip(np.round(tensor / (scale + 1e-8)), -128, 127).astype(np.int8)
    return quantized, scale

def dequantize(quantized, scale):
    return quantized.astype(np.float32) * scale

if __name__ == "__main__":
    np.random.seed(0)
    fake_weight = np.random.normal(0, 1.0, size=(64, 64)).astype(np.float32)
    q_w, scale = symmetric_int8_quantize(fake_weight)
    deq_w = dequantize(q_w, scale)
    mse = np.mean((fake_weight - deq_w) ** 2)
    print(f"PTQ INT8 Quantization Complete. Scale: {scale:.6f}, MSE Loss: {mse:.6e}")
