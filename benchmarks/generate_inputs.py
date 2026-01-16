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
# Count 102 Benchmark
# =============================================================================


def get_count_102_inputs() -> Tuple[List[InputArgs], int]:
    """
    Generate inputs for count_102 benchmark.

    N = length of Seq
    Seq = input sequence
    Syms = [a, b, c]
    """
    all_args = []
    non_vec_up_to = 0

    # for N in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    for N in [1024, 4096]:
        args = [
            "--N",
            "{}".format(N),
        ]
        Seq = get_rand_ints(N, min_val=0, max_val=2)
        Syms = [1, 0, 2]
        args.append("--Seq")
        args.extend(list(map(str, Seq)))
        args.append("--Syms")
        args.extend(list(map(str, Syms)))
        label = "N: {}".format(N)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def get_count_10s_inputs() -> Tuple[List[InputArgs], int]:
    """
    Generate inputs for count_10s benchmark.

    N = length of Seq
    Seq = input sequence
    Syms = [a, b]
    """
    all_args = []
    non_vec_up_to = 0

    # for N in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    for N in [1024, 4096]:
        args = [
            "--N",
            "{}".format(N),
        ]
        Seq = get_rand_ints(N, min_val=0, max_val=2)
        Syms = [0, 1]
        args.append("--Seq")
        args.extend(list(map(str, Seq)))
        args.append("--Syms")
        args.extend(list(map(str, Syms)))
        label = "N: {}".format(N)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def get_cryptonets_max_pooling_inputs() -> Tuple[List[InputArgs], int]:
    """
    Generate inputs for cryptonets_max_pooling benchmark.

    rows/cols define the input matrix dimensions.
    """
    all_args = []
    non_vec_up_to = 0

    # for config in [[4, 4], [8, 8], [16, 16], [32, 32], [64, 64]]:
    for config in [[16, 16]]:
        rows = config[0]
        cols = config[1]
        rows_res = rows // 2
        cols_res = cols // 2

        args = [
            "--cols",
            str(cols),
            "--rows",
            str(rows),
            "--cols_res",
            str(cols_res),
            "--rows_res",
            str(rows_res),
        ]
        vals = [i + 2 for i in range(rows * cols)]
        args.append("--vals")
        args.extend(list(map(str, vals)))
        label = "rows: {}, cols: {}".format(rows, cols)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def get_db_cross_join_trivial_inputs() -> Tuple[List[InputArgs], int]:
    """
    Generate inputs for db_join cross join benchmark.

    Len_A/Len_B are the number of tuples (2 attributes each).
    """
    all_args = []
    non_vec_up_to = 0

    # for N in [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]:
    for N in [32, 64]:
        Len_A = N
        Len_B = N
        args = [
            "--Len_A",
            str(Len_A),
            "--Len_B",
            str(Len_B),
        ]
        A = get_rand_ints(Len_A * 2)
        B = get_rand_ints(Len_B * 2)
        args.append("--A")
        args.extend(list(map(str, A)))
        args.append("--B")
        args.extend(list(map(str, B)))
        label = "{}, {}".format(Len_A, Len_B)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def get_db_variance_inputs() -> Tuple[List[InputArgs], int]:
    """
    Generate inputs for db_variance benchmark.

    A and V are length-N arrays.
    """
    all_args = []
    non_vec_up_to = 0

    # for N in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    for N in [512, 1024, 2048, 4096]:
        args = [
            "--len",
            "{}".format(N),
        ]
        A = get_rand_ints(N)
        V = [0 for _ in range(N)]
        args.append("--A")
        args.extend(list(map(str, A)))
        args.append("--V")
        args.extend(list(map(str, V)))
        label = "len: {}".format(N)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def get_inner_product_inputs() -> Tuple[List[InputArgs], int]:
    """Generate inputs for inner_product benchmark."""
    all_args = []
    non_vec_up_to = 0

    # for N in [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    for N in [512, 4096]:
        args = [
            "--N",
            "{}".format(N),
        ]
        A = get_rand_ints(N)
        B = get_rand_ints(N)
        args.append("--A")
        args.extend(list(map(str, A)))
        args.append("--B")
        args.extend(list(map(str, B)))
        label = "N: {}".format(N)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def get_longest_102_inputs() -> Tuple[List[InputArgs], int]:
    """Generate inputs for longest_102 benchmark."""
    all_args = []
    non_vec_up_to = 0

    # for N in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    for N in [1024, 4096]:
        args = [
            "--N",
            "{}".format(N),
        ]
        Seq = get_rand_ints(N, min_val=0, max_val=2)
        Syms = [1, 0, 2]
        args.append("--Seq")
        args.extend(list(map(str, Seq)))
        args.append("--Syms")
        args.extend(list(map(str, Syms)))
        label = "N: {}".format(N)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def get_max_dist_between_syms_inputs() -> Tuple[List[InputArgs], int]:
    """Generate inputs for max_dist_between_syms benchmark."""
    all_args = []
    non_vec_up_to = 0

    # for N in [8, 16, 32, 64, 128, 256, 512, 1024, 4096]:
    for N in [1024, 2048]:
        args = [
            "--N",
            "{}".format(N),
        ]
        Seq = get_rand_ints(N)
        some_i = random.randint(0, len(Seq) - 1)
        Sym = Seq[some_i]
        args.append("--Seq")
        args.extend(list(map(str, Seq)))
        args.append("--Sym")
        args.append(str(Sym))
        label = "N: {}".format(N)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def get_minimal_points_inputs() -> Tuple[List[InputArgs], int]:
    """Generate inputs for minimal_points benchmark."""
    all_args = []
    non_vec_up_to = 0

    # for N in [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    for N in [32, 64, 128, 256]:
        args = [
            "--N",
            "{}".format(N),
        ]
        X_coords = get_rand_ints(N)
        Y_coords = get_rand_ints(N)
        result_X = [0] * N
        result_Y = [0] * N
        args.append("--X_coords")
        args.extend(list(map(str, X_coords)))
        args.append("--Y_coords")
        args.extend(list(map(str, Y_coords)))
        args.append("--result_X")
        args.extend(list(map(str, result_X)))
        args.append("--result_Y")
        args.extend(list(map(str, result_Y)))
        label = "N: {}".format(N)
        all_args.append(InputArgs(label, args))

    return all_args, non_vec_up_to


