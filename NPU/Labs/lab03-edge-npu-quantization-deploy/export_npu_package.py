import json
from ptq_quantizer import symmetric_int8_quantize
import numpy as np

def export_model():
    weights = np.random.randn(32, 32).astype(np.float32)
    q_w, scale = symmetric_int8_quantize(weights)
    meta = {
        "model_name": "toy_npu_model",
        "weight_shape": list(q_w.shape),
        "scale": float(scale),
        "quant_type": "INT8_SYMMETRIC"
    }
    with open("npu_model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    q_w.tofile("model_weights.bin")
    print("Exported NPU offline model package: npu_model_meta.json, model_weights.bin")

if __name__ == "__main__":
    export_model()
