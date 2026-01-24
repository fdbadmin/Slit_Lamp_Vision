#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Deploy Slit Lamp Camera to Raspberry Pi
# =============================================================================
# Syncs code to Pi and optionally runs full setup.
#
# Usage:
#   PI_HOST=vision.local ./scripts/deploy_rsync.sh           # Sync only
#   PI_HOST=vision.local ./scripts/deploy_rsync.sh --setup   # Sync + full setup
#
# Environment:
#   PI_HOST  - Required. Hostname or IP (e.g., vision.local)
#   PI_USER  - Optional. Default: admin
#   PI_DIR   - Optional. Default: /home/$PI_USER/slit-lamp-camera
# =============================================================================

PI_HOST="${PI_HOST:-}"
PI_USER="${PI_USER:-admin}"
PI_DIR="${PI_DIR:-/home/$PI_USER/slit-lamp-camera}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

show_usage() {
    echo "Usage: PI_HOST=<hostname> $0 [--setup]"
    echo ""
    echo "Options:"
    echo "  --setup    Run full setup after sync (installs services, etc.)"
    echo ""
    echo "Environment:"
    echo "  PI_HOST    Required. Pi hostname (e.g., vision.local)"
    echo "  PI_USER    Optional. Default: admin"
    echo "  PI_DIR     Optional. Default: /home/\$PI_USER/slit-lamp-camera"
}

if [[ -z "$PI_HOST" ]]; then
    echo "ERROR: PI_HOST not set"
    echo ""
    show_usage
    exit 2
fi

# Parse arguments
RUN_SETUP=false
for arg in "$@"; do
    case $arg in
        --setup)
            RUN_SETUP=true
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
    esac
done

echo -e "${BLUE}Deploying to ${PI_USER}@${PI_HOST}:${PI_DIR}${NC}"
echo ""

# Sync files
rsync -az --delete \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.ruff_cache' \
    --exclude 'setup.log' \
    ./ "${PI_USER}@${PI_HOST}:${PI_DIR}/"

echo -e "${GREEN}✓ Code synced${NC}"

# Optionally run setup
if $RUN_SETUP; then
    echo ""
    echo -e "${BLUE}Running setup on Pi...${NC}"
    echo ""
    ssh -t "${PI_USER}@${PI_HOST}" "cd ${PI_DIR} && chmod +x scripts/pi_setup.sh && ./scripts/pi_setup.sh"
else
    echo ""
    echo "To run full setup on Pi:"
    echo "  ssh ${PI_USER}@${PI_HOST}"
    echo "  cd ${PI_DIR}"
    echo "  ./scripts/pi_setup.sh"
fi
