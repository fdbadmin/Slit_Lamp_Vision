# Slit Lamp Vision

A Raspberry Pi-based slit lamp camera system with hands-free, button-controlled video recording to USB storage.

## Overview

This project enables ophthalmologists to record slit lamp examinations without touching a computer. Simply:

1. **Boot** the Raspberry Pi (service starts automatically)
2. **Insert** any USB drive (auto-detected and mounted)
3. **Press** the latching button to start recording
4. **Press** again to stop recording (auto-converts to MP4)
5. **Remove** USB and view recordings on any computer

## Hardware

| Component | Specification |
|-----------|---------------|
| Computer | Raspberry Pi Zero 2 W |
| Camera | OV5647 (Pi Camera Module v1.3) |
| Storage | Any FAT32/exFAT USB drive |
| Control | 16mm latching push button on GPIO17 |
| Power | USB-C 5V power supply |

### GPIO Wiring

```
GPIO17 (pin 11) ──── Button terminal 1
GND    (pin 9)  ──── Button terminal 2
```

The button uses internal pull-up resistor. Pressed = LOW, Released = HIGH.

## Software Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Zero 2 W                     │
├─────────────────────────────────────────────────────────────┤
│  systemd                                                     │
│  ├── slitcam-recorder.service (auto-start on boot)          │
│  └── usb-automount.service (triggered by udev)              │
├─────────────────────────────────────────────────────────────┤
│  slit_lamp_camera package                                    │
│  ├── recorder.py    - Main service (RecordingService)       │
│  ├── gpio_io.py     - LatchingButton class                  │
│  ├── camera.py      - rpicam-vid wrapper                    │
│  ├── storage.py     - USB mount detection                   │
│  └── cli.py         - Command-line interface                │
├─────────────────────────────────────────────────────────────┤
│  USB Automount                                               │
│  ├── udev rule      - Detects USB insertion                 │
│  └── usb-mount.sh   - Mounts to /media/usb-<device>         │
│                       Symlinks /media/usb → current mount   │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Raspberry Pi OS Bookworm (64-bit Lite)
- SSH access to the Pi
- Python 3.11+

### Quick Install

```bash
# On your development machine
git clone https://github.com/fdbadmin/Slit_Lamp_Vision.git
cd Slit_Lamp_Vision

# Deploy to Pi (assumes Pi hostname is vision.local)
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='.venv' \
  . admin@vision.local:/home/admin/slit-lamp-camera/

# SSH to Pi and run bootstrap
ssh admin@vision.local
cd /home/admin/slit-lamp-camera
./scripts/pi_bootstrap.sh
```

### Manual Installation (on Pi)

```bash
# Create virtual environment with system site-packages (for lgpio)
python3 -m venv --system-site-packages ~/.venv
source ~/.venv/bin/activate
pip install -e /home/admin/slit-lamp-camera

# Install systemd services
sudo cp scripts/slitcam-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable slitcam-recorder.service

# Install USB automount
sudo cp scripts/usb-mount.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/usb-mount.sh
sudo cp scripts/usb-automount.rules /etc/udev/rules.d/99-usb-automount.rules

cat << 'EOF' | sudo tee /etc/systemd/system/usb-automount.service
[Unit]
Description=USB Automount Service
[Service]
Type=oneshot
ExecStart=/usr/local/bin/usb-mount.sh mount
EOF

sudo systemctl daemon-reload
sudo udevadm control --reload-rules
```

## Usage

### Automatic Operation

After installation, the system runs automatically:

1. Power on the Pi
2. Wait ~35 seconds for boot
3. Insert USB drive (LED activity indicates mounting)
4. Toggle button ON → recording starts
5. Toggle button OFF → recording stops, MP4 created
6. Remove USB drive

### Recording Output

Recordings are saved to:
```
/media/usb/slitlamp_recordings/rec_YYYYMMDD_HHMMSS.mp4
```

### Manual Commands

```bash
# Check service status
systemctl status slitcam-recorder.service

# View service logs
journalctl -u slitcam-recorder.service -f

# Check USB mount
ls -la /media/usb/

# Manual recording test
slitcam record-service  # Ctrl+C to stop

# Camera diagnostic
slitcam camera-check

# USB status
slitcam usb-status
```

## Development

### Local Setup (macOS/Linux)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt

# Test with fake GPIO (no hardware needed)
SLITCAM_FAKE_GPIO=1 python -m slit_lamp_camera record-service
```

### Deploy Changes to Pi

```bash
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='.venv' \
  . admin@vision.local:/home/admin/slit-lamp-camera/

ssh admin@vision.local "sudo systemctl restart slitcam-recorder.service"
```

### Project Structure

```
Slit_Lamp_Vision/
├── src/slit_lamp_camera/
│   ├── __init__.py
│   ├── __main__.py       # Entry point
│   ├── cli.py            # Click-based CLI
│   ├── camera.py         # Camera control (rpicam-vid)
│   ├── gpio_io.py        # GPIO/button handling
│   ├── recorder.py       # Main recording service
│   └── storage.py        # USB detection
├── scripts/
│   ├── slitcam-recorder.service   # systemd unit
│   ├── usb-mount.sh               # USB mount script
│   ├── usb-automount.rules        # udev rules
│   ├── pi_bootstrap.sh            # Initial Pi setup
│   └── deploy_rsync.sh            # Deployment helper
├── requirements/
│   ├── dev.txt           # Development dependencies
│   └── pi.txt            # Pi runtime dependencies
├── Documentation/
│   ├── pi-setup.md       # Pi OS installation
│   ├── deploy.md         # Deployment guide
│   └── phase-1-bringup.md
└── pyproject.toml        # Package configuration
```

## Troubleshooting

### Service won't start

```bash
# Check for errors
journalctl -u slitcam-recorder.service -n 50

# Common issue: No USB mounted
slitcam usb-status

# Common issue: Camera not detected
slitcam camera-check
```

### USB not mounting

```bash
# Check udev logs
journalctl -t usb-mount -n 20

# Check device detection
lsblk

# Manual mount test
sudo /usr/local/bin/usb-mount.sh mount
```

### GPIO permission denied

The service must run as root for GPIO access:
```bash
# Check service is running as root
grep User /etc/systemd/system/slitcam-recorder.service
# Should show: User=root
```

### Camera not found

```bash
# Check camera is detected
rpicam-hello --list-cameras

# If not detected, check ribbon cable connection
# and ensure camera is enabled in raspi-config
```

## Technical Notes

### USB Device Name Changes

Linux assigns device names (sda, sdb, etc.) dynamically. Unplugging and replugging a USB drive may assign a different name. This system handles this by:

1. Mounting each device to `/media/usb-<devicename>` (e.g., `/media/usb-sda1`)
2. Creating a symlink `/media/usb` → current mount
3. Using the symlink in the recording service

### Video Format

- Raw recording: H.264 (`.h264`)
- Final output: MP4 with fast-start (`.mp4`)
- Resolution: Camera default (typically 1080p)
- Conversion: `ffmpeg -c copy` (no re-encoding, instant)

### GPIO Backend

Uses `lgpio` backend via `gpiozero`. The `lgpio` library requires root access or membership in the `gpio` group. For simplicity, the service runs as root.

## License

MIT License - See LICENSE file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on actual hardware
5. Submit a pull request

## Roadmap

- [x] **Phase 1**: Button-controlled recording with USB storage
- [ ] **Phase 2**: LED status indicators
- [ ] **Phase 3**: Web interface for configuration
- [ ] **Phase 4**: Cloud upload option
