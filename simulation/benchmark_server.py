#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import socket
import subprocess
from datetime import datetime
from pathlib import Path

ASSIGNMENT_TIME_RE = re.compile(r"LOG: Assignment time: ([0-9.]+)(ms|s)")
ILP_TIME_RE = re.compile(r"LOG: ILP time: ([0-9.]+)(ms|s)")
SERVER_TOTAL_TIME_RE = re.compile(r"LOG: Server total time: ([0-9.]+)")
DEFAULT_COMPILE_TIMEOUT_SECONDS = 120


def iter_benchmarks(benchmarks_dir: Path):
    for c_path in sorted(benchmarks_dir.glob("*/*/*.c")):
        benchmark = c_path.parent.parent.name
        size = c_path.parent.name
        if c_path.name != f"{benchmark}.c":
            continue
        yield benchmark, size, c_path


def timestamp():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def parse_time_seconds(pattern: re.Pattern, output: str):
    matches = pattern.findall(output)
    if not matches:
        return None
    value, unit = matches[-1]
    seconds = float(value) / 1000 if unit == "ms" else float(value)
    return f"{seconds:.6f}"


def parse_total_time(pattern: re.Pattern, output: str):
    matches = pattern.findall(output)
    if not matches:
        return None
    return f"{float(matches[-1]):.6f}"


def send_message(conn: socket.socket, payload: dict):
    message = json.dumps(payload).encode("utf-8") + b"\n"
    conn.sendall(message)


def recv_message(conn: socket.socket):
    buffer = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            return None
        buffer += chunk
        if b"\n" in buffer:
            line, _, buffer = buffer.partition(b"\n")
            return json.loads(line.decode("utf-8"))