def compute_count_102_result(Seq: List[int], Syms: List[int], N: int) -> int:
    """
    Compute the count_102 result.

    Counts occurrences of regex a(b*)c in Seq.
    """
    s0 = False
    c = 0

    for i in range(N):
        if s0 and (Seq[i] == Syms[2]):
            c = c + 1

        s0 = (Seq[i] == Syms[1]) or (s0 and (Seq[i] == Syms[0]))

    return c


def generate_count_102_test_file(N: int, output_path: str) -> None:
    """Generate a test input file for the count_102 benchmark."""
    Seq = get_rand_ints(N, min_val=0, max_val=2)
    Syms = [1, 0, 2]

    # Compute the correct result
    res = compute_count_102_result(Seq, Syms, N)

    with open(output_path, "w") as f:
        f.write("Seq " + " ".join(map(str, Seq)) + "\n")
        f.write("Syms " + " ".join(map(str, Syms)) + "\n")
        f.write(f"res {res}\n")

    print(f"Generated: {output_path} (N={N}, expected_result={res})")


def compute_count_10s_result(Seq: List[int], Syms: List[int], N: int) -> int:
    """
    Compute the count_10s result.

    Counts occurrences of regex a(b+) in Seq.
    """
    s0 = False
    s1 = False
    scount = 0

    for i in range(N):
        if s1 and (Seq[i] != Syms[0]):
            scount = scount + 1

        s1 = (Seq[i] == Syms[0]) and (s0 or s1)
        s0 = Seq[i] == Syms[1]

    return scount


