#!/bin/sh

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

command -v docker >/dev/null 2>&1 || { echo "setup: Docker is required" >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "setup: Docker Compose v2 is required" >&2; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "setup: OpenSSL is required" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "setup: Node.js is required" >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "setup: npm is required" >&2; exit 1; }

make env
make certs
make config-check

echo "setup: OK    run 'make demo' for the complete stack or 'make dev' for Vite HMR"
