#!/bin/bash
# =============================================================================
# Slit Lamp Camera - Uninstall Script
# =============================================================================
# Removes all slit lamp camera components from the Raspberry Pi.
#
# Usage:
#   ./scripts/pi_uninstall.sh          # Remove services only
#   ./scripts/pi_uninstall.sh --all    # Remove everything including venv
#
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}→ $1${NC}"; }
log_success() { echo -e "${GREEN}✓ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠ $1${NC}"; }

# =============================================================================
# Uninstall Steps
# =============================================================================

stop_services() {
    log_info "Stopping services..."
    
    if systemctl is-active slitcam-recorder.service &>/dev/null; then
        sudo systemctl stop slitcam-recorder.service
        log_success "Stopped slitcam-recorder.service"
    fi
}

disable_services() {
    log_info "Disabling services..."
    
    if systemctl is-enabled slitcam-recorder.service &>/dev/null; then
        sudo systemctl disable slitcam-recorder.service
        log_success "Disabled slitcam-recorder.service"
    fi
}

remove_systemd_services() {
    log_info "Removing systemd service files..."
    
    local services=(
        "/etc/systemd/system/slitcam-recorder.service"
        "/etc/systemd/system/usb-mount@.service"
    )
    
    for svc in "${services[@]}"; do
        if [[ -f "$svc" ]]; then
            sudo rm "$svc"
            log_success "Removed $svc"
        fi
    done
    
    sudo systemctl daemon-reload
    log_success "Systemd daemon reloaded"
}

remove_udev_rules() {
    log_info "Removing udev rules..."
    
    local rules="/etc/udev/rules.d/99-usb-automount.rules"
    
    if [[ -f "$rules" ]]; then
        sudo rm "$rules"
        sudo udevadm control --reload-rules
        log_success "Removed udev rules"
    fi
}

remove_mount_script() {
    log_info "Removing USB mount script..."
    
    local script="/usr/local/bin/usb-mount.sh"
    
    if [[ -f "$script" ]]; then
        sudo rm "$script"
        log_success "Removed $script"
    fi
}

unmount_usb() {
    log_info "Unmounting USB drives..."
    
    # Unmount any /media/usb-* mounts
    for mnt in /media/usb-*; do
        if [[ -d "$mnt" ]] && mountpoint -q "$mnt" 2>/dev/null; then
            sudo umount -l "$mnt" 2>/dev/null || true
            sudo rmdir "$mnt" 2>/dev/null || true
            log_success "Unmounted $mnt"
        fi
    done
    
    # Remove symlink
    if [[ -L "/media/usb" ]]; then
        sudo rm "/media/usb"
        log_success "Removed /media/usb symlink"
    fi
}

remove_venv() {
    log_info "Removing Python virtual environment..."
    
    if [[ -d "$VENV_DIR" ]]; then
        rm -rf "$VENV_DIR"
        log_success "Removed $VENV_DIR"
    fi
}

remove_project() {
    log_info "Removing project directory..."
    
    if [[ -d "$PROJECT_DIR" ]]; then
        rm -rf "$PROJECT_DIR"
        log_success "Removed $PROJECT_DIR"
    fi
}

# =============================================================================
# Main
# =============================================================================

show_banner() {
    echo ""
    echo "=============================================="
    echo "   Slit Lamp Camera - Uninstall"
    echo "=============================================="
    echo ""
}

main() {
    show_banner
    
    local remove_all=false
    if [[ "$1" == "--all" ]]; then
        remove_all=true
        log_warn "Full removal mode - will remove venv and project files"
        echo ""
        read -p "Are you sure? This cannot be undone. [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cancelled."
            exit 0
        fi
    fi
    
    # Always remove services and config
    stop_services
    disable_services
    unmount_usb
    remove_systemd_services
    remove_udev_rules
    remove_mount_script
    
    # Optionally remove venv and project
    if $remove_all; then
        remove_venv
        echo ""
        log_warn "Project directory NOT removed (you're running from it)"
        log_warn "To fully remove, run: rm -rf $PROJECT_DIR"
    fi
    
    echo ""
    echo "=============================================="
    echo "   Uninstall Complete"
    echo "=============================================="
    echo ""
    echo "  Removed:"
    echo "    • slitcam-recorder.service"
    echo "    • usb-mount@.service"
    echo "    • udev rules"
    echo "    • /usr/local/bin/usb-mount.sh"
    
    if $remove_all; then
        echo "    • Python virtual environment"
    fi
    
    echo ""
    echo "  System packages (libcamera-apps, ffmpeg, etc.) were NOT removed."
    echo "  To remove them: sudo apt remove libcamera-apps ffmpeg python3-gpiozero"
    echo ""
}

main "$@"
