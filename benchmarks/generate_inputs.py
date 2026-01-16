#!/usr/bin/env python3
"""
Benchmark Input Generator for Silph MPC Benchmarks

Generates random inputs for various MPC benchmarks and creates
test input files compatible with the ABY interpreter.
"""

import random
import argparse
from dataclasses import dataclass
from typing import List, Tuple
import os

# Hardcoded seed for reproducibility
random.seed(0)


@dataclass
class InputArgs:
    """Represents a benchmark configuration with its arguments."""
    label: str
    args: List[str]


def get_rand_ints(n: int, min_val: int = 0, max_val: int = 100) -> List[int]:
    """Generate n random integers in the given range."""
    return [random.randint(min_val, max_val) for _ in range(n)]


def get_rand_int(min_val: int = 0, max_val: int = 100) -> int:
    """Generate a single random integer in the given range."""
    return random.randint(min_val, max_val)


# =============================================================================
# Biometric Matching Benchmark
# =============================================================================

def get_biometric_inputs() -> Tuple[List[InputArgs], int]:
    """
    Generate inputs for biometric matching benchmark.

    D = number of features (fixed at 4)
    N = database size (number of entries)
    C = query vector (D features)
    S = database (N * D values)
    """
    all_args = []
    non_vec_up_to = 0  # Only run non-vectorized benchmark up to this index

    # for config in [[4, 4], [4, 8], [4, 16], [4, 32], [4, 64], [4, 128], [4, 256], [4, 512], [4, 1024], [4, 2048], [4, 4096]]:
    # for config in [[4, 128], [4, 4096]]:
    for config in [[4, 512], [4, 1024]]:
        D = config[0]
        N = config[1]
        args = [
            "--D", "{}".format(D),
            "--N", "{}".format(N),
        ]
        C = get_rand_ints(D)
        S = get_rand_ints(D * N)
        args.append("--C")
        args.extend(list(map(str, C)))
        args.append("--S")
        args.extend(list(map(str, S)))
        label = "D: {}, N: {}".format(D, N)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def compute_biometric_result(S: List[int], C: List[int], D: int, N: int) -> int:
    """
    Compute the biometric matching result (minimum squared Euclidean distance).

    This mirrors the MPC computation:
    - For each database entry i, compute sum of squared differences
    - Return the minimum distance
    """
    min_sum = float('inf')

    for i in range(N):
        distance = 0
        for j in range(D):
            diff = S[i * D + j] - C[j]
            distance += diff * diff
        if distance < min_sum:
            min_sum = distance

    return min_sum


def generate_biometric_test_file(D: int, N: int, output_path: str) -> None:
    """Generate a test input file for the biometric benchmark."""
    C = get_rand_ints(D)
    S = get_rand_ints(D * N)

    # Compute the correct result
    res = compute_biometric_result(S, C, D, N)

    with open(output_path, 'w') as f:
        f.write("db " + " ".join(map(str, S)) + "\n")
        f.write("sample " + " ".join(map(str, C)) + "\n")
        f.write(f"res {res}\n")

    print(f"Generated: {output_path} (D={D}, N={N}, expected_result={res})")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate benchmark inputs for Silph MPC")
    parser.add_argument("--benchmark", "-b", type=str, required=True,
                        choices=["biometric", "all"],
                        help="Which benchmark to generate inputs for")
    parser.add_argument("--output-dir", "-o", type=str, default=".",
                        help="Output directory for generated files")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.benchmark == "biometric" or args.benchmark == "all":
        # Generate biometric test files
        configs = [[4, 512], [4, 1024]]
        for D, N in configs:
            output_path = os.path.join(args.output_dir, f"biometric_{N}_test.txt")
            generate_biometric_test_file(D, N, output_path)

    print("\nTo get InputArgs programmatically:")
    print("  from generate_inputs import get_biometric_inputs")
    print("  inputs, non_vec_idx = get_biometric_inputs()")


if __name__ == "__main__":
    main()