def generate_count_10s_test_file(N: int, output_path: str) -> None:
    """Generate a test input file for the count_10s benchmark."""
    Seq = get_rand_ints(N, min_val=0, max_val=2)
    Syms = [0, 1]

    # Compute the correct result
    res = compute_count_10s_result(Seq, Syms, N)

    with open(output_path, "w") as f:
        f.write("Seq " + " ".join(map(str, Seq)) + "\n")
        f.write("Syms " + " ".join(map(str, Syms)) + "\n")
        f.write(f"res {res}\n")

    print(f"Generated: {output_path} (N={N}, expected_result={res})")


def compute_cryptonets_max_pooling_result(
    vals: List[int], cols: int, rows: int
) -> List[int]:
    """Compute max pooling output for cryptonets_max_pooling."""
    cols_res = cols // 2
    rows_res = rows // 2
    output = [0] * (cols_res * rows_res)

    for i in range(rows_res):
        for j in range(cols_res):
            idx = i * 2 * cols + j * 2
            max_val = vals[idx]
            candidate = vals[idx + 1]
            if candidate > max_val:
                max_val = candidate
            candidate = vals[(i * 2 + 1) * cols + j * 2]
            if candidate > max_val:
                max_val = candidate
            candidate = vals[(i * 2 + 1) * cols + j * 2 + 1]
            if candidate > max_val:
                max_val = candidate
            output[i * cols_res + j] = max_val

    return output


def generate_cryptonets_max_pooling_test_file(
    rows: int, cols: int, output_path: str
) -> None:
    """Generate a test input file for the cryptonets_max_pooling benchmark."""
    vals = [i + 2 for i in range(rows * cols)]

    # Compute the correct result
    output = compute_cryptonets_max_pooling_result(vals, cols, rows)

    with open(output_path, "w") as f:
        f.write("vals " + " ".join(map(str, vals)) + "\n")
        f.write("res " + " ".join(map(str, output)) + "\n")

    print(
        f"Generated: {output_path} (rows={rows}, cols={cols}, expected_values={len(output)})"
    )


def compute_db_cross_join_trivial_result(
    A: List[int], B: List[int], Len_A: int, Len_B: int
) -> List[int]:
    """Compute the db cross join result arrays."""
    Att_A = 2
    Att_B = 2
    Att = Att_A + Att_B - 1
    ret = [0] * (Len_A * Len_B * Att)
    ret_idx = 0

    for i in range(Len_A):
        for j in range(Len_B):
            if A[i * Att_A] == B[j * Att_B]:
                ret[ret_idx * Att] = A[i * Att_A]
                ret[ret_idx * Att + 1] = A[i * Att_A + 1]
                ret[ret_idx * Att + 2] = B[j * Att_B + 1]
                ret_idx = ret_idx + 1

    return ret


def generate_db_cross_join_trivial_test_file(
    Len_A: int, Len_B: int, output_path: str
) -> None:
    """Generate a test input file for the db cross join benchmark."""
    A = get_rand_ints(Len_A * 2)
    B = get_rand_ints(Len_B * 2)

    # Compute the correct result
    res = compute_db_cross_join_trivial_result(A, B, Len_A, Len_B)

    with open(output_path, "w") as f:
        f.write("A " + " ".join(map(str, A)) + "\n")
        f.write("B " + " ".join(map(str, B)) + "\n")
        f.write("res " + " ".join(map(str, res)) + "\n")

    print(
        f"Generated: {output_path} (Len_A={Len_A}, Len_B={Len_B}, expected_values={len(res)})"
    )


def compute_db_variance_result(A: List[int], N: int) -> int:
    """Compute variance for db_variance benchmark."""
    total = 0
    for value in A:
        total += value
    exp = total // N

    res = 0
    for value in A:
        dist = value - exp
        res += dist * dist

    return res // N


def generate_db_variance_test_file(N: int, output_path: str) -> None:
    """Generate a test input file for the db_variance benchmark."""
    A = get_rand_ints(N)
    V = [0 for _ in range(N)]

    # Compute the correct result
    res = compute_db_variance_result(A, N)

    with open(output_path, "w") as f:
        f.write("A " + " ".join(map(str, A)) + "\n")
        f.write("V " + " ".join(map(str, V)) + "\n")
        f.write(f"res {res}\n")

    print(f"Generated: {output_path} (len={N}, expected_result={res})")


