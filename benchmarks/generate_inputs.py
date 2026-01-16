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
            "--D",
            "{}".format(D),
            "--N",
            "{}".format(N),
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


def compute_biometric_result(
    S: List[int], C: List[int], D: int, N: int
) -> Tuple[int, int]:
    """
    Compute the biometric matching result (minimum squared Euclidean distance).

    This mirrors the MPC computation:
    - For each database entry i, compute sum of squared differences
    - Return the minimum distance and index
    """
    min_sum = 0
    min_index = 0

    for i in range(N):
        distance = 0
        for j in range(D):
            diff = S[i * D + j] - C[j]
            distance += diff * diff
        if i == 0 or distance < min_sum:
            min_sum = distance
            min_index = i

    return min_sum, min_index


def generate_biometric_test_file(D: int, N: int, output_path: str) -> None:
    """Generate a test input file for the biometric benchmark."""
    C = get_rand_ints(D)
    S = get_rand_ints(D * N)

    # Compute the correct result
    min_sum, min_index = compute_biometric_result(S, C, D, N)

    with open(output_path, "w") as f:
        f.write("db " + " ".join(map(str, S)) + "\n")
        f.write("sample " + " ".join(map(str, C)) + "\n")
        f.write(f"res {min_sum} {min_index}\n")

    print(
        f"Generated: {output_path} (D={D}, N={N}, min_sum={min_sum}, min_index={min_index})"
    )


# =============================================================================
# Convex Hull Benchmark
# =============================================================================


def get_convex_hull_inputs() -> Tuple[List[InputArgs], int]:
    """
    Generate inputs for convex hull benchmark.

    N = number of points
    X_coords = X coordinates of points
    Y_coords = Y coordinates of points
    """
    all_args = []
    non_vec_up_to = 0

    # for N in [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    # for N in [32, 256]:
    for N in [32, 64, 128, 256]:
        args = [
            "--N",
            "{}".format(N),
        ]
        X_coords = get_rand_ints(N)
        Y_coords = get_rand_ints(N)
        args.append("--X_coords")
        args.extend(list(map(str, X_coords)))
        args.append("--Y_coords")
        args.extend(list(map(str, Y_coords)))
        label = "N: {}".format(N)
        all_args.append(InputArgs(label, args))

    return (all_args, non_vec_up_to)


def compute_convex_hull_result(
    X_coords: List[int], Y_coords: List[int], N: int
) -> Tuple[List[int], List[int]]:
    """
    Compute the convex hull result arrays (result_X, result_Y).

    This mirrors the MPC computation:
    - For each point, check if it's on the hull
    - Populate result_X/result_Y with hull points
    """
    result_X = [0] * N
    result_Y = [0] * N

    for i in range(N):
        is_hull = True
        p1_X = X_coords[i]
        p1_Y = Y_coords[i]

        if p1_X <= 0 and p1_Y >= 0:
            for j in range(N):
                p2_X = X_coords[j]
                p2_Y = Y_coords[j]

                if not (p1_X <= p2_X or p1_Y >= p2_Y):
                    is_hull = False

        val_X = result_X[i]
        val_Y = result_Y[i]

        if is_hull:
            val_X = p1_X
            val_Y = p1_Y

        result_X[i] = val_X
        result_Y[i] = val_Y

    return result_X, result_Y


def generate_convex_hull_test_file(N: int, output_path: str) -> None:
    """Generate a test input file for the convex hull benchmark."""
    X_coords = get_rand_ints(N, min_val=-50, max_val=50)
    Y_coords = get_rand_ints(N, min_val=-50, max_val=50)

    # Compute the correct result
    result_X, result_Y = compute_convex_hull_result(X_coords, Y_coords, N)
    res_values = result_X + result_Y

    with open(output_path, "w") as f:
        f.write("X_coords " + " ".join(map(str, X_coords)) + "\n")
        f.write("Y_coords " + " ".join(map(str, Y_coords)) + "\n")
        f.write("res " + " ".join(map(str, res_values)) + "\n")

    print(f"Generated: {output_path} (N={N}, expected_values={len(res_values)})")


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate benchmark inputs for Silph MPC"
    )
    parser.add_argument(
        "--benchmark",
        "-b",
        type=str,
        required=True,
        choices=["biometric", "convex_hull", "all"],
        help="Which benchmark to generate inputs for",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=".",
        help="Output directory for generated files",
    )

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.benchmark == "biometric" or args.benchmark == "all":
        # Generate biometric test files
        configs = [[4, 512], [4, 1024]]
        for D, N in configs:
            output_path = os.path.join(args.output_dir, f"biometric_{N}_test.txt")
            generate_biometric_test_file(D, N, output_path)

    if args.benchmark == "convex_hull" or args.benchmark == "all":
        # Generate convex hull test files
        for N in [32, 64, 128, 256]:
            output_path = os.path.join(args.output_dir, f"convex_hull_{N}_test.txt")
            generate_convex_hull_test_file(N, output_path)

    print("\nTo get InputArgs programmatically:")
    print("  from generate_inputs import get_biometric_inputs, get_convex_hull_inputs")


if __name__ == "__main__":
    main()
