#!/usr/bin/env python3

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


PROFILE_DIR = Path.home() / ".local/state/sclerotix-profile"
MEMRAY = Path.home() / ".local/share/sclerotix-profile-venv/bin/memray"


def newest_profile():
    profiles = sorted(
        PROFILE_DIR.glob("sclerotix-allocations-*.bin"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not profiles:
        raise SystemExit(f"No allocation profiles found in {PROFILE_DIR}")
    return profiles[0]


def previous_profile():
    profiles = sorted(
        PROFILE_DIR.glob("sclerotix-allocations-*.bin"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if len(profiles) < 2:
        raise SystemExit(f"Fewer than two allocation profiles found in {PROFILE_DIR}")
    return profiles[1]


def read_stats(profile):
    with tempfile.TemporaryDirectory() as temporary_directory:
        output = Path(temporary_directory) / "stats.json"
        subprocess.run(
            [
                str(MEMRAY),
                "stats",
                "-n",
                "1000",
                "--json",
                "-o",
                str(output),
                str(profile),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        with output.open(encoding="utf-8") as stats_file:
            return json.load(stats_file)


def focused_rows(stats, focus):
    rows = {}
    for row in stats["top_allocations_by_count"]:
        if focus in row["location"]:
            rows.setdefault(row["location"], {})["count"] = row["count"]
    for row in stats["top_allocations_by_size"]:
        if focus in row["location"]:
            rows.setdefault(row["location"], {})["size"] = row["size"]
    return rows


def print_full_report(label, profile, stats, top, requests):
    print(f"\n{label}: {profile}")
    print(f"Total allocations:     {stats['total_num_allocations']:,}")
    print(f"Total bytes allocated: {stats['total_bytes_allocated']:,}")
    if requests:
        print(f"Requests:              {requests:,}")
        print(
            f"Allocations/request:   "
            f"{stats['total_num_allocations'] / requests:,.3f}"
        )
        print(
            f"Bytes/request:         "
            f"{stats['total_bytes_allocated'] / requests:,.3f}"
        )

    print(f"\nTOP {top} BY ALLOCATION COUNT")
    print(f"{'location':100} {'allocations':>15}")
    for row in stats["top_allocations_by_count"][:top]:
        print(f"{row['location']:100} {row['count']:>15,}")

    print(f"\nTOP {top} BY ALLOCATED BYTES")
    print(f"{'location':100} {'bytes':>15}")
    for row in stats["top_allocations_by_size"][:top]:
        print(f"{row['location']:100} {row['size']:>15,}")


def print_report(label, profile, stats, focus, min_count):
    print(f"\n{label}: {profile}")
    print(f"Total allocations:     {stats['total_num_allocations']:,}")
    print(f"Total bytes allocated: {stats['total_bytes_allocated']:,}")
    print(f"\nFocus: {focus}")
    print(f"{'location':70} {'allocations':>15} {'bytes':>15}")
    for location, values in focused_rows(stats, focus).items():
        if values.get("count", 0) < min_count:
            continue
        print(
            f"{location:70} "
            f"{values.get('count', 0):>15,} "
            f"{values.get('size', 0):>15,}"
        )


def print_delta(current, baseline, focus, min_count):
    current_rows = focused_rows(current, focus)
    baseline_rows = focused_rows(baseline, focus)
    locations = sorted(current_rows.keys() | baseline_rows.keys())

    print("\nDELTA CURRENT - BASELINE")
    print(
        f"Total allocations:     "
        f"{current['total_num_allocations'] - baseline['total_num_allocations']:+,}"
    )
    print(
        f"Total bytes allocated: "
        f"{current['total_bytes_allocated'] - baseline['total_bytes_allocated']:+,}"
    )
    print(f"\n{'location':70} {'allocations':>15} {'bytes':>15}")
    for location in locations:
        current_values = current_rows.get(location, {})
        baseline_values = baseline_rows.get(location, {})
        if max(
            current_values.get("count", 0), baseline_values.get("count", 0)
        ) < min_count:
            continue
        count_delta = current_values.get("count", 0) - baseline_values.get("count", 0)
        size_delta = current_values.get("size", 0) - baseline_values.get("size", 0)
        print(f"{location:70} {count_delta:>+15,} {size_delta:>+15,}")


def main():
    parser = argparse.ArgumentParser(
        description="Print a focused allocation report from Memray profiles."
    )
    parser.add_argument("focus", nargs="?", default="enum.py")
    parser.add_argument("--profile", type=Path, default=None)
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--previous", action="store_true")
    parser.add_argument("--min-count", type=int, default=10_000)
    parser.add_argument(
        "--full",
        action="store_true",
        help="print complete rankings instead of filtering by focus",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="number of rows in each full ranking (default: 30)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=None,
        help="request count used to print normalized totals",
    )
    args = parser.parse_args()

    if args.baseline and args.previous:
        parser.error("use either --baseline or --previous")
    if args.top < 1:
        parser.error("--top must be positive")
    if args.requests is not None and args.requests < 1:
        parser.error("--requests must be positive")

    profile = args.profile or newest_profile()
    current = read_stats(profile)
    if args.full:
        print_full_report("CURRENT", profile, current, args.top, args.requests)
    else:
        print_report("CURRENT", profile, current, args.focus, args.min_count)

    baseline_profile = args.baseline
    if args.previous:
        baseline_profile = previous_profile()

    if baseline_profile:
        baseline = read_stats(baseline_profile)
        if args.full:
            print_full_report(
                "BASELINE", baseline_profile, baseline, args.top, args.requests
            )
        else:
            print_report(
                "BASELINE", baseline_profile, baseline, args.focus, args.min_count
            )
            print_delta(current, baseline, args.focus, args.min_count)


if __name__ == "__main__":
    main()
