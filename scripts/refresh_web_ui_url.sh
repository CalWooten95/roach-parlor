#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="cloudflared"
SLEEP_SECONDS=${SLEEP_SECONDS:-5}
LOG_LOOKBACK="10 minutes ago"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing .env file at ${ENV_FILE}" >&2
  exit 1
fi

restart_service() {
  echo "Restarting systemd service: ${SERVICE_NAME}" >&2
  sudo systemctl restart "${SERVICE_NAME}"
}

fetch_tunnel_url() {
  echo "Waiting ${SLEEP_SECONDS}s for tunnel to establish" >&2
  sleep "${SLEEP_SECONDS}"

  echo "Reading journal for fresh tunnel URL" >&2
  journalctl -u "${SERVICE_NAME}" --since "${LOG_LOOKBACK}" |
    grep -Eo 'https://[A-Za-z0-9-]+\\.trycloudflare\\.com' |
    tail -n 1
}

update_env_file() {
  local url="$1"
  python3 - "$ENV_FILE" "$url" <<'PYCODE'
import pathlib
import sys

env_path = pathlib.Path(sys.argv[1])
url = sys.argv[2]
lines = env_path.read_text().splitlines()

for i, line in enumerate(lines):
    if line.startswith("WEB_UI_URL="):
        lines[i] = f"WEB_UI_URL={url}"
        break
else:
    lines.append(f"WEB_UI_URL={url}")

env_path.write_text("\n".join(lines) + "\n")
PYCODE
}

restart_service

TUNNEL_URL=$(fetch_tunnel_url)
if [[ -z "${TUNNEL_URL}" ]]; then
  echo "Unable to locate tunnel URL in journal" >&2
  exit 1
fi

echo "Found tunnel URL: ${TUNNEL_URL}" >&2

echo "Updating WEB_UI_URL in ${ENV_FILE}" >&2
update_env_file "${TUNNEL_URL}"

echo "Recycling Docker Compose stack" >&2
docker compose down
docker compose up -d

echo "Refresh complete. WEB_UI_URL=${TUNNEL_URL}" >&2
