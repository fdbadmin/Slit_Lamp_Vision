# Phase 1 — Button-controlled recording to USB

## What Phase 1 delivers

A fully headless workflow on Raspberry Pi Zero 2 W:

- Auto-starts on boot (`slitcam-recorder.service`)
- Detects and mounts *any* USB drive when inserted
- Latching button (GPIO17) toggles recording on/off
- Stops recording and produces an MP4 on button-off
- User can pull the USB and view recordings on a computer

## “Freeze” Phase 1 so we can iterate safely

Phase 1 is intended to be a stable baseline that later phases build on. We preserve it in git using:

- A **tag**: `phase-1.0.0`
- A **branch**: `phase-1` (points at the tag)

This keeps the Phase 1 code easy to find and reproducible, while `main` continues forward.

## Key files for Phase 1

- Runtime package: `src/slit_lamp_camera/`
  - `recorder.py` — main service wiring button → camera
  - `gpio_io.py` — `LatchingButton` implementation
  - `camera.py` — `rpicam-vid` start/stop + MP4 conversion
  - `storage.py` — finds current writable USB mount

- Services and automount:
  - `scripts/slitcam-recorder.service` — systemd unit (runs as root for GPIO)
  - `scripts/usb-automount.rules` — udev rule triggering automount
  - `scripts/usb-mount.sh` — mounts to `/media/usb-<partition>` and updates `/media/usb` symlink

- Bring-up guides:
  - `Documentation/pi-setup.md`
  - `Documentation/deploy.md`
  - `Documentation/phase-1-bringup.md`

## Output location

Recordings are written under:

- `/media/usb/slitlamp_recordings/`

(Where `/media/usb` is a symlink to the currently inserted drive’s mountpoint.)
