from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UsbTarget:
    mountpoint: Path
    device: str | None = None
    fstype: str | None = None
    label: str | None = None


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".slitcam_write_test"
        with probe.open("w", encoding="utf-8") as f:
            f.write("ok")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def _run_lsblk_json() -> dict:
    cmd = [
        "lsblk",
        "-J",
        "-o",
        "NAME,KNAME,PATH,TRAN,RM,HOTPLUG,MOUNTPOINT,FSTYPE,LABEL,SIZE",
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(proc.stdout)


def _flatten_lsblk(tree: dict) -> list[dict]:
    out: list[dict] = []

    def walk(node: dict) -> None:
        out.append(node)
        for child in node.get("children") or []:
            walk(child)

    for dev in tree.get("blockdevices") or []:
        walk(dev)
    return out


def find_usb_mount_targets(
    recordings_dir_name: str = "slitlamp-recordings",
    prefer_label_prefixes: tuple[str, ...] = ("SLITLAMP", "SLITLAMP_"),
) -> list[UsbTarget]:
    """Return candidate writable mount targets for removable/USB storage.

    Strategy:
    - Use `lsblk -J` to identify mounted partitions that look removable (RM/HOTPLUG) or USB (TRAN=usb).
    - Filter to writable mountpoints.
    - Candidate path is <mountpoint>/<recordings_dir_name>.
    """

    # Allow test override for macOS dev.
    override = os.environ.get("SLITCAM_STORAGE_DIR")
    if override:
        p = Path(override).expanduser()
        return [UsbTarget(mountpoint=p / recordings_dir_name, device=None, fstype=None, label=None)]

    try:
        tree = _run_lsblk_json()
    except Exception:
        return []

    nodes = _flatten_lsblk(tree)
    candidates: list[UsbTarget] = []
    for n in nodes:
        mountpoint = n.get("mountpoint")
        if not mountpoint:
            continue

        tran = (n.get("tran") or "").lower()
        rm = n.get("rm")
        # Handle both bool and int from lsblk JSON
        is_removable = rm is True or rm == 1 or str(rm).lower() == "true"
        
        # Only accept USB transport or removable media
        # Exclude mmc (SD card) to avoid writing to boot partition
        is_usbish = tran == "usb" or (is_removable and tran != "mmc")
        if not is_usbish:
            continue

        mp = Path(mountpoint)
        # Avoid writing to system paths
        if mp == Path("/"):
            continue
        if str(mp).startswith("/boot"):
            continue

        target = mp / recordings_dir_name
        if _is_writable_dir(target):
            candidates.append(
                UsbTarget(
                    mountpoint=target,
                    device=n.get("path") or n.get("kname"),
                    fstype=n.get("fstype"),
                    label=n.get("label"),
                )
            )

    def score(t: UsbTarget) -> tuple[int, str, str]:
        label = (t.label or "").upper()
        preferred = 1 if any(label.startswith(p) for p in prefer_label_prefixes) else 0
        # We cannot reliably get mount time from lsblk; fall back to stable sort.
        return (preferred, label, str(t.mountpoint))

    candidates.sort(key=score, reverse=True)
    return candidates


def choose_usb_target() -> UsbTarget | None:
    targets = find_usb_mount_targets()
    return targets[0] if targets else None
