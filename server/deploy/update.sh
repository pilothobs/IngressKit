#!/usr/bin/env bash
set -euo pipefail

# Quick update script for existing systemd installation
# Run this when you have code changes to deploy

APP_DIR="${APP_DIR:-/opt/ingresskit/server}"
VENV_DIR="${VENV_DIR:-/opt/ingresskit/venv}"
SERVICE_NAME="ingresskit"

echo "Updating IngressKit server deployment..."

# Sync latest code
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
echo "Syncing code from ${SRC_DIR} -> ${APP_DIR}"
sudo rsync -a --delete "${SRC_DIR}/" "${APP_DIR}/"

# Update dependencies
echo "Updating requirements"
sudo "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

# Restart service
echo "Restarting ${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"
sleep 2

# Check status
echo "Service status:"
sudo systemctl --no-pager status "${SERVICE_NAME}" | sed -n '1,15p'

echo
echo "Update complete. Test with:"
echo "curl -sS http://127.0.0.1:8080/v1/ping"