def compile_benchmark(
    repo_root: Path,
    c_path: Path,
    log_file,
    timeout_seconds: int,
    csv_writer,
    csv_file,
    benchmark: str,
    size: str,
    role: str,
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

    log_file.write(f"{timestamp()} SERVER compile command: {' '.join(command)}\n")
    log_file.flush()
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
        log_file.write(str(output))
        log_file.write(f"{timestamp()} SERVER compile timeout\n")
        log_file.flush()
        subprocess.run(["pkill", "-f", "/target/release/examples/circ"])
        csv_writer.writerow(
            {
                "benchmark": benchmark,
                "size": size,
                "timestamp": timestamp(),
                "role": role,
                "phase": "compile",
                "ilp_time_seconds": "",
                "assignment_time_seconds": "",
                "total_time_seconds": "",
                "status": "timeout",
                "error": f"compile exceeded {timeout_seconds}s",
            }
        )
        csv_file.flush()
        return False

    log_file.write(result.stdout)
    log_file.write(f"{timestamp()} SERVER compile exit={result.returncode}\n")
    log_file.flush()

    ilp_time = parse_time_seconds(ILP_TIME_RE, result.stdout)
    assignment_time = parse_time_seconds(ASSIGNMENT_TIME_RE, result.stdout)
    csv_writer.writerow(
        {
            "benchmark": benchmark,
            "size": size,
            "timestamp": timestamp(),
            "role": role,
            "phase": "compile",
            "ilp_time_seconds": ilp_time or "",
            "assignment_time_seconds": assignment_time or "",
            "total_time_seconds": "",
            "status": "ok" if result.returncode == 0 else "error",
            "error": "" if result.returncode == 0 else f"exit {result.returncode}",
        }
    )
    csv_file.flush()

    return result.returncode == 0


def run_party(
    repo_root: Path,
    benchmark: str,
    size: str,
    role: int,
    log_file,
    timeout_seconds: int,
    csv_writer,
    csv_file,
    role_label: str,
):
    test_path = repo_root / "benchmarks" / benchmark / size / f"{benchmark}_test.txt"
    command = [
        str(Path.home() / "ABY" / "build" / "bin" / "aby_interpreter"),
        "-m",
        "mpc",
        "-f",
        str(repo_root / "scripts" / "aby_tests" / "tests" / f"{benchmark}_c"),
        "-t",
        str(test_path),
        "-r",
        str(role),
        "-a",
        "0.0.0.0" if role == 0 else "127.0.0.1",
        "-p",
        "7766",
    ]
    log_file.write(f"{timestamp()} SERVER party{role} command: {' '.join(command)}\n")
    log_file.flush()
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        log_file.write(str(output))
        log_file.write(f"{timestamp()} SERVER party{role} timeout\n")
        log_file.flush()
        subprocess.run(["pkill", "-f", "aby_interpreter"])
        csv_writer.writerow(
            {
                "benchmark": benchmark,
                "size": size,
                "timestamp": timestamp(),
                "role": role_label,
                "phase": "run",
                "ilp_time_seconds": "",
                "assignment_time_seconds": "",
                "total_time_seconds": "",
                "status": "timeout",
                "error": f"run exceeded {timeout_seconds}s",
            }
        )
        csv_file.flush()
        return False

    log_file.write(result.stdout)
    log_file.write(f"{timestamp()} SERVER party{role} exit={result.returncode}\n")
    log_file.flush()

    total_time = parse_total_time(SERVER_TOTAL_TIME_RE, result.stdout)
    csv_writer.writerow(
        {
            "benchmark": benchmark,
            "size": size,
            "timestamp": timestamp(),
            "role": role_label,
            "phase": "run",
            "ilp_time_seconds": "",
            "assignment_time_seconds": "",
            "total_time_seconds": total_time or "",
            "status": "ok" if result.returncode == 0 else "error",
            "error": "" if result.returncode == 0 else f"exit {result.returncode}",
        }
    )
    csv_file.flush()
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Server benchmark runner.")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind host.")
    parser.add_argument("--port", type=int, default=9000, help="Server port.")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=600,
        help="Max seconds for party run.",
    )
    parser.add_argument(
        "--compile-timeout-seconds",
        type=int,
        default=DEFAULT_COMPILE_TIMEOUT_SECONDS,
        help="Max seconds for compilation before skipping.",
    )
    parser.add_argument(
        "--log-file",
        default="simulation/results/server_benchmark.log",
        help="Log file path.",
    )
    parser.add_argument(
        "--csv-file",
        default="simulation/results/server_benchmark.csv",
        help="CSV output path.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path = Path(args.csv_file)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "benchmark",
        "size",
        "timestamp",
        "role",
        "phase",
        "ilp_time_seconds",
        "assignment_time_seconds",
        "total_time_seconds",
        "status",
        "error",
    ]

    with log_path.open("w") as log_file, csv_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        log_file.write(f"{timestamp()} SERVER listening on {args.host}:{args.port}\n")
        log_file.flush()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((args.host, args.port))
            server_sock.listen(1)
            conn, addr = server_sock.accept()
            with conn:
                log_file.write(f"{timestamp()} SERVER client connected: {addr}\n")
                log_file.flush()

                for benchmark, size, c_path in iter_benchmarks(
                    repo_root / "benchmarks"
                ):
                    log_file.write(
                        f"{timestamp()} SERVER starting {benchmark}/{size}\n"
                    )
                    log_file.flush()
                    if not compile_benchmark(
                        repo_root,
                        c_path,
                        log_file,
                        args.compile_timeout_seconds,
                        writer,
                        csv_file,
                        benchmark,
                        size,
                        "server",
                    ):
                        send_message(
                            conn,
                            {
                                "type": "compile_failed",
                                "benchmark": benchmark,
                                "size": size,
                            },
                        )
                        continue

                    send_message(
                        conn,
                        {
                            "type": "compile",
                            "benchmark": benchmark,
                            "size": size,
                        },
                    )

                    response = recv_message(conn)
                    if not response or response.get("type") != "compile_done":
                        log_file.write(
                            f"{timestamp()} SERVER client compile missing for {benchmark}/{size}\n"
                        )
                        log_file.flush()
                        continue

                    send_message(
                        conn,
                        {
                            "type": "run",
                            "benchmark": benchmark,
                            "size": size,
                        },
                    )

                    run_party(
                        repo_root,
                        benchmark,
                        size,
                        0,
                        log_file,
                        args.timeout_seconds,
                        writer,
                        csv_file,
                        "server",
                    )

                send_message(conn, {"type": "done"})
                log_file.write(f"{timestamp()} SERVER completed all benchmarks\n")
                log_file.flush()


if __name__ == "__main__":
    main()
