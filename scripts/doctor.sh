#!/bin/sh

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

failed=0

check() {
  label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "doctor: OK    $label"
  else
    echo "doctor: FAIL  $label" >&2
    failed=1
  fi
}

check "Docker CLI" docker version
check "Docker Compose" docker compose version
check "OpenSSL" openssl version
check "Node.js" node --version
check "npm" npm --version
check "environment" sh scripts/validate_env.sh
check "Compose configuration" docker compose config --quiet

if docker compose ps --format '{{.Service}} {{.Health}} {{.State}}' >/tmp/aquaguard-doctor-ps.$$ 2>/dev/null; then
  if [ -s /tmp/aquaguard-doctor-ps.$$ ]; then
    sed 's/^/doctor: INFO  /' /tmp/aquaguard-doctor-ps.$$
  else
    echo "doctor: INFO  stack is not running"
  fi
  rm -f /tmp/aquaguard-doctor-ps.$$
else
  echo "doctor: FAIL  cannot query Docker Compose services" >&2
  failed=1
fi

[ "$failed" -eq 0 ] || exit 1
echo "doctor: OK    environment is ready"
