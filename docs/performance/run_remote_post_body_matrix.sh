#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Не идём по возрастанию размера: иначе размер тела смешается со временем запуска.
readonly body_sizes=(
    1024 32 8192 128 65536 16 2048 64 16384 256 4096 512 32768
)

for body_bytes in "${body_sizes[@]}"; do
    printf '\n===== POST body: %s bytes =====\n' "$body_bytes"
    "$script_dir/run_remote_post_body_baseline.sh" "$body_bytes"
done
