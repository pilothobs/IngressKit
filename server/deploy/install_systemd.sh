#!/usr/bin/env bash
set -euo pipefail

# This script installs the IngressKit FastAPI server under systemd using uvicorn.
# Run on the target host. Requires sudo privileges.

APP_ROOT_DEFAULT="/opt/ingresskit"
APP_DIR_DEFAULT="${APP_ROOT_DEFAULT}/server"
VENV_DIR_DEFAULT="${APP_ROOT_DEFAULT}/venv"
SERVICE_NAME="ingresskit"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_DIR="/etc/ingresskit"
ENV_FILE="${ENV_DIR}/server.env"

# Configurable via env vars
APP_DIR="${APP_DIR:-${APP_DIR_DEFAULT}}"
VENV_DIR="${VENV_DIR:-${VENV_DIR_DEFAULT}}"
PORT="${PORT:-8080}"
SVC_USER="${SVC_USER:-www-data}"

echo "Installing IngressKit server as systemd service '${SERVICE_NAME}'"
echo "App dir: ${APP_DIR}"
echo "Venv dir: ${VENV_DIR}"
echo "Run user: ${SVC_USER}"
echo "Port: ${PORT}"

# Ensure directories
sudo mkdir -p "${APP_DIR}"
sudo mkdir -p "${VENV_DIR}"
sudo mkdir -p "${ENV_DIR}"

# Sync code
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
echo "Syncing server code from ${SRC_DIR} -> ${APP_DIR}"
sudo rsync -a --delete "${SRC_DIR}/" "${APP_DIR}/"

# Create venv and install deps
if [ ! -x "${VENV_DIR}/bin/python" ]; then
  echo "Creating venv at ${VENV_DIR}"
  sudo python3 -m venv "${VENV_DIR}"
fi

echo "Installing requirements"
sudo "${VENV_DIR}/bin/pip" install --upgrade pip
sudo "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

# Create default env file if missing
if [ ! -f "${ENV_FILE}" ]; then
  echo "Creating ${ENV_FILE}"
  sudo bash -c "cat > '${ENV_FILE}' <<EOF
# Example environment overrides
# STRIPE_SECRET_KEY=sk_live_xxx
# STRIPE_WEBHOOK_SECRET=whsec_xxx
# INGRESSKIT_ADMIN_TOKEN=replace_me
# INGRESSKIT_API_KEYS=demo:1000
# INGRESSKIT_PRICE_MAP=price_123:5000
# INGRESSKIT_PRICE_ALIASES=small:price_123
EOF"
fi

# Write systemd unit
echo "Writing ${SERVICE_FILE}"
sudo bash -c "cat > '${SERVICE_FILE}' <<UNIT
[Unit]
Description=IngressKit FastAPI Server
After=network.target

[Service]
Type=simple
User=${SVC_USER}
WorkingDirectory=${APP_DIR}
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-${ENV_FILE}
ExecStart=${VENV_DIR}/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT"

echo "Reloading systemd and enabling service"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"
sleep 1
sudo systemctl --no-pager status "${SERVICE_NAME}" | sed -n '1,80p'

echo
echo "Done. If you have a reverse proxy, ensure it forwards to 127.0.0.1:${PORT}."
echo "Example check: curl -sS http://127.0.0.1:${PORT}/v1/ping"


