# Raspberry Pi Setup Guide

Complete setup guide for the Slit Lamp Camera system on Raspberry Pi.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Hardware Requirements](#hardware-requirements)
3. [Flashing the SD Card](#flashing-the-sd-card)
4. [One-Command Setup](#one-command-setup)
5. [Manual Setup](#manual-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Uninstall](#uninstall)

---

## Quick Start

**TL;DR** - If you just want to get up and running:

```bash
# From your Mac/Linux machine
git clone https://github.com/fdbadmin/Slit_Lamp_Vision.git
cd Slit_Lamp_Vision
PI_HOST=vision.local ./scripts/deploy_rsync.sh --setup
```

That's it! The script handles everything. Read on for details.

---

## Hardware Requirements

| Component | Specification | Notes |
|-----------|---------------|-------|
| Raspberry Pi | Pi Zero 2 W (recommended) | Pi 3/4/5 also work |
| Camera | OV5647 or IMX219 | Pi Camera Module v1.3 or v2 |
| SD Card | 8GB+ microSD | Class 10 or better |
| USB Drive | Any FAT32/exFAT drive | For recording storage |
| Button | 16mm latching push button | Connected to GPIO17 |
| Power | 5V 2.5A USB-C | Good quality PSU recommended |

### GPIO Wiring

```
Raspberry Pi                  Button
───────────────────────────────────────
GPIO17 (pin 11) ────────────── Terminal 1
GND    (pin 9)  ────────────── Terminal 2
```

The button uses internal pull-up resistor:
- **Pressed (latched ON)** = GPIO reads LOW → Recording
- **Released (latched OFF)** = GPIO reads HIGH → Stopped

---

## Flashing the SD Card

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)

2. Select OS: **Raspberry Pi OS Lite (64-bit)** (Bookworm or newer)

3. Click the **gear icon** (⚙️) to configure:

   | Setting | Recommended Value |
   |---------|-------------------|
   | Hostname | `vision` (or your preferred name) |
   | Enable SSH | ✅ Yes |
   | Username | `admin` |
   | Password | Your choice |
   | Wi-Fi SSID | Your network |
   | Wi-Fi Password | Your password |
   | Wi-Fi Country | Your country code |
   | Locale | Your timezone |

4. Flash the SD card

5. Insert SD card into Pi and power on

6. Wait 2-3 minutes for first boot, then verify SSH:
   ```bash
   ssh admin@vision.local
   ```

---

## One-Command Setup

From your development machine (Mac/Linux):

```bash
# Clone the repository (if not already done)
git clone https://github.com/fdbadmin/Slit_Lamp_Vision.git
cd Slit_Lamp_Vision

# Deploy and configure everything
PI_HOST=vision.local ./scripts/deploy_rsync.sh --setup
```

### What the setup script does:

1. **Installs system packages:**
   - `libcamera-apps` - Camera tools (rpicam-vid)
   - `python3-gpiozero` - GPIO library
   - `python3-lgpio` - Low-level GPIO
   - `ffmpeg` - Video conversion
   - `exfatprogs`, `dosfstools` - USB filesystem support

2. **Configures user permissions:**
   - Adds user to `gpio` group

3. **Creates Python environment:**
   - Virtual environment with `--system-site-packages`
   - Installs `slit-lamp-camera` package
   - Creates `slitcam` CLI tool

4. **Installs services:**
   - `slitcam-recorder.service` - Main recording service
   - `usb-mount@.service` - USB automount template

5. **Configures USB automount:**
   - Installs `/usr/local/bin/usb-mount.sh`
   - Installs udev rules to `/etc/udev/rules.d/`

6. **Runs verification:**
   - Tests camera detection
   - Tests GPIO access
   - Tests CLI functionality

### After setup:

- **Reboot if prompted** (required for GPIO group membership)
- Insert a USB drive
- Press the button to start recording
- Press again to stop and save MP4

---

## Manual Setup

If you prefer to run steps individually:

### 1. Deploy code to Pi

```bash
PI_HOST=vision.local ./scripts/deploy_rsync.sh
```

### 2. SSH to Pi and run setup

```bash
ssh admin@vision.local
cd ~/slit-lamp-camera
./scripts/pi_setup.sh
```

### 3. Reboot (if needed)

```bash
sudo reboot
```

---

## Verification

### Check service status

```bash
sudo systemctl status slitcam-recorder.service
```

### Check USB mount

```bash
# Insert USB drive, then:
ls -la /media/usb/
```

### Test camera

```bash
rpicam-hello --list-cameras
```

### Test GPIO

```bash
/home/admin/slit-lamp-camera/.venv/bin/slitcam gpio-check --pin 17 --seconds 10
```

### View logs

```bash
# Service logs
sudo journalctl -u slitcam-recorder.service -f

# USB mount logs
sudo journalctl -t usb-mount -f
```

---

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u slitcam-recorder.service -n 50 --no-pager

# Common issues:
# - No USB drive inserted
# - Camera not detected
# - GPIO permission denied (reboot needed)
```

### USB not mounting

```bash
# Check udev rules
cat /etc/udev/rules.d/99-usb-automount.rules

# Manually trigger mount
sudo /usr/local/bin/usb-mount.sh mount

# Check mount logs
sudo journalctl -t usb-mount --since "5 minutes ago"
```

### Camera not detected

```bash
# Check camera connection
rpicam-hello --list-cameras

# Enable camera in config (if needed)
sudo raspi-config
# → Interface Options → Camera → Enable
```

### GPIO permission denied

```bash
# Check group membership
groups

# Should include 'gpio'. If not:
sudo usermod -aG gpio $USER
sudo reboot
```

### Re-run setup

The setup script is idempotent - safe to run multiple times:

```bash
./scripts/pi_setup.sh
```

---

## Uninstall

### Remove services only

```bash
./scripts/pi_uninstall.sh
```

This removes:
- Systemd services
- Udev rules
- Mount script

### Complete removal

```bash
./scripts/pi_uninstall.sh --all
```

This also removes the Python virtual environment.

To fully remove the project:

```bash
./scripts/pi_uninstall.sh --all
cd ~
rm -rf ~/slit-lamp-camera
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PI_HOST` | (required) | Pi hostname (e.g., `vision.local`) |
| `PI_USER` | `admin` | SSH username |
| `PI_DIR` | `/home/$PI_USER/slit-lamp-camera` | Install directory |

---

## File Locations (on Pi)

| File | Location |
|------|----------|
| Project code | `/home/admin/slit-lamp-camera/` |
| Python venv | `/home/admin/slit-lamp-camera/.venv/` |
| CLI tool | `/home/admin/slit-lamp-camera/.venv/bin/slitcam` |
| Recorder service | `/etc/systemd/system/slitcam-recorder.service` |
| USB mount service | `/etc/systemd/system/usb-mount@.service` |
| Mount script | `/usr/local/bin/usb-mount.sh` |
| Udev rules | `/etc/udev/rules.d/99-usb-automount.rules` |
| USB mount point | `/media/usb` → `/media/usb-<device>` |
| Recordings | `/media/usb/slitlamp_recordings/` |
| Setup log | `/home/admin/slit-lamp-camera/setup.log` |
