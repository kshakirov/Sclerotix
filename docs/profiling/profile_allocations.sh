#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$script_dir/../.." && pwd)"
cd "$project_dir"

port="${1:-18082}"
server_script="${SERVER_SCRIPT:-event_pool.py}"
profiler="$HOME/.local/share/sclerotix-profile-venv/bin/memray"
output_dir="$HOME/.local/state/sclerotix-profile"

if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port <= 10000 || port > 65535 )); then
  echo "Port must be a number between 10001 and 65535" >&2
  exit 2
fi

if [[ "$port" != 18082 ]]; then
  echo "Selected server scripts listen on port 18082; use that port" >&2
  exit 2
fi
[[ -f "$server_script" ]] || { echo "Server script not found: $server_script" >&2; exit 1; }

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
echo "Server:  $server_script"
echo "Listen:  127.0.0.1:$port"
echo "Profile: $output"
echo "Stop with Ctrl-C after the load finishes"
printf 'GIT_COMMIT=%s\nSERVER_SCRIPT=%s\nPORT=%s\n' \
  "$(git rev-parse HEAD)" "$server_script" "$port" > "$output.metadata.env"

exec "$profiler" run \
  --trace-python-allocators \
  --compress-on-exit \
  -o "$output" \
  "$server_script"
