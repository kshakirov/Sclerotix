#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$script_dir/../.." && pwd)"
cd "$project_dir"

port="${1:-18082}"
rate=5000/s
duration=10s
generator="$HOME/.local/bin/vegeta"

if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port <= 10000 || port > 65535 )); then
  echo "Port must be a number between 10001 and 65535" >&2
  exit 2
fi

if ! ss -ltnH "( sport = :$port )" | grep -q .; then
  echo "Nothing is listening on 127.0.0.1:$port" >&2
  exit 1
fi

if [[ ! -x "$generator" ]]; then
  echo "Vegeta is not installed at $generator" >&2
  exit 1
fi

day="$(date -u +%F)"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
run_dir="var/performance/raw/$day/post_index_16b/profile_5000rps_10s/$timestamp"
results="$run_dir/results.gob"
report="$run_dir/report.json"
samples="$run_dir/samples.csv"
body="$run_dir/body.bin"
target="http://127.0.0.1:$port/index.html"

mkdir -p "$run_dir"

echo "Target:   $target"
echo "Method:   POST"
echo "Body:     16 bytes"
echo "Rate:     $rate"
echo "Duration: $duration"
echo "Run:      $run_dir"

printf '0123456789abcdef' > "$body"

printf 'POST %s\nContent-Type: application/octet-stream\n' "$target" | "$generator" attack \
  -rate="$rate" \
  -duration="$duration" \
  -body="$body" \
  -name=post_index_16b_profile \
  -output="$results"

"$generator" report -type=json "$results" > "$report"
"$generator" encode --to csv --output "$samples" "$results"

python3 - "$report" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as report_file:
    report = json.load(report_file)

latencies = report["latencies"]
print(f"Requests:   {report['requests']}")
print(f"Throughput: {report['throughput']:.2f} requests/s")
print(f"Success:    {report['success']:.6f}")
print(f"Statuses:   {report['status_codes']}")
print(f"p50:        {latencies['50th'] / 1_000_000:.3f} ms")
print(f"p99:        {latencies['99th'] / 1_000_000:.3f} ms")
print(f"Max:        {latencies['max'] / 1_000_000:.3f} ms")
PY
