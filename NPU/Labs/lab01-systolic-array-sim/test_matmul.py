import numpy as np
from systolic_sim import SystolicArray2D

def test_systolic():
    rows, cols = 4, 4
    np.random.seed(42)
    W = np.random.randn(rows, cols).astype(np.float32)
    A = np.random.randn(8, rows).astype(np.float32)

    sim = SystolicArray2D(rows, cols)
    sim.load_weights(W)
    sim_result = sim.run_matmul(A)

    expected = np.dot(A, W)
    np.testing.assert_allclose(sim_result, expected, atol=1e-4)
    print("✅ 2D Systolic Array Simulator Verified Against NumPy GEMM Successfully!")

if __name__ == "__main__":
    test_systolic()
