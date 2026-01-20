#!/usr/bin/env bash
set -euo pipefail

# Sync this repo to the Raspberry Pi over SSH.
# Usage:
#   PI_HOST=slitlamp.local ./scripts/deploy_rsync.sh

PI_HOST="${PI_HOST:-}"
PI_USER="${PI_USER:-pi}"
PI_DIR="${PI_DIR:-/home/pi/slit-lamp-camera}"

if [[ -z "$PI_HOST" ]]; then
  echo "ERROR: Set PI_HOST (e.g., PI_HOST=slitlamp.local)" >&2
  exit 2
fi

rsync -az --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  ./ "${PI_USER}@${PI_HOST}:${PI_DIR}/"

echo "Synced to ${PI_USER}@${PI_HOST}:${PI_DIR}"