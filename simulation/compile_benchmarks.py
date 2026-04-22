#!/usr/bin/env python3
import argparse
import csv
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

ILP_TIME_RE = re.compile(r"LOG: Assignment time: ([0-9.]+)(ms|s)")
DEFAULT_TIMEOUT_SECONDS = 120
RUNS_PER_BENCHMARK = 10


def iter_benchmarks(benchmarks_dir: Path):
    for c_path in sorted(benchmarks_dir.glob("*/*/*.c")):
        benchmark = c_path.parent.parent.name
        size = c_path.parent.name
        if c_path.name != f"{benchmark}.c":
            continue
        yield benchmark, size, c_path


def iter_selection_schemes():
    return ["smart_lp"]


def parse_ilp_time(output: str):
    matches = ILP_TIME_RE.findall(output)
    if not matches:
        return None
    value, unit = matches[-1]
    seconds = float(value) / 1000 if unit == "ms" else float(value)
    return f"{seconds:.6f}"


def format_error(output: str, returncode: int):
    lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
    tail = lines[-5:] if lines else ["no output captured"]
    message = " | ".join(tail)
    return f"exit {returncode}: {message}"


def run_compile(
    repo_root: Path,
    c_path: Path,
    selection_scheme: str,
    timeout_seconds: int,
):
    command = [
        str(repo_root / "target" / "release" / "examples" / "circ"),
        "--parties",
        "2",
        str(c_path),
        "mpc",
        "--cost-model",
        "empirical",
        "--selection-scheme",
        selection_scheme,
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
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        return None, str(output)
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
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Max seconds per compilation before killing it.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    benchmarks_dir = repo_root / "benchmarks"
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "benchmark",
        "size",
        "selection_scheme",
        "run",
        "timestamp",
        "ilp_time_assignment",
        "status",
        "error",
    ]
    seen = set()
    if output_path.exists():
        with output_path.open(newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = (
                    row.get("benchmark"),
                    row.get("size"),
                    row.get("selection_scheme"),
                    row.get("run"),
                )
                if key != (None, None, None, None):
                    seen.add(key)

    write_header = not output_path.exists()
    with output_path.open("a", newline="") as csvfile, log_path.open("w") as log_file:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for benchmark, size, c_path in iter_benchmarks(benchmarks_dir):
            for selection_scheme in iter_selection_schemes():
                for run in range(1, RUNS_PER_BENCHMARK + 1):
                    run_str = str(run)
                    if (benchmark, size, selection_scheme, run_str) in seen:
                        log_file.write(
                            f"[skip] {benchmark}/{size} {selection_scheme} run {run} already recorded\n"
                        )
                        log_file.flush()
                        continue

                    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                    header = f"[{timestamp}] {benchmark}/{size} ({selection_scheme}) run {run}/{RUNS_PER_BENCHMARK}"
                    command_display = (
                        f"{repo_root / 'target' / 'release' / 'examples' / 'circ'} "
                        f"--parties 2 {c_path} mpc --cost-model empirical "
                        f"--selection-scheme {selection_scheme} --part-size 8000 "
                        f"--mut-level 2 --mut-step-size 1 --graph-type 0"
                    )
                    log_file.write(f"{header} START\n")
                    log_file.write(f"COMMAND: {command_display}\n")
                    log_file.flush()

                    returncode, output = run_compile(
                        repo_root,
                        c_path,
                        selection_scheme,
                        args.timeout_seconds,
                    )
                    ilp_time = parse_ilp_time(output)

                    log_file.write(output)
                    log_file.write(f"{header} EXIT={returncode}\n")
                    log_file.flush()

                    if returncode is None:
                        timeout_message = (
                            f"compile exceeded {args.timeout_seconds}s; "
                            "killing circ processes"
                        )
                        subprocess.run(
                            [
                                "pkill",
                                "-f",
                                "/target/release/examples/circ",
                            ]
                        )
                        row = {
                            "benchmark": benchmark,
                            "size": size,
                            "selection_scheme": selection_scheme,
                            "run": run,
                            "timestamp": timestamp,
                            "ilp_time_assignment": "",
                            "status": "timeout",
                            "error": timeout_message,
                        }
                        writer.writerow(row)
                        csvfile.flush()
                        continue

                    if returncode != 0:
                        row = {
                            "benchmark": benchmark,
                            "size": size,
                            "selection_scheme": selection_scheme,
                            "run": run,
                            "timestamp": timestamp,
                            "ilp_time_assignment": "",
                            "status": "error",
                            "error": format_error(output, returncode),
                        }
                        writer.writerow(row)
                        csvfile.flush()
                        continue

                    if ilp_time is None:
                        row = {
                            "benchmark": benchmark,
                            "size": size,
                            "selection_scheme": selection_scheme,
                            "run": run,
                            "timestamp": timestamp,
                            "ilp_time_assignment": "",
                            "status": "missing_ilp_time",
                            "error": "ILP time not found in compiler output",
                        }
                        writer.writerow(row)
                        csvfile.flush()
                        continue

                    row = {
                        "benchmark": benchmark,
                        "size": size,
                        "selection_scheme": selection_scheme,
                        "run": run,
                        "timestamp": timestamp,
                        "ilp_time_assignment": ilp_time,
                        "status": "ok",
                        "error": "",
                    }
                    writer.writerow(row)
                    csvfile.flush()

    print(f"Results written to {output_path}")
    print(f"Detailed log written to {log_path}")


if __name__ == "__main__":
    main()
