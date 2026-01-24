#!/bin/bash
# =============================================================================
# Slit Lamp Camera - Complete Pi Setup Script
# =============================================================================
# This script configures a fresh Raspberry Pi OS installation with everything
# needed for the slit lamp camera system. It is idempotent - safe to run
# multiple times.
#
# Usage:
#   ./scripts/pi_setup.sh          # Full setup
#   ./scripts/pi_setup.sh --check  # Verify setup without changes
#
# Requirements:
#   - Raspberry Pi OS (Bookworm/Trixie 64-bit recommended)
#   - Internet connection for apt packages
#   - Run as the user who will operate the camera (e.g., admin)
#   - Script must be run from the slit-lamp-camera directory
#
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_FILE="$PROJECT_DIR/setup.log"
CURRENT_USER="$(whoami)"
HOME_DIR="$HOME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

log_success() { log "${GREEN}✓ $1${NC}"; }
log_info() { log "${BLUE}→ $1${NC}"; }
log_warn() { log "${YELLOW}⚠ $1${NC}"; }
log_error() { log "${RED}✗ $1${NC}"; }

# Check if running on Raspberry Pi
check_pi() {
    if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        log_error "This script must be run on a Raspberry Pi"
        exit 1
    fi
    log_success "Running on $(cat /proc/device-tree/model | tr -d '\0')"
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check if user is in group
user_in_group() {
    groups "$CURRENT_USER" 2>/dev/null | grep -qw "$1"
}

# Check if package is installed
package_installed() {
    dpkg -l "$1" 2>/dev/null | grep -q "^ii"
}

# Check if systemd service exists
service_exists() {
    [[ -f "/etc/systemd/system/$1" ]]
}

# =============================================================================
# Setup Steps
# =============================================================================

install_apt_packages() {
    log_info "Checking system packages..."
    
    local packages=(
        "libcamera-apps"    # Camera tools (rpicam-vid, rpicam-hello)
        "python3-gpiozero"  # GPIO library
        "python3-lgpio"     # lgpio backend for gpiozero
        "python3-venv"      # Python virtual environments
        "ffmpeg"            # Video conversion (h264 → mp4)
        "exfatprogs"        # exFAT filesystem support
        "dosfstools"        # FAT32 filesystem support
    )
    
    local to_install=()
    for pkg in "${packages[@]}"; do
        if ! package_installed "$pkg"; then
            to_install+=("$pkg")
        fi
    done
    
    if [[ ${#to_install[@]} -eq 0 ]]; then
        log_success "All system packages already installed"
    else
        log_info "Installing: ${to_install[*]}"
        sudo apt-get update
        sudo apt-get install -y "${to_install[@]}"
        log_success "System packages installed"
    fi
}

setup_gpio_group() {
    log_info "Checking GPIO group membership..."
    
    if user_in_group "gpio"; then
        log_success "User '$CURRENT_USER' already in gpio group"
    else
        log_info "Adding user '$CURRENT_USER' to gpio group..."
        sudo usermod -aG gpio "$CURRENT_USER"
        log_success "Added to gpio group (reboot required)"
        NEEDS_REBOOT=true
    fi
}

setup_python_venv() {
    log_info "Checking Python virtual environment..."
    
    if [[ -d "$VENV_DIR" ]] && [[ -f "$VENV_DIR/bin/python" ]]; then
        log_success "Virtual environment exists at $VENV_DIR"
    else
        log_info "Creating virtual environment with system-site-packages..."
        python3 -m venv --system-site-packages "$VENV_DIR"
        log_success "Virtual environment created"
    fi
    
    # Always upgrade pip and install/update the package
    log_info "Installing slit-lamp-camera package..."
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -e "$PROJECT_DIR" -q
    log_success "Package installed: $("$VENV_DIR/bin/slitcam" --version 2>/dev/null || echo 'slitcam')"
}

install_mount_script() {
    log_info "Installing USB mount script..."
    
    local src="$PROJECT_DIR/scripts/usb-mount.sh"
    local dst="/usr/local/bin/usb-mount.sh"
    
    if [[ ! -f "$src" ]]; then
        log_error "Source script not found: $src"
        exit 1
    fi
    
    sudo cp "$src" "$dst"
    sudo chmod +x "$dst"
    log_success "Installed $dst"
}

install_systemd_services() {
    log_info "Installing systemd services..."
    
    # Generate slitcam-recorder.service with correct paths
    local service_file="/etc/systemd/system/slitcam-recorder.service"
    
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=SlitCam Button-Controlled Recording Service
Documentation=https://github.com/fdbadmin/Slit_Lamp_Vision
After=local-fs.target

[Service]
Type=simple
User=root
ExecStartPre=/bin/sleep 2
ExecStart=$VENV_DIR/bin/slitcam record-service
Restart=on-failure
RestartSec=5
Environment=HOME=$HOME_DIR

[Install]
WantedBy=multi-user.target
EOF
    log_success "Installed slitcam-recorder.service"
    
    # Install USB mount template service
    local usb_service="/etc/systemd/system/usb-mount@.service"
    sudo cp "$PROJECT_DIR/scripts/usb-mount@.service" "$usb_service"
    log_success "Installed usb-mount@.service"
    
    # Reload systemd
    sudo systemctl daemon-reload
    log_success "Systemd daemon reloaded"
}

install_udev_rules() {
    log_info "Installing udev rules..."
    
    local src="$PROJECT_DIR/scripts/usb-automount.rules"
    local dst="/etc/udev/rules.d/99-usb-automount.rules"
    
    if [[ ! -f "$src" ]]; then
        log_error "Source rules not found: $src"
        exit 1
    fi
    
    sudo cp "$src" "$dst"
    sudo udevadm control --reload-rules
    log_success "Installed udev rules and reloaded"
}

setup_media_directory() {
    log_info "Setting up /media/usb directory..."
    
    if [[ ! -d "/media" ]]; then
        sudo mkdir -p /media
    fi
    
    log_success "/media directory ready"
}

enable_services() {
    log_info "Enabling services..."
    
    if ! systemctl is-enabled slitcam-recorder.service &>/dev/null; then
        sudo systemctl enable slitcam-recorder.service
        log_success "Enabled slitcam-recorder.service"
    else
        log_success "slitcam-recorder.service already enabled"
    fi
}

# =============================================================================
# Verification
# =============================================================================

verify_camera() {
    log_info "Verifying camera..."
    
    if command_exists rpicam-hello; then
        if timeout 5 rpicam-hello --list-cameras 2>&1 | grep -q "Available cameras"; then
            log_success "Camera detected"
            return 0
        else
            log_warn "Camera command exists but no camera detected"
            log_warn "Check camera connection and enable in raspi-config"
            return 1
        fi
    else
        log_warn "rpicam-hello not found"
        return 1
    fi
}

verify_gpio() {
    log_info "Verifying GPIO access..."
    
    if "$VENV_DIR/bin/python" -c "from gpiozero import Button; print('GPIO OK')" 2>/dev/null; then
        log_success "GPIO access working"
        return 0
    else
        log_warn "GPIO access failed (may need reboot for group membership)"
        return 1
    fi
}

verify_slitcam() {
    log_info "Verifying slitcam CLI..."
    
    if "$VENV_DIR/bin/slitcam" --help &>/dev/null; then
        log_success "slitcam CLI working"
        return 0
    else
        log_error "slitcam CLI not working"
        return 1
    fi
}

run_verification() {
    log_info "Running verification checks..."
    echo ""
    
    local all_ok=true
    
    verify_slitcam || all_ok=false
    verify_camera || all_ok=false
    verify_gpio || all_ok=false
    
    echo ""
    if $all_ok; then
        log_success "All verification checks passed!"
    else
        log_warn "Some checks failed - review warnings above"
    fi
}

# =============================================================================
# Main
# =============================================================================

show_banner() {
    echo ""
    echo "=============================================="
    echo "   Slit Lamp Camera - Pi Setup"
    echo "=============================================="
    echo ""
}

show_summary() {
    echo ""
    echo "=============================================="
    echo "   Setup Complete!"
    echo "=============================================="
    echo ""
    echo "  Project:  $PROJECT_DIR"
    echo "  Venv:     $VENV_DIR"
    echo "  Log:      $LOG_FILE"
    echo ""
    echo "  Services:"
    echo "    • slitcam-recorder.service (enabled)"
    echo "    • usb-mount@.service (template)"
    echo ""
    echo "  Usage:"
    echo "    1. Insert USB drive"
    echo "    2. Service auto-starts"
    echo "    3. Press button to record"
    echo "    4. Release button to stop + save MP4"
    echo ""
    
    if [[ "$NEEDS_REBOOT" == "true" ]]; then
        echo "  ${YELLOW}⚠ REBOOT REQUIRED for GPIO group membership${NC}"
        echo ""
        read -p "  Reboot now? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Rebooting..."
            sudo reboot
        else
            echo "  Run 'sudo reboot' when ready."
        fi
    else
        echo "  System is ready! Insert a USB drive to start."
    fi
    echo ""
}

main() {
    NEEDS_REBOOT=false
    
    show_banner
    
    # Initialize log
    echo "" >> "$LOG_FILE"
    log "========== Setup started =========="
    
    # Pre-flight checks
    check_pi
    
    if [[ ! -f "$PROJECT_DIR/pyproject.toml" ]]; then
        log_error "Must run from slit-lamp-camera project directory"
        log_error "Expected: $PROJECT_DIR/pyproject.toml"
        exit 1
    fi
    
    # Check for --check flag
    if [[ "$1" == "--check" ]]; then
        log_info "Check mode - no changes will be made"
        run_verification
        exit 0
    fi
    
    # Run setup steps
    install_apt_packages
    setup_gpio_group
    setup_python_venv
    install_mount_script
    install_systemd_services
    install_udev_rules
    setup_media_directory
    enable_services
    
    # Verify
    run_verification
    
    # Done
    log "========== Setup completed =========="
    show_summary
}

main "$@"
