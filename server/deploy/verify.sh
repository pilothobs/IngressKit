#!/usr/bin/env bash
set -euo pipefail

# Verification script for IngressKit deployment
# Tests local and remote endpoints

PORT="${PORT:-8080}"
REMOTE_HOST="${REMOTE_HOST:-api.ingresskit.com}"

echo "=== IngressKit Deployment Verification ==="
echo

# Test local
echo "Testing local server (127.0.0.1:${PORT})..."
if curl -sS -f "http://127.0.0.1:${PORT}/v1/ping" >/dev/null 2>&1; then
    PING_RESULT=$(curl -sS "http://127.0.0.1:${PORT}/v1/ping" | jq -r '.message' 2>/dev/null || echo "unknown")
    echo "✓ Local /v1/ping: ${PING_RESULT}"
else
    echo "✗ Local /v1/ping: failed"
fi

if curl -sS -f "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
    echo "✓ Local /: OK"
else
    echo "✗ Local /: failed"
fi

echo

# Test remote
echo "Testing remote server (${REMOTE_HOST})..."
if curl -sS -f "https://${REMOTE_HOST}/v1/ping" >/dev/null 2>&1; then
    REMOTE_PING=$(curl -sS "https://${REMOTE_HOST}/v1/ping" | jq -r '.message' 2>/dev/null || echo "unknown")
    echo "✓ Remote /v1/ping: ${REMOTE_PING}"
else
    echo "✗ Remote /v1/ping: failed"
fi

if curl -sS -f "https://${REMOTE_HOST}/" >/dev/null 2>&1; then
    echo "✓ Remote /: OK"
else
    echo "✗ Remote /: failed"
fi

echo

# Check systemd service
echo "Service status:"
if systemctl is-active --quiet ingresskit 2>/dev/null; then
    echo "✓ ingresskit service: running"
    systemctl --no-pager status ingresskit | grep -E '(Active:|Main PID:|Memory:)'
else
    echo "✗ ingresskit service: not running"
fi

echo
echo "Verification complete."
