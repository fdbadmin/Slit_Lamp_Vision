#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# DEPRECATED - Use pi_setup.sh instead
# =============================================================================
#
# This script is kept for backwards compatibility only.
# For new installations, use:
#
#   ./scripts/pi_setup.sh
#
# Or deploy from your Mac with:
#
#   PI_HOST=vision.local ./scripts/deploy_rsync.sh --setup
#
# =============================================================================

echo ""
echo "⚠️  DEPRECATED: This script is outdated."
echo ""
echo "Please use the new setup script instead:"
echo ""
echo "  ./scripts/pi_setup.sh"
echo ""
echo "This provides:"
echo "  • Complete one-command setup"
echo "  • Automatic service installation"
echo "  • USB automount configuration"
echo "  • Verification checks"
echo ""
read -p "Continue with legacy bootstrap anyway? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Run: ./scripts/pi_setup.sh"
    exit 0
fi

echo ""
echo "Running legacy bootstrap..."
echo ""

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

echo ""
echo "Legacy bootstrap complete."
echo ""
echo "⚠️  Note: Services NOT installed. Run ./scripts/pi_setup.sh for full setup."