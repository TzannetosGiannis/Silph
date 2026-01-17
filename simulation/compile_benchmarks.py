#!/usr/bin/env python3
import argparse
import csv
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

ILP_TIME_RE = re.compile(r"LOG: ILP time: ([0-9.]+)s")


def iter_benchmarks(benchmarks_dir: Path):
    for c_path in sorted(benchmarks_dir.glob("*/*/*.c")):
        benchmark = c_path.parent.parent.name
        size = c_path.parent.name
        if c_path.name != f"{benchmark}.c":
            continue
        yield benchmark, size, c_path


def parse_ilp_time(output: str):
    matches = ILP_TIME_RE.findall(output)
    if not matches:
        return None
    return matches[-1]


def format_error(output: str, returncode: int):
    lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
    tail = lines[-5:] if lines else ["no output captured"]
    message = " | ".join(tail)
    return f"exit {returncode}: {message}"


def run_compile(repo_root: Path, c_path: Path):
    command = [
        str(repo_root / "target" / "release" / "examples" / "circ"),
        "--parties",
        "2",
        str(c_path),
        "mpc",
        "--cost-model",
        "empirical",
        "--selection-scheme",
        "smart_lp",
        "--part-size",
        "8000",
        "--mut-level",
        "2",
        "--mut-step-size",
        "1",
        "--graph-type",
        "0",
    ]
    env = os.environ.copy()
    env["CARGO_MANIFEST_DIR"] = str(repo_root)
    env.setdefault("CARGO_FEATURE_C_NO_TESTS", "1")
    env.setdefault("ABY_SOURCE", str(repo_root.parent / "ABY"))
    env.setdefault("KAHIP_SOURCE", str(repo_root.parent / "KaHIP"))
    env.setdefault("KAHYPAR_SOURCE", str(repo_root.parent / "kahypar"))
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compile all benchmarks and capture ILP times. "
            "Default output: simulation/results/ILP_time.csv."
        )
    )
    parser.add_argument(
        "--output",
        default="simulation/results/ILP_time.csv",
        help="Path to output CSV file.",
    )
    parser.add_argument(
        "--log-file",
        default="simulation/results/ILP_time.log",
        help="Path to detailed log file.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    benchmarks_dir = repo_root / "benchmarks"
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    with log_path.open("w") as log_file:
        for benchmark, size, c_path in iter_benchmarks(benchmarks_dir):
            timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            header = f"[{timestamp}] {benchmark}/{size}"
            command_display = (
                f"{repo_root / 'target' / 'release' / 'examples' / 'circ'} "
                f"--parties 2 {c_path} mpc --cost-model empirical "
                f"--selection-scheme smart_lp --part-size 8000 --mut-level 2 "
                f"--mut-step-size 1 --graph-type 0"
            )
            log_file.write(f"{header} START\n")
            log_file.write(f"COMMAND: {command_display}\n")
            log_file.flush()

            returncode, output = run_compile(repo_root, c_path)
            ilp_time = parse_ilp_time(output)

            log_file.write(output)
            log_file.write(f"{header} EXIT={returncode}\n")
            log_file.flush()

            if returncode != 0:
                rows.append(
                    {
                        "benchmark": benchmark,
                        "size": size,
                        "timestamp": timestamp,
                        "ilp_time_seconds": "",
                        "status": "error",
                        "error": format_error(output, returncode),
                    }
                )
                continue

            if ilp_time is None:
                rows.append(
                    {
                        "benchmark": benchmark,
                        "size": size,
                        "timestamp": timestamp,
                        "ilp_time_seconds": "",
                        "status": "missing_ilp_time",
                        "error": "ILP time not found in compiler output",
                    }
                )
                continue

            rows.append(
                {
                    "benchmark": benchmark,
                    "size": size,
                    "timestamp": timestamp,
                    "ilp_time_seconds": ilp_time,
                    "status": "ok",
                    "error": "",
                }
            )

    with output_path.open("w", newline="") as csvfile:
        fieldnames = [
            "benchmark",
            "size",
            "timestamp",
            "ilp_time_seconds",
            "status",
            "error",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")
    print(f"Detailed log written to {log_path}")


if __name__ == "__main__":
    main()
