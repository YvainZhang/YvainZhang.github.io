"""Educational capacity/tail model; not a compiler backend or latency predictor."""

from itertools import product
import json


def positive_int(name, value):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def evaluate_tile(M, N, K, tile, elem_bytes=1, acc_bytes=4,
                  reserved_bytes=16 * 1024):
    """Full padded tiles, double-buffered A/B, one accumulator, reserved output."""
    for name, value in (("M", M), ("N", N), ("K", K),
                        ("elem_bytes", elem_bytes), ("acc_bytes", acc_bytes)):
        positive_int(name, value)
    if type(reserved_bytes) is not int or reserved_bytes < 0:
        raise ValueError("reserved_bytes must be a nonnegative integer")
    if len(tile) != 3:
        raise ValueError("tile must contain Tm, Tn, Tk")
    tm, tn, tk = tile
    for name, value in zip(("Tm", "Tn", "Tk"), tile):
        positive_int(name, value)
    calls = ((M + tm - 1) // tm) * ((N + tn - 1) // tn) * ((K + tk - 1) // tk)
    physical_macs = calls * tm * tn * tk
    return {
        "tile": list(tile),
        "sram_bytes": 2 * (tm * tk + tk * tn) * elem_bytes
                      + tm * tn * acc_bytes + reserved_bytes,
        "tile_calls": calls,
        "useful_macs": M * N * K,
        "physical_macs": physical_macs,
        "padding_efficiency": M * N * K / physical_macs,
    }


def calculate_npu_tiling(M, N, K, sram_capacity_bytes=1024 * 1024,
                         elem_bytes=1, acc_bytes=4, reserved_bytes=16 * 1024,
                         candidates=(16, 32, 64, 128)):
    """Rank feasible candidates by padded work, call count, then SRAM; no timing."""
    positive_int("sram_capacity_bytes", sram_capacity_bytes)
    # Validate even when no candidate is feasible.
    evaluate_tile(M, N, K, (1, 1, 1), elem_bytes, acc_bytes, reserved_bytes)
    candidates = tuple(candidates)
    if not candidates:
        raise ValueError("candidates must not be empty")
    for value in candidates:
        positive_int("candidate", value)
    feasible = []
    for tile in product(sorted(set(candidates)), repeat=3):
        result = evaluate_tile(M, N, K, tile, elem_bytes, acc_bytes, reserved_bytes)
        if result["sram_bytes"] <= sram_capacity_bytes:
            feasible.append(result)
    if not feasible:
        return None
    return min(feasible, key=lambda r: (r["physical_macs"], r["tile_calls"],
                                       r["sram_bytes"], r["tile"]))


if __name__ == "__main__":
    print("Teaching model only: no TVM backend, no measured latency")
    for shape in ((4096, 4096, 4096), (130, 70, 129)):
        print(json.dumps({"shape": shape, "selected": calculate_npu_tiling(*shape)},
                         indent=2))
    print("Case-study tile:")
    print(json.dumps(evaluate_tile(130, 70, 129, (64, 64, 128)), indent=2))
