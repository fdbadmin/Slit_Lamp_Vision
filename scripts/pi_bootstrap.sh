#!/usr/bin/env bash
set -euo pipefail

# Bootstrap the Raspberry Pi (run ON the Pi).
# Installs system packages + creates a venv + installs pip requirements.
#
# Usage on Pi:
#   cd ~/slit-lamp-camera
#   ./scripts/pi_bootstrap.sh

sudo apt update

# Camera tooling + helpful utilities
sudo apt install -y \
  libcamera-apps \
  python3-gpiozero \
  exfatprogs \
  dosfstools

# Optional NTFS support (uncomment if you want best-effort NTFS write support)
# sudo apt install -y ntfs-3g

# Ensure user 'pi' can access GPIO without sudo (requires re-login to take effect)
if ! groups pi | grep -q '\bgpio\b'; then
  sudo usermod -aG gpio pi
  echo "Added pi to gpio group. Reboot or log out/in for this to take effect."
fi

# Create venv and install Python deps
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/pi.txt

echo "Bootstrap complete."