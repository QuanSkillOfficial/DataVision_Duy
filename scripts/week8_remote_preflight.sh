#!/usr/bin/env bash
set -euo pipefail

staging_path="${1:?staging path is required}"
backend_port="${2:?backend port is required}"
ui_port="${3:?UI port is required}"

fail() {
  printf 'PREFLIGHT_FAIL code=%s\n' "$1" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || fail docker_missing
docker info >/dev/null 2>&1 || fail docker_unavailable
docker compose version >/dev/null 2>&1 || fail compose_unavailable
compose_version="$(docker compose version --short 2>/dev/null | sed 's/^v//')"
minimum_compose_version="2.24.0"
if [ "$(printf '%s\n%s\n' "$minimum_compose_version" "$compose_version" | sort -V | head -n 1)" != "$minimum_compose_version" ]; then
  fail compose_version_below_2_24
fi

parent="$staging_path"
while [ ! -e "$parent" ] && [ "$parent" != "/" ]; do
  parent="${parent%/*}"
  [ -n "$parent" ] || parent="/"
done
if [ ! -d "$parent" ] || [ ! -w "$parent" ]; then
  fail staging_path_not_writable
fi

available_kb="$(df -Pk "$parent" 2>/dev/null | awk 'NR==2 {print $4}')"
if [[ ! "$available_kb" =~ ^[0-9]+$ ]]; then
  fail disk_check_unavailable
fi
(( available_kb >= 2097152 )) || fail disk_below_2gb

for host in ghcr.io pkg-containers.githubusercontent.com; do
  getent hosts "$host" >/dev/null 2>&1 || fail "dns_${host//[^a-zA-Z0-9]/_}"
done

if command -v ss >/dev/null 2>&1; then
  for port in "$backend_port" "$ui_port"; do
    if ss -H -ltn "sport = :$port" 2>/dev/null | grep -q .; then
      printf 'PREFLIGHT_NOTICE code=port_in_use port=%s\n' "$port"
    fi
  done
fi

printf 'PREFLIGHT_PASS docker=ready compose=%s disk_kb=%s path_parent=%s\n' \
  "$compose_version" "$available_kb" "$parent"