def compute_inner_product_result(A: List[int], B: List[int], N: int) -> int:
    """Compute the inner product for the benchmark."""
    total = 0
    for i in range(N):
        total += A[i] * B[i]
    return total


def generate_inner_product_test_file(N: int, output_path: str) -> None:
    """Generate a test input file for the inner_product benchmark."""
    A = get_rand_ints(N)
    B = get_rand_ints(N)

    # Compute the correct result
    res = compute_inner_product_result(A, B, N)

    with open(output_path, "w") as f:
        f.write("A " + " ".join(map(str, A)) + "\n")
        f.write("B " + " ".join(map(str, B)) + "\n")
        f.write(f"res {res}\n")

    print(f"Generated: {output_path} (N={N}, expected_result={res})")


def compute_longest_102_result(Seq: List[int], Syms: List[int], N: int) -> int:
    """Compute the longest_102 result."""
    s0 = False
    max_len = 0
    length = 0

    for i in range(N):
        s1 = s0 and (Seq[i] == Syms[2])
        s0 = (Seq[i] == Syms[1]) or (s0 and (Seq[i] == Syms[0]))

        if s1 or s0:
            length = length + 1
        else:
            length = 0

        if s1 and max_len < length:
            max_len = length

    return max_len


def generate_longest_102_test_file(N: int, output_path: str) -> None:
    """Generate a test input file for the longest_102 benchmark."""
    Seq = get_rand_ints(N, min_val=0, max_val=2)
    Syms = [1, 0, 2]

    # Compute the correct result
    res = compute_longest_102_result(Seq, Syms, N)

    with open(output_path, "w") as f:
        f.write("Seq " + " ".join(map(str, Seq)) + "\n")
        f.write("Syms " + " ".join(map(str, Syms)) + "\n")
        f.write(f"res {res}\n")

    print(f"Generated: {output_path} (N={N}, expected_result={res})")


def compute_max_dist_between_syms_result(Seq: List[int], Sym: int, N: int) -> int:
    """Compute the max distance between symbol occurrences."""
    max_dist = 0
    current_dist = 0
    for i in range(N):
        if Seq[i] != Sym:
            current_dist += 1
        else:
            current_dist = 0
        if current_dist > max_dist:
            max_dist = current_dist
    return max_dist


def generate_max_dist_between_syms_test_file(N: int, output_path: str) -> None:
    """Generate a test input file for max_dist_between_syms benchmark."""
    Seq = get_rand_ints(N)
    some_i = random.randint(0, len(Seq) - 1)
    Sym = Seq[some_i]

    # Compute the correct result
    res = compute_max_dist_between_syms_result(Seq, Sym, N)

    with open(output_path, "w") as f:
        f.write("Seq " + " ".join(map(str, Seq)) + "\n")
        f.write(f"Sym {Sym}\n")
        f.write(f"res {res}\n")

    print(f"Generated: {output_path} (N={N}, expected_result={res})")


def compute_minimal_points_result(
    X_coords: List[int], Y_coords: List[int], N: int
) -> Tuple[List[int], List[int]]:
    """Compute minimal points output arrays."""
    result_X = [0] * N
    result_Y = [0] * N

    for i in range(N):
        bx = False
        for j in range(N):
            if X_coords[j] < X_coords[i] and Y_coords[j] < Y_coords[i]:
                bx = True
        val_X = result_X[i]
        val_Y = result_Y[i]
        if not bx:
            val_X = X_coords[i]
            val_Y = Y_coords[i]
        result_X[i] = val_X
        result_Y[i] = val_Y

    return result_X, result_Y


