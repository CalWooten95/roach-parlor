#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$REPO_ROOT/ai_context/preview"
mkdir -p "$STATE_DIR"

PROJECT_NAME="${PREVIEW_PROJECT_NAME:-preview-${RANDOM}}"
BRANCH_NAME="${PREVIEW_BRANCH:-}"

if [[ -z "$BRANCH_NAME" ]]; then
  echo "[preview] PREVIEW_BRANCH not provided" >&2
  exit 1
fi

random_port() {
  python3 - <<'PY'
import socket
s = socket.socket()
s.bind(('', 0))
port = s.getsockname()[1]
s.close()
print(port)
PY
}

WEB_PORT="${PREVIEW_WEB_PORT:-$(random_port)}"
DB_PORT="${PREVIEW_DB_PORT:-$(random_port)}"
while [[ "$DB_PORT" == "$WEB_PORT" ]]; do
  DB_PORT="$(random_port)"
done

export COMPOSE_PROJECT_NAME="$PROJECT_NAME"
export WEB_PORT
export DB_PORT

pushd "$REPO_ROOT" >/dev/null

echo "[preview] bringing up compose project $PROJECT_NAME (web port $WEB_PORT, db port $DB_PORT)"
docker compose down --remove-orphans >/dev/null 2>&1 || true
docker compose up -d --build

LOG_FILE="$STATE_DIR/${PROJECT_NAME}_cloudflared.log"
touch "$LOG_FILE"

echo "[preview] starting cloudflared tunnel"
nohup cloudflared tunnel --no-autoupdate --url "http://localhost:${WEB_PORT}" >"$LOG_FILE" 2>&1 &
TUNNEL_PID=$!
disown "$TUNNEL_PID" || true

TUNNEL_URL=""
for _ in {1..30}; do
  if [[ -s "$LOG_FILE" ]]; then
    MATCH="$(grep -Eo 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' "$LOG_FILE" | tail -n 1 || true)"
    if [[ -n "$MATCH" ]]; then
      TUNNEL_URL="$MATCH"
      break
    fi
  fi
  sleep 1
done

if [[ -z "$TUNNEL_URL" ]]; then
  echo "[preview] failed to obtain Cloudflare tunnel URL" >&2
  exit 1
fi

STATE_FILE="$STATE_DIR/${PROJECT_NAME}.env"
cat >"$STATE_FILE" <<EOF
PROJECT_NAME=$PROJECT_NAME
WEB_PORT=$WEB_PORT
DB_PORT=$DB_PORT
CLOUDFLARED_PID=$TUNNEL_PID
LOG_FILE=$LOG_FILE
BRANCH_NAME=$BRANCH_NAME
EOF

popd >/dev/null

echo "[preview] tunnel ready at $TUNNEL_URL"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "preview_state_file=$STATE_FILE"
    echo "tunnel_url=$TUNNEL_URL"
    echo "project_name=$PROJECT_NAME"
  } >>"$GITHUB_OUTPUT"
fi
