# Phase 1 – Hardware Bring-Up

From the project plan (acceptance): **record a 10-second test video and save it to USB storage**.

## Wiring (button)

- Use BCM numbering.
- Default pin in the CLI: GPIO17.
- Recommended simple wiring for pull-up (default):
  - Button between **GPIO17** and **GND**.

## Bring-up checklist

1) Confirm the Pi is headless and reachable

```bash
ssh pi@slitlamp.local
```

2) Install OS dependencies

Follow Documentation/pi-setup.md, then bootstrap:

```bash
cd ~/slit-lamp-camera
./scripts/pi_bootstrap.sh
```

3) Verify USB detection (no USB => failure is expected)

```bash
. .venv/bin/activate
slitcam usb-status
```

4) Verify camera tooling

```bash
slitcam camera-check
```

5) Verify button presses

Press the button a few times while it listens:

```bash
slitcam gpio-check --pin 17 --seconds 10
```

6) Phase 1 acceptance test: record 10 seconds to USB

Insert a USB drive (exFAT/FAT32). Then:

```bash
slitcam record-test --seconds 10
```

Expected outcome:
- A file `test_YYYYmmdd_HHMMSS.h264` exists under `<USB_MOUNT>/slitlamp_recordings/`.

## Notes

- Recording is intentionally disabled until a writable USB target is detected.
- If multiple USB drives are mounted, the selection prefers drives with labels beginning with `SLITLAMP`.
