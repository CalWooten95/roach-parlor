#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-roach-parlor-smoke}"

cleanup() {
  echo "[smoke] tearing down compose stack"
  docker compose down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[smoke] compiling python sources"
python3 -m compileall bot web/app >/dev/null

echo "[smoke] starting docker compose stack"
docker compose up -d --build

echo "[smoke] waiting for FastAPI health endpoint"
attempt=0
until curl -fsS "http://localhost:8000/health" >/tmp/health-check.json; do
  attempt=$((attempt + 1))
  if [[ $attempt -ge 30 ]]; then
    echo "[smoke] FastAPI health endpoint did not become ready in time"
    exit 1
  fi
  sleep 2
done
cat /tmp/health-check.json

echo "[smoke] stack healthy"
