#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE = (
    PROJECT_DIR
    / "docs/performance/baselines/pmd-pims-aio-get-10k-2026-10-06.json"
)
RAW_DIR = PROJECT_DIR / "var/performance/raw"
METRICS = (
    ("mean_ns", "Mean"),
    ("stddev_ns", "Stddev"),
    ("min_ns", "Min"),
    ("p50_ns", "P50"),
    ("p95_ns", "P95"),
    ("p99_ns", "P99"),
    ("max_ns", "Max"),
)
PROFILE_FIELDS = (
    "host_id",
    "request_id",
    "port",
    "rate_rps",
    "duration_s",
    "runs",
    "workers",
    "connections",
    "keepalive",
    "server_cpu",
    "vegeta_cpus",
)


def latest_summary():
    summaries = sorted(
        RAW_DIR.glob("**/combined-summary.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not summaries:
        raise SystemExit(f"No combined-summary.json found under {RAW_DIR}")
    return summaries[0]


def read_summary(path):
    try:
        with path.open(encoding="utf-8") as source:
            summary = json.load(source)
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Cannot read {path}: {error}") from error

    missing = [name for name, _ in METRICS if name not in summary]
    if missing:
        raise SystemExit(f"{path} misses metrics: {', '.join(missing)}")
    return summary


def compare_profiles(baseline, current):
    baseline_profile = baseline.get("profile")
    current_profile = current.get("profile")
    if not baseline_profile or not current_profile:
        print("WARNING: profile metadata is absent; compatibility was not verified.")
        return

    differences = []
    for field in PROFILE_FIELDS:
        before = baseline_profile.get(field)
        after = current_profile.get(field)
        if before != after:
            differences.append((field, before, after))

    if not differences:
        print("Profile compatibility: exact match")
        return

    print("WARNING: profiles differ:")
    for field, before, after in differences:
        print(f"  {field}: {before!r} -> {after!r}")


def format_commit(summary):
    commit = summary.get("commit", "unknown")
    return commit[:12]


def print_comparison(baseline_path, current_path, baseline, current):
    print(f"BASELINE: {baseline_path}")
    print(f"CURRENT:  {current_path}")
    print(f"Commits:  {format_commit(baseline)} -> {format_commit(current)}")
    print(
        f"Samples:  {baseline.get('sample_n', 'unknown')} -> "
        f"{current.get('sample_n', 'unknown')}"
    )
    compare_profiles(baseline, current)

    if baseline.get("source_values_rounded_to_ms"):
        print("WARNING: baseline metrics were recorded with 0.001 ms precision.")

    print()
    print(f"{'metric':8} {'baseline':>12} {'current':>12} {'delta':>12} {'change':>10} {'result':>11}")
    for key, label in METRICS:
        before = baseline[key]
        after = current[key]
        delta = after - before
        change = delta / before * 100 if before else float("nan")
        if delta < 0:
            result = "improved"
        elif delta > 0:
            result = "regressed"
        else:
            result = "unchanged"
        print(
            f"{label:8} "
            f"{before / 1_000_000:>9.3f} ms "
            f"{after / 1_000_000:>9.3f} ms "
            f"{delta / 1_000_000:>+9.3f} ms "
            f"{change:>+9.1f}% "
            f"{result:>11}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Compare a Sclerotix performance series with a baseline."
    )
    parser.add_argument(
        "current",
        nargs="?",
        type=Path,
        help="current combined-summary.json; defaults to the newest raw summary",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="baseline JSON",
    )
    args = parser.parse_args()

    baseline_path = args.baseline.resolve()
    current_path = (args.current or latest_summary()).resolve()
    baseline = read_summary(baseline_path)
    current = read_summary(current_path)
    print_comparison(baseline_path, current_path, baseline, current)


if __name__ == "__main__":
    main()
