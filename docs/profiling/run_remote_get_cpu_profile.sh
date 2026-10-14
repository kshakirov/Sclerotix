#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$script_dir/../.." && pwd)"
cd "$project_dir"

readonly profile_name="cpu_remote_get_10k_10s_port18082"
readonly port=18082
readonly rate="10000/s"
readonly attack_duration="10s"
readonly profile_duration=20
readonly sample_rate=100
readonly workers=10
readonly connections=100
readonly profiler_cpu=0
readonly server_cpu=3
readonly vegeta_cpus="4,5,10,11"
readonly target_file="docs/performance/requests/get_index_empty.targets"

profiler="${PY_SPY:-$HOME/.local/share/sclerotix-profile-venv/bin/py-spy}"
vegeta="${VEGETA:-$HOME/.local/bin/vegeta}"
python="${PYTHON:-python3}"
profiler_pid=""

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

stop_profile() {
    if [[ -n "$profiler_pid" ]] && kill -0 "$profiler_pid" 2>/dev/null; then
        kill -TERM "$profiler_pid" 2>/dev/null || true
        for _ in {1..50}; do
            if ! kill -0 "$profiler_pid" 2>/dev/null; then
                break
            fi
            sleep 0.1
        done
        if kill -0 "$profiler_pid" 2>/dev/null; then
            kill -KILL "$profiler_pid" 2>/dev/null || true
        fi
        wait "$profiler_pid" 2>/dev/null || true
    fi
    profiler_pid=""
}

trap stop_profile EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

for command in taskset ss git "$python"; do
    command -v "$command" >/dev/null 2>&1 || fail "required command not found: $command"
done
[[ -x "$profiler" ]] || fail "py-spy is not executable at $profiler"
[[ -x "$vegeta" ]] || fail "Vegeta is not executable at $vegeta"
[[ -f "$target_file" ]] || fail "target file not found: $target_file"
(( $(getconf _NPROCESSORS_ONLN) > 11 )) || fail "this profile requires logical CPUs 0-11"

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    fail "tracked worktree changes found; commit them before measuring"
fi
if ss -ltnH "( sport = :$port )" | grep -q .; then
    fail "port $port is already occupied"
fi
ulimit -n 65535 || fail "cannot raise open-file limit to 65535"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_dir="$HOME/.local/state/sclerotix-profile/cpu/$timestamp"
mkdir -p "$output_dir"
profile="$output_dir/profile.json"
results="$output_dir/results.gob"
samples="$output_dir/samples.csv"
load_report="$output_dir/load-report.json"
cpu_report="$output_dir/cpu-top.txt"
metadata="$output_dir/metadata.env"

git_commit="$(git rev-parse HEAD)"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
    printf 'STARTED_AT_UTC=%s\n' "$started_at"
    printf 'GIT_COMMIT=%s\n' "$git_commit"
    printf 'HOST_ID=%s\n' "$(hostname)"
    printf 'PROFILE=%s\n' "$profile_name"
    printf 'PORT=%s\n' "$port"
    printf 'RATE=%s\n' "$rate"
    printf 'ATTACK_DURATION=%s\n' "$attack_duration"
    printf 'PROFILE_DURATION=%s\n' "$profile_duration"
    printf 'SAMPLE_RATE=%s\n' "$sample_rate"
    printf 'WORKERS=%s\n' "$workers"
    printf 'CONNECTIONS=%s\n' "$connections"
    printf 'KEEPALIVE=false\n'
    printf 'SERVER_CPU=%s\n' "$server_cpu"
    printf 'PROFILER_CPU=%s\n' "$profiler_cpu"
    printf 'VEGETA_CPUS=%s\n' "$vegeta_cpus"
    printf 'ULIMIT_NOFILE=%s\n' "$(ulimit -n)"
} >"$metadata"

printf 'Profile: %s\nCommit:  %s\nOutput:  %s\n' \
    "$profile_name" "$git_commit" "$output_dir"

taskset -c "$profiler_cpu" "$profiler" record \
    --rate "$sample_rate" \
    --duration "$profile_duration" \
    --idle \
    --format speedscope \
    -o "$profile" \
    -- taskset -c "$server_cpu" "$python" -u run_performance_server.py \
    >"$output_dir/server-and-profiler.log" 2>&1 &
profiler_pid=$!

for _ in {1..100}; do
    if ! kill -0 "$profiler_pid" 2>/dev/null; then
        wait "$profiler_pid" || true
        fail "profiler or server exited during startup; see server-and-profiler.log"
    fi
    if ss -ltnH "( sport = :$port )" | grep -q .; then
        break
    fi
    sleep 0.1
done
ss -ltnH "( sport = :$port )" | grep -q . || fail "server did not listen on port $port"

sleep 1
taskset -c "$vegeta_cpus" "$vegeta" attack \
    -name="$profile_name" \
    -targets="$target_file" \
    -rate="$rate" \
    -duration="$attack_duration" \
    -workers="$workers" \
    -connections="$connections" \
    -keepalive=false \
    -http2=false \
    -output="$results"

"$vegeta" encode -to=csv -output="$samples" "$results"
"$vegeta" report -type=json -output="$load_report" "$results"

"$python" - "$load_report" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    report = json.load(source)
statuses = report.get("status_codes", {})
if report.get("success") != 1 or set(statuses) != {"200"}:
    raise SystemExit(
        f"invalid load: success={report.get('success')} statuses={statuses} "
        f"errors={report.get('errors')}"
    )
print(
    f"requests={report['requests']} throughput={report['throughput']:.2f} "
    f"p50={report['latencies']['50th'] / 1_000_000:.3f}ms "
    f"p99={report['latencies']['99th'] / 1_000_000:.3f}ms"
)
PY

printf 'Load complete; waiting for the %ss CPU recording to finish.\n' "$profile_duration"
wait "$profiler_pid"
profiler_pid=""

"$python" docs/profiling/report_cpu.py "$profile" --top 30 | tee "$cpu_report"
printf '\nRaw CPU profile: %s\nCPU report:      %s\n' "$profile" "$cpu_report"
