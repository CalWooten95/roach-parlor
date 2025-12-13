#!/usr/bin/env bash

set -euo pipefail

STATE_FILE="${1:-}"
if [[ -z "$STATE_FILE" || ! -f "$STATE_FILE" ]]; then
  echo "[preview] no state file provided for cleanup" >&2
  exit 1
fi

source "$STATE_FILE"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export COMPOSE_PROJECT_NAME="$PROJECT_NAME"
export WEB_PORT="${WEB_PORT:-8000}"
export DB_PORT="${DB_PORT:-5432}"

pushd "$REPO_ROOT" >/dev/null
echo "[preview] tearing down compose project $PROJECT_NAME"
docker compose down -v --remove-orphans >/dev/null 2>&1 || true
popd >/dev/null

if [[ -n "${CLOUDFLARED_PID:-}" ]]; then
  if kill -0 "$CLOUDFLARED_PID" >/dev/null 2>&1; then
    echo "[preview] stopping cloudflared process $CLOUDFLARED_PID"
    kill "$CLOUDFLARED_PID" >/dev/null 2>&1 || true
  fi
fi

rm -f "$STATE_FILE"
