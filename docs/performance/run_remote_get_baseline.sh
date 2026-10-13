#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$script_dir/../.." && pwd)"
cd "$project_dir"

readonly request_id="get_index_empty"
readonly profile="baseline_remote_get_10k_10s_port18082"
readonly rate="10000/s"
readonly duration="10s"
readonly runs=5
readonly warmup_duration="5s"
readonly workers=10
readonly connections=100
readonly port=18082
readonly server_cpu=3
readonly vegeta_cpus="4,5,10,11"
readonly cooldown_margin=100
readonly cooldown_timeout=180
readonly target_file="docs/performance/requests/get_index_empty.targets"

vegeta="${VEGETA:-$HOME/.local/bin/vegeta}"
python="${PYTHON:-python3}"
server_pid=""

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

stop_server() {
    if [[ -n "$server_pid" ]] && kill -0 "$server_pid" 2>/dev/null; then
        kill -TERM "$server_pid" 2>/dev/null || true
        for _ in {1..50}; do
            if ! kill -0 "$server_pid" 2>/dev/null; then
                break
            fi
            sleep 0.1
        done
        if kill -0 "$server_pid" 2>/dev/null; then
            printf 'Server did not stop after SIGTERM; sending SIGKILL\n' >&2
            kill -KILL "$server_pid" 2>/dev/null || true
        fi
        wait "$server_pid" 2>/dev/null || true
    fi
    server_pid=""
}

trap stop_server EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

time_wait_count() {
    ss -tan state time-wait 2>/dev/null | awk 'NR > 1 { count += 1 } END { print count + 0 }'
}

wait_for_cooldown() {
    local started now count
    started="$(date +%s)"
    while true; do
        count="$(time_wait_count)"
        if (( count <= time_wait_limit )); then
            printf 'TCP cooldown complete: TIME_WAIT=%d (limit=%d)\n' \
                "$count" "$time_wait_limit"
            return
        fi
        now="$(date +%s)"
        if (( now - started >= cooldown_timeout )); then
            fail "TIME_WAIT stayed at $count above limit $time_wait_limit for ${cooldown_timeout}s"
        fi
        printf 'Waiting for TCP cooldown: TIME_WAIT=%d, limit=%d\n' \
            "$count" "$time_wait_limit"
        sleep 5
    done
}

start_server() {
    local log_file="$1"
    if ss -ltnH "( sport = :$port )" | grep -q .; then
        fail "port $port is already occupied"
    fi

    taskset -c "$server_cpu" "$python" run_performance_server.py \
        >"$log_file" 2>&1 &
    server_pid=$!

    for _ in {1..50}; do
        if ! kill -0 "$server_pid" 2>/dev/null; then
            wait "$server_pid" || true
            fail "Sclerotix exited during startup; see $log_file"
        fi
        if ss -ltnH "( sport = :$port )" | grep -q .; then
            return
        fi
        sleep 0.1
    done
    fail "Sclerotix did not listen on port $port; see $log_file"
}

run_attack() {
    local run_dir="$1"
    local attack_duration="$2"
    local attack_name="$3"

    mkdir -p "$run_dir"
    taskset -c "$vegeta_cpus" "$vegeta" attack \
        -name="$attack_name" \
        -targets="$target_file" \
        -rate="$rate" \
        -duration="$attack_duration" \
        -workers="$workers" \
        -connections="$connections" \
        -keepalive=false \
        -http2=false \
        -output="$run_dir/results.gob"

    "$vegeta" encode -to=csv \
        -output="$run_dir/samples.csv" "$run_dir/results.gob"
    "$vegeta" report -type=json \
        -output="$run_dir/report.json" "$run_dir/results.gob"
}

validate_report() {
    local report="$1"
    "$python" - "$report" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as report_file:
    report = json.load(report_file)

statuses = report.get("status_codes", {})
if report.get("success") != 1 or set(statuses) != {"200"}:
    raise SystemExit(
        f"invalid run: success={report.get('success')} statuses={statuses} "
        f"errors={report.get('errors')}"
    )
print(
    f"requests={report['requests']} throughput={report['throughput']:.2f} "
    f"p50={report['latencies']['50th'] / 1_000_000:.3f}ms "
    f"p99={report['latencies']['99th'] / 1_000_000:.3f}ms"
)
PY
}

