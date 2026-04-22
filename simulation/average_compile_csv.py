#!/usr/bin/env python3
"""Aggregate per-run rows in ILP_time.csv into one row per (benchmark, size, scheme).

Average is taken over the runs that finished with status=ok; error/timeout rows are
not counted toward the mean. The error column is rewritten to a human-readable label:
  * any exit -9 in the group -> "OUT OF MEMORY"
  * any timeout in the group -> "TIMEOUT"
  * both present              -> "OUT OF MEMORY/TIMEOUT"
  * otherwise                 -> ""
"""
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT = SCRIPT_DIR / "results" / "ILP_time.csv"
OUTPUT = SCRIPT_DIR / "results" / "ILP_time_average.csv"

EXIT_CODE_RE = re.compile(r"exit\s+(-?\d+)")


def classify(rows):
    oom = any(
        r["status"] == "error"
        and (m := EXIT_CODE_RE.search(r["error"]))
        and m.group(1) == "-9"
        for r in rows
    )
    timeout = any(r["status"] == "timeout" for r in rows)

    if oom and timeout:
        error_label = "OUT OF MEMORY/TIMEOUT"
    elif oom:
        error_label = "OUT OF MEMORY"
    elif timeout:
        error_label = "TIMEOUT"
    else:
        error_label = ""

    status = Counter(r["status"] for r in rows).most_common(1)[0][0]
    return status, error_label


def main():
    groups = defaultdict(list)
    with INPUT.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["benchmark"], row["size"], row["selection_scheme"])
            groups[key].append(row)

    fieldnames = [
        "benchmark",
        "size",
        "selection_scheme",
        "timestamp",
        "ilp_time_assignment",
        "status",
        "error",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(groups):
            rows = groups[key]
            ok_times = [
                float(r["ilp_time_assignment"])
                for r in rows
                if r["status"] == "ok" and r["ilp_time_assignment"]
            ]
            avg = f"{fmean(ok_times):.6f}" if ok_times else ""
            status, error_label = classify(rows)
            writer.writerow(
                {
                    "benchmark": key[0],
                    "size": key[1],
                    "selection_scheme": key[2],
                    "timestamp": max(r["timestamp"] for r in rows),
                    "ilp_time_assignment": avg,
                    "status": status,
                    "error": error_label,
                }
            )
    print(f"Wrote {len(groups)} grouped rows to {OUTPUT}")


if __name__ == "__main__":
    main()
