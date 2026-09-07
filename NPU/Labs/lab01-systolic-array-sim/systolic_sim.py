import numpy as np

class PE:
    def __init__(self, r, c):
        self.r = r
        self.c = c
        self.weight = 0.0
        self.in_act = 0.0
        self.out_act = 0.0
        self.in_acc = 0.0
        self.out_acc = 0.0

    def load_weight(self, w):
        self.weight = w

    def step(self):
        # Weight Stationary: Acc_out = Acc_in + Act_in * Weight
        self.out_acc = self.in_acc + self.in_act * self.weight
        self.out_act = self.in_act

class SystolicArray2D:
    def __init__(self, rows=4, cols=4):
        self.rows = rows
        self.cols = cols
        self.pes = [[PE(r, c) for c in range(cols)] for r in range(rows)]

    def load_weights(self, W):
        assert W.shape == (self.rows, self.cols)
        for r in range(self.rows):
            for c in range(self.cols):
                self.pes[r][c].load_weight(W[r, c])

    def run_matmul(self, A):
        # A: (M, K), assuming K == rows
        M, K = A.shape
        total_cycles = M + self.rows + self.cols - 1
        results = np.zeros((M, self.cols), dtype=np.float32)

        # Skew input activations
        act_skewed = [[0.0] * total_cycles for _ in range(self.rows)]
        for r in range(self.rows):
            for m in range(M):
                act_skewed[r][m + r] = A[m, r]

        # Cycle-by-cycle simulation
        for cycle in range(total_cycles):
            # 1. Update inputs
            for r in range(self.rows):
                self.pes[r][0].in_act = act_skewed[r][cycle]

            # 2. Forward activations across rows (West -> East)
            for r in range(self.rows):
                for c in range(1, self.cols):
                    self.pes[r][c].in_act = self.pes[r][c-1].out_act

            # 3. Forward partial sums down columns (North -> South)
            for c in range(self.cols):
                self.pes[0][c].in_acc = 0.0
                for r in range(1, self.rows):
                    self.pes[r][c].in_acc = self.pes[r-1][c].out_acc

            # 4. Compute all PEs
            for r in range(self.rows):
                for c in range(self.cols):
                    self.pes[r][c].step()

            # 5. Collect outputs at the bottom (South)
            for c in range(self.cols):
                # Output m finishes at column c after m + (rows-1) + c cycles
                out_m = cycle - (self.rows - 1 + c)
                if 0 <= out_m < M:
                    results[out_m, c] = self.pes[self.rows-1][c].out_acc

        return results