write_metadata() {
    local run_dir="$1"
    local run_index="$2"
    local started_at="$3"
    local time_wait_before="$4"
    {
        printf 'STARTED_AT_UTC=%s\n' "$started_at"
        printf 'GIT_COMMIT=%s\n' "$git_commit"
        printf 'GIT_TAG=%s\n' "$git_tag"
        printf 'GIT_DIRTY=false\n'
        printf 'HOST_ID=%s\n' "$host_id"
        printf 'KERNEL=%s\n' "$kernel"
        printf 'PYTHON_VERSION=%s\n' "$python_version"
        printf 'VEGETA_VERSION=%s\n' "$vegeta_version"
        printf 'REQUEST_ID=%s\n' "$request_id"
        printf 'PROFILE=%s\n' "$profile"
        printf 'PORT=%s\n' "$port"
        printf 'RATE=%s\n' "$rate"
        printf 'DURATION=%s\n' "$duration"
        printf 'WORKERS=%s\n' "$workers"
        printf 'CONNECTIONS=%s\n' "$connections"
        printf 'KEEPALIVE=false\n'
        printf 'HTTP2=false\n'
        printf 'SERVER_CPU=%s\n' "$server_cpu"
        printf 'VEGETA_CPUS=%s\n' "$vegeta_cpus"
        printf 'ULIMIT_NOFILE=%s\n' "$(ulimit -n)"
        printf 'TIME_WAIT_BEFORE=%s\n' "$time_wait_before"
        printf 'RUN_INDEX=%s\n' "$run_index"
    } >"$run_dir/metadata.env"
}

