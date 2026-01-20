# End-to-end workflow (macOS → Raspberry Pi Zero 2 W)

This project is developed on macOS and deployed to a Raspberry Pi Zero 2 W running **Raspberry Pi OS Lite 64-bit** (Bookworm) via SSH.

## Principles

- The Pi runs headless.
- The app runs as user `pi`.
- **No USB mounted => no recording.**
- Prefer OS packages (`apt`) for hardware-adjacent dependencies.

## High-level pipeline

1. macOS: edit code + run static checks.
2. macOS: `rsync` code to Pi.
3. Pi: install OS dependencies + create venv.
4. Pi: run Phase 1 bring-up commands.
5. Pi: once Phase 2 starts, install/enable a systemd service.

## Commands

### 1) Sync code to the Pi

```bash
PI_HOST=slitlamp.local ./scripts/deploy_rsync.sh
```

### 2) Bootstrap the Pi (first time)

SSH into the Pi, then:

```bash
cd ~/slit-lamp-camera
./scripts/pi_bootstrap.sh
```

### 3) Update deps after code changes (later)

```bash
cd ~/slit-lamp-camera
./scripts/pi_update.sh
```

### 4) Phase 1 acceptance test

```bash
cd ~/slit-lamp-camera
. .venv/bin/activate
slitcam usb-status
slitcam camera-check
slitcam record-test --seconds 10
```
