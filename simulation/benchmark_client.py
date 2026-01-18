#!/usr/bin/env python3
import argparse
import json
import os
import socket
import subprocess
from datetime import datetime
from pathlib import Path

DEFAULT_COMPILE_TIMEOUT_SECONDS = 120


def timestamp():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


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
    repo_root: Path, benchmark: str, size: str, log_file, timeout_seconds: int
):
    c_path = repo_root / "benchmarks" / benchmark / size / f"{benchmark}.c"
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

    log_file.write(f"{timestamp()} CLIENT compile command: {' '.join(command)}\n")
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
        log_file.write(f"{timestamp()} CLIENT compile timeout\n")
        log_file.flush()
        subprocess.run(["pkill", "-f", "/target/release/examples/circ"])
        return False

    log_file.write(result.stdout)
    log_file.write(f"{timestamp()} CLIENT compile exit={result.returncode}\n")
    log_file.flush()
    return result.returncode == 0


def run_party(
    repo_root: Path,
    benchmark: str,
    size: str,
    role: int,
    log_file,
    timeout_seconds: int,
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
        "127.0.0.1",
        "-p",
        "7766",
    ]
    log_file.write(f"{timestamp()} CLIENT party{role} command: {' '.join(command)}\n")
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
        log_file.write(f"{timestamp()} CLIENT party{role} timeout\n")
        log_file.flush()
        subprocess.run(["pkill", "-f", "aby_interpreter"])
        return False

    log_file.write(result.stdout)
    log_file.write(f"{timestamp()} CLIENT party{role} exit={result.returncode}\n")
    log_file.flush()
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Client benchmark runner.")
    parser.add_argument("--server-host", required=True, help="Server host/IP.")
    parser.add_argument("--server-port", type=int, default=9000, help="Server port.")
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
        default="simulation/results/client_benchmark.log",
        help="Log file path.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w") as log_file:
        log_file.write(
            f"{timestamp()} CLIENT connecting to {args.server_host}:{args.server_port}\n"
        )
        log_file.flush()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((args.server_host, args.server_port))
            while True:
                message = recv_message(sock)
                if not message:
                    log_file.write(f"{timestamp()} CLIENT connection closed\n")
                    log_file.flush()
                    break

                msg_type = message.get("type")
                if msg_type == "compile":
                    benchmark = message.get("benchmark")
                    size = message.get("size")
                    log_file.write(
                        f"{timestamp()} CLIENT compile request {benchmark}/{size}\n"
                    )
                    log_file.flush()
                    success = compile_benchmark(
                        repo_root,
                        benchmark,
                        size,
                        log_file,
                        args.compile_timeout_seconds,
                    )
                    send_message(
                        sock,
                        {
                            "type": "compile_done",
                            "benchmark": benchmark,
                            "size": size,
                            "success": success,
                        },
                    )
                    continue

                if msg_type == "run":
                    benchmark = message.get("benchmark")
                    size = message.get("size")
                    log_file.write(
                        f"{timestamp()} CLIENT run request {benchmark}/{size}\n"
                    )
                    log_file.flush()
                    run_party(
                        repo_root,
                        benchmark,
                        size,
                        1,
                        log_file,
                        args.timeout_seconds,
                    )
                    continue

                if msg_type == "compile_failed":
                    benchmark = message.get("benchmark")
                    size = message.get("size")
                    log_file.write(
                        f"{timestamp()} CLIENT server compile failed {benchmark}/{size}\n"
                    )
                    log_file.flush()
                    continue

                if msg_type == "done":
                    log_file.write(f"{timestamp()} CLIENT done\n")
                    log_file.flush()
                    break


if __name__ == "__main__":
    main()