summarize_series() {
    "$python" - "$series_dir" "$git_commit" <<'PY'
import csv
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

series_dir = Path(sys.argv[1])
commit = sys.argv[2]
rows = []
combined = []

def read_metadata(path):
    metadata = {}
    with path.open(encoding="utf-8") as source:
        for line in source:
            key, value = line.rstrip("\n").split("=", 1)
            metadata[key] = value
    return metadata

for run_dir in sorted(series_dir.glob("run-*")):
    metadata = read_metadata(run_dir / "metadata.env")
    with (run_dir / "report.json").open(encoding="utf-8") as report_file:
        report = json.load(report_file)
    latencies = []
    with (run_dir / "samples.csv").open(newline="", encoding="utf-8") as source:
        for row in csv.reader(source):
            latencies.append(int(row[2]))
    combined.extend(latencies)
    latencies.sort()

    def percentile(values, probability):
        return values[max(0, math.ceil(probability * len(values)) - 1)]

    rows.append(
        {
            "run": run_dir.name,
            "sample_n": len(latencies),
            "success": report["success"],
            "throughput_rps": report["throughput"],
            "mean_ns": statistics.fmean(latencies),
            "stddev_ns": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "min_ns": latencies[0],
            "p50_ns": percentile(latencies, 0.50),
            "p90_ns": percentile(latencies, 0.90),
            "p95_ns": percentile(latencies, 0.95),
            "p99_ns": percentile(latencies, 0.99),
            "max_ns": latencies[-1],
            "metadata": metadata,
            "raw_csv": str(run_dir / "samples.csv"),
        }
    )

series_fieldnames = [name for name in rows[0] if name not in {"metadata", "raw_csv"}]
with (series_dir / "series-summary.csv").open("w", newline="", encoding="utf-8") as target:
    writer = csv.DictWriter(target, fieldnames=series_fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

global_summary = Path("var/performance/summary.csv")
global_fieldnames = [
    "started_at_utc", "date_utc", "commit", "tag", "dirty", "host_id",
    "python_version", "vegeta_version", "request_id", "method", "path",
    "body_bytes", "expected_status", "rate_rps", "duration_s", "workers",
    "connections", "keepalive", "run_index", "sample_n", "valid",
    "success_ratio", "mean_ns", "stddev_ns", "min_ns", "p50_ns", "p90_ns",
    "p95_ns", "p99_ns", "max_ns", "throughput_rps", "raw_csv", "notes",
]
write_header = not global_summary.exists() or global_summary.stat().st_size == 0
global_summary.parent.mkdir(parents=True, exist_ok=True)
with global_summary.open("a", newline="", encoding="utf-8") as target:
    writer = csv.DictWriter(target, fieldnames=global_fieldnames)
    if write_header:
        writer.writeheader()
    for row in rows:
        metadata = row["metadata"]
        started_at = metadata["STARTED_AT_UTC"]
        writer.writerow(
            {
                "started_at_utc": started_at,
                "date_utc": datetime.fromisoformat(started_at.removesuffix("Z")).date(),
                "commit": metadata["GIT_COMMIT"],
                "tag": metadata["GIT_TAG"],
                "dirty": metadata["GIT_DIRTY"],
                "host_id": metadata["HOST_ID"],
                "python_version": metadata["PYTHON_VERSION"],
                "vegeta_version": metadata["VEGETA_VERSION"],
                "request_id": metadata["REQUEST_ID"],
                "method": "GET",
                "path": "/index.html",
                "body_bytes": 0,
                "expected_status": 200,
                "rate_rps": 10000,
                "duration_s": 10,
                "workers": metadata["WORKERS"],
                "connections": metadata["CONNECTIONS"],
                "keepalive": False,
                "run_index": metadata["RUN_INDEX"],
                "sample_n": row["sample_n"],
                "valid": True,
                "success_ratio": row["success"],
                "mean_ns": f"{row['mean_ns']:.6f}",
                "stddev_ns": f"{row['stddev_ns']:.6f}",
                "min_ns": row["min_ns"],
                "p50_ns": row["p50_ns"],
                "p90_ns": row["p90_ns"],
                "p95_ns": row["p95_ns"],
                "p99_ns": row["p99_ns"],
                "max_ns": row["max_ns"],
                "throughput_rps": f"{row['throughput_rps']:.6f}",
                "raw_csv": row["raw_csv"],
                "notes": "automated_baseline_remote_get_10k_10s_port18082",
            }
        )

combined.sort()

def percentile(values, probability):
    return values[max(0, math.ceil(probability * len(values)) - 1)]

summary = {
    "schema_version": 1,
    "profile": {
        "name": "baseline_remote_get_10k_10s_port18082",
        "host_id": rows[0]["metadata"]["HOST_ID"],
        "request_id": rows[0]["metadata"]["REQUEST_ID"],
        "port": int(rows[0]["metadata"]["PORT"]),
        "rate_rps": 10000,
        "duration_s": 10,
        "runs": len(rows),
        "workers": int(rows[0]["metadata"]["WORKERS"]),
        "connections": int(rows[0]["metadata"]["CONNECTIONS"]),
        "keepalive": False,
        "server_cpu": int(rows[0]["metadata"]["SERVER_CPU"]),
        "vegeta_cpus": rows[0]["metadata"]["VEGETA_CPUS"],
    },
    "commit": commit,
    "sample_n": len(combined),
    "mean_ns": statistics.fmean(combined),
    "stddev_ns": statistics.stdev(combined) if len(combined) > 1 else 0,
    "min_ns": combined[0],
    "p50_ns": percentile(combined, 0.50),
    "p95_ns": percentile(combined, 0.95),
    "p99_ns": percentile(combined, 0.99),
    "max_ns": combined[-1],
}
with (series_dir / "combined-summary.json").open("w", encoding="utf-8") as target:
    json.dump(summary, target, indent=2)
    target.write("\n")

print("\nCOMBINED SERIES")
print(f"commit:   {commit}")
print(f"sample_n: {summary['sample_n']:,}")
for name in ("mean_ns", "stddev_ns", "min_ns", "p50_ns", "p95_ns", "p99_ns", "max_ns"):
    print(f"{name[:-3]:8} {summary[name] / 1_000_000:.3f} ms")
print(f"raw:      {series_dir}")
print("compare:  ./docs/performance/compare_baseline.py")
PY
}

require_command taskset
require_command ss
require_command git
require_command "$python"
[[ -x "$vegeta" ]] || fail "Vegeta is not executable at $vegeta"
[[ -f "$target_file" ]] || fail "target file not found: $target_file"

max_cpu="$(getconf _NPROCESSORS_ONLN)"
(( max_cpu > 11 )) || fail "this profile requires logical CPUs 0-11"

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    fail "tracked worktree changes found; commit them before measuring"
fi

if ss -ltnH "( sport = :$port )" | grep -q .; then
    fail "port $port is already occupied"
fi

ulimit -n 65535 || fail "cannot raise open-file limit to 65535"

git_commit="$(git rev-parse HEAD)"
git_tag="$(git describe --tags --exact-match 2>/dev/null || true)"
host_id="$(hostname)"
kernel="$(uname -sr)"
python_version="$($python --version 2>&1)"
vegeta_version="$($vegeta --version 2>&1 | paste -sd ' ' -)"
background_time_wait="$(time_wait_count)"
time_wait_limit=$(( background_time_wait + cooldown_margin ))
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
day="$(date -u +%F)"
series_dir="var/performance/raw/$day/$request_id/$profile/$timestamp"
mkdir -p "$series_dir"

printf 'Profile:             %s\n' "$profile"
printf 'Commit:              %s\n' "$git_commit"
printf 'Output:              %s\n' "$series_dir"
printf 'Background TIME_WAIT:%s (cooldown limit %s)\n' \
    "$background_time_wait" "$time_wait_limit"
printf 'Storm workers must already be stopped.\n\n'

wait_for_cooldown
start_server "$series_dir/warmup-server.log"
run_attack "$series_dir/warmup" "$warmup_duration" "${request_id}_warmup"
validate_report "$series_dir/warmup/report.json"
stop_server

for run_index in $(seq 1 "$runs"); do
    wait_for_cooldown
    run_name="$(printf 'run-%03d' "$run_index")"
    run_dir="$series_dir/$run_name"
    started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    time_wait_before="$(time_wait_count)"

    printf '\nStarting %s/%s: %s\n' "$run_index" "$runs" "$run_name"
    mkdir -p "$run_dir"
    write_metadata "$run_dir" "$run_index" "$started_at" "$time_wait_before"
    start_server "$run_dir/server.log"
    run_attack "$run_dir" "$duration" "${request_id}_${run_name}"
    stop_server
    validate_report "$run_dir/report.json"
done

summarize_series
