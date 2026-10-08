#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$script_dir/../.." && pwd)"
cd "$project_dir"

port="${1:-18082}"
profiler="$HOME/.local/share/sclerotix-profile-venv/bin/memray"
output_dir="$HOME/.local/state/sclerotix-profile"

if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port <= 10000 || port > 65535 )); then
  echo "Port must be a number between 10001 and 65535" >&2
  exit 2
fi

if ss -ltnH "( sport = :$port )" | grep -q .; then
  echo "Port $port is already in use" >&2
  exit 1
fi

if [[ ! -x "$profiler" ]]; then
  echo "Memray is not installed at $profiler" >&2
  exit 1
fi

mkdir -p "$output_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="$output_dir/sclerotix-allocations-$timestamp.bin"

echo "Project: $project_dir"
echo "Listen:  127.0.0.1:$port"
echo "Profile: $output"
echo "Stop with Ctrl-C after the load finishes"

exec "$profiler" run \
  --trace-python-allocators \
  --compress-on-exit \
  -o "$output" \
  -c "import run_server_epoll as s; s.run_event_loop(host='127.0.0.1', port=$port)"
