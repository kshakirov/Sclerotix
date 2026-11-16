#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."
port="${1:-8080}"
rate="${RATE:-100/s}"
duration="${DURATION:-5s}"
vegeta="${VEGETA:-$HOME/.local/bin/vegeta}"

[[ "$port" =~ ^[0-9]+$ ]] && (( port >= 1024 && port <= 65535 )) || {
    echo 'Port must be between 1024 and 65535' >&2; exit 1;
}
[[ -x "$vegeta" ]] || { echo "Vegeta not found: $vegeta" >&2; exit 1; }
[[ -n "$(ss -ltnH "( sport = :$port )")" ]] || {
    echo "Start event_pool.py on 127.0.0.1:$port first" >&2; exit 1;
}

mkdir -p var/performance/raw/event_pool_smoke
run_dir="$(mktemp -d "var/performance/raw/event_pool_smoke/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXXXX")"
printf '0123456789abcdef' > "$run_dir/body.bin"
printf 'COMMIT=%s\nPORT=%s\nRATE=%s\nDURATION=%s\n' \
    "$(git rev-parse HEAD)" "$port" "$rate" "$duration" > "$run_dir/metadata.env"
printf 'POST 16 B, %s, %s; existing server on port %s\nResults: %s\n' \
    "$rate" "$duration" "$port" "$run_dir"

printf 'POST http://127.0.0.1:%s/index.html\n' "$port" | "$vegeta" attack \
    -rate="$rate" -duration="$duration" -timeout=3s \
    -workers=2 -max-workers=2 -connections=2 -keepalive=false -http2=false \
    -body="$run_dir/body.bin" -output="$run_dir/results.gob"
"$vegeta" report -type=json "$run_dir/results.gob" > "$run_dir/report.json"
"$vegeta" report "$run_dir/results.gob"
python3 - "$run_dir/report.json" <<'PY'
import json
import sys
with open(sys.argv[1]) as source:
    report = json.load(source)
if not report['requests'] or report['success'] != 1 or set(report['status_codes']) != {'200'}:
    raise SystemExit(f"FAILED: statuses={report['status_codes']}, errors={report['errors']}")
PY