def generate_minimal_points_test_file(N: int, output_path: str) -> None:
    """Generate a test input file for minimal_points benchmark."""
    X_coords = get_rand_ints(N)
    Y_coords = get_rand_ints(N)
    result_X = [0] * N
    result_Y = [0] * N

    # Compute the correct result
    expected_X, expected_Y = compute_minimal_points_result(X_coords, Y_coords, N)
    res_values = expected_X + expected_Y

    with open(output_path, "w") as f:
        f.write("X_coords " + " ".join(map(str, X_coords)) + "\n")
        f.write("Y_coords " + " ".join(map(str, Y_coords)) + "\n")
        f.write("result_X " + " ".join(map(str, result_X)) + "\n")
        f.write("result_Y " + " ".join(map(str, result_Y)) + "\n")
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
        choices=[
            "biometric",
            "convex_hull",
            "count_102",
            "count_10s",
            "cryptonets_max_pooling",
            "db_join",
            "db_variance",
            "inner_product",
            "longest_102",
            "max_dist_between_syms",
            "minimal_points",
            "all",
        ],
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

    if args.benchmark == "count_102" or args.benchmark == "all":
        # Generate count_102 test files
        for N in [1024, 4096]:
            output_path = os.path.join(args.output_dir, f"count_102_{N}_test.txt")
            generate_count_102_test_file(N, output_path)

    if args.benchmark == "count_10s" or args.benchmark == "all":
        # Generate count_10s test files
        for N in [1024, 4096]:
            output_path = os.path.join(args.output_dir, f"count_10s_{N}_test.txt")
            generate_count_10s_test_file(N, output_path)

    if args.benchmark == "cryptonets_max_pooling" or args.benchmark == "all":
        # Generate cryptonets max pooling test files
        for rows, cols in [(16, 16)]:
            output_path = os.path.join(
                args.output_dir, f"cryptonets_max_pooling_{rows}x{cols}_test.txt"
            )
            generate_cryptonets_max_pooling_test_file(rows, cols, output_path)

    if args.benchmark == "db_join" or args.benchmark == "all":
        # Generate db cross join test files
        for n in [32, 64]:
            output_path = os.path.join(args.output_dir, f"db_join_{n}_test.txt")
            generate_db_cross_join_trivial_test_file(n, n, output_path)

    if args.benchmark == "db_variance" or args.benchmark == "all":
        # Generate db variance test files
        for n in [512, 1024, 2048, 4096]:
            output_path = os.path.join(args.output_dir, f"db_variance_{n}_test.txt")
            generate_db_variance_test_file(n, output_path)

    if args.benchmark == "inner_product" or args.benchmark == "all":
        # Generate inner product test files
        for n in [512, 4096]:
            output_path = os.path.join(args.output_dir, f"inner_product_{n}_test.txt")
            generate_inner_product_test_file(n, output_path)

    if args.benchmark == "longest_102" or args.benchmark == "all":
        # Generate longest_102 test files
        for n in [1024, 4096]:
            output_path = os.path.join(args.output_dir, f"longest_102_{n}_test.txt")
            generate_longest_102_test_file(n, output_path)

    if args.benchmark == "max_dist_between_syms" or args.benchmark == "all":
        # Generate max_dist_between_syms test files
        for n in [1024, 2048]:
            output_path = os.path.join(
                args.output_dir, f"max_dist_between_syms_{n}_test.txt"
            )
            generate_max_dist_between_syms_test_file(n, output_path)

    if args.benchmark == "minimal_points" or args.benchmark == "all":
        # Generate minimal_points test files
        for n in [32, 64, 128, 256]:
            output_path = os.path.join(args.output_dir, f"minimal_points_{n}_test.txt")
            generate_minimal_points_test_file(n, output_path)

    print("\nTo get InputArgs programmatically:")
    print(
        "  from generate_inputs import get_biometric_inputs, get_convex_hull_inputs, get_count_102_inputs, get_count_10s_inputs, get_cryptonets_max_pooling_inputs, get_db_cross_join_trivial_inputs, get_db_variance_inputs, get_inner_product_inputs, get_longest_102_inputs, get_max_dist_between_syms_inputs, get_minimal_points_inputs"
    )


if __name__ == "__main__":
    main()
