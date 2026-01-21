# Phase 1 Context Summary (Completed)

Date range: Jan 2026

## Goal (Phase 1)

Deliver a **hands-off recording workflow** for a Raspberry Pi Zero 2 W slit lamp observer-view camera:

1. Boot Pi (service auto-starts)
2. Insert **any** USB drive
3. Toggle a **latching button** to start recording
4. Toggle again to stop recording and produce MP4
5. Remove USB and view recordings on another computer

## What we built (working end state)

### Button-controlled recording service

- Added a GPIO-backed latching button abstraction that supports:
  - Polling
  - Initial state detection (so ON at boot starts recording immediately)
  - Callbacks on transition

- Implemented a long-running service that:
  - Watches GPIO17
  - Starts `rpicam-vid` recording when the switch is ON
  - Stops recording when OFF
  - Converts recorded `.h264` → `.mp4` without re-encoding

- Exposed the service via CLI and systemd:
  - CLI command to run the service interactively
  - systemd unit to start on boot

### USB automount (robust to device name changes)

The final robust design uses this approach:

- Each insert is mounted to a unique mount point:
  - `/media/usb-sdX1` (example: `/media/usb-sdd1`)
- A stable symlink is updated on each insert:
  - `/media/usb` → `/media/usb-sdX1`
- The recording service always uses `/media/usb/...` so it doesn’t care about Linux device renames.

This removes the core failure mode where the kernel assigns different block names on each plug cycle (`sda1`, `sdb1`, `sdc1`, ...).

### Git “freeze” for Phase 1

Phase 1 is preserved so later phases can iterate safely:

- Tag: `phase-1.0.0`
- Branch: `phase-1`

## What worked well

- Recording control via a latching button is stable and intuitive.
- `rpicam-vid` works well for Bookworm and produces consistent H.264 output.
- MP4 conversion using stream copy is fast and keeps quality.
- Running the recorder under systemd makes boot behavior reliable.
- The **symlink-based USB mount scheme** made the “any USB, any device name” requirement reliable.

## What failed (and why)

### 1) GPIO access / permissions

Symptoms:
- GPIO libraries failed or produced permission errors.

Root cause:
- The chosen GPIO stack requires access that the default user session didn’t have.

Resolution:
- Run the recorder service as root via systemd.
- Ensure the Python venv is created with `--system-site-packages` so system packages (notably GPIO deps) are usable.

### 2) Camera command mismatch (`libcamera-vid` vs `rpicam-vid`)

Symptoms:
- Recording command not found / not working on Bookworm.

Root cause:
- Newer Raspberry Pi OS uses `rpicam-*` tooling.

Resolution:
- Implemented command selection preferring `rpicam-vid`.

### 3) USB automount reliability (device renames + stale mounts)

Symptoms:
- Automount would sometimes mount the wrong device.
- On repeated unplug/replug, the device name changed (`sda1` → `sdb1` → `sdc1`) and the system ended up with a stale mount.
- `storage.py` reported “No writable USB mount targets found” even though the USB was plugged in.

Root cause:
- Relying on the kernel-assigned name (`/dev/sda1`) is not stable across hotplug cycles.
- Attempting to unmount stale mounts in-place proved unreliable under udev timing and kernel behavior.

Resolutions attempted:
- udev RUN rules running a mount script directly
- aggressive unmount logic
- trying to pass `%k` to scripts

Final resolution:
- Stop fighting the stale-mount problem.
- Mount each new USB partition to a distinct mount point and repoint a stable symlink (`/media/usb`).
- Trigger mount via udev → systemd oneshot service to avoid udev timeouts and ensure the script runs fully.

### 4) udev timeout / backgrounding behavior

Symptoms:
- Mount script sometimes didn’t finish when triggered indirectly.

Root cause:
- Early versions backgrounded the work to avoid udev timeouts; when triggered via systemd oneshot, backgrounding caused the service to exit before the mount completed.

Resolution:
- For the systemd-triggered path, removed backgrounding so the oneshot service waits for completion.

### 5) “Fix” that killed SSH

Symptoms:
- SSH disconnected and the Pi stopped responding.

Root cause:
- A too-aggressive cleanup (`fuser -km /media/usb`) killed processes including the active SSH session.

Resolution:
- Removed that approach and avoided using process-killing as part of the mount path.
- Power-cycled the Pi to recover.

## Final acceptance test (pass)

- Boot Pi → service is active
- Insert USB → mounted at `/media/usb-sdX1` and symlink `/media/usb` points to it
- Toggle button ON → recording starts
- Toggle button OFF → recording stops and MP4 is produced on USB
- Unplug USB and replug → device name changes but symlink updates correctly and workflow continues

## Useful references in repo

- Phase 1 guide: Documentation/phases/phase-1.md
- Main README: README.md
- Recorder service unit: scripts/slitcam-recorder.service
- USB automount pieces:
  - scripts/usb-automount.rules
  - scripts/usb-mount.sh

## Next-phase suggestions (Phase 2)

- Add LED indicators (idle / recording / error / USB missing)
- Add explicit “safe to remove USB” behavior (sync + status)
- Add healthcheck command that validates camera + GPIO + USB end-to-end
