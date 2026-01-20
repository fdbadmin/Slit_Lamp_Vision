#!/usr/bin/env bash
set -euo pipefail

# Update the Pi after syncing code (run ON the Pi).
# Usage:
#   cd ~/slit-lamp-camera
#   ./scripts/pi_update.sh

if [[ ! -d .venv ]]; then
  echo "ERROR: .venv not found. Run ./scripts/pi_bootstrap.sh first." >&2
  exit 2
fi

. .venv/bin/activate
python -m pip install -r requirements/pi.txt

echo "Updated Python deps."