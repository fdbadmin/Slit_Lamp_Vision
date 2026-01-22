from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from . import __version__
from .camera import camera_sanity_check, record_h264
from .gpio_io import DEFAULT_BUTTON_PIN, wait_for_button_presses
from .storage import choose_usb_target, find_usb_mount_targets

# Default subdirectory for recordings on USB
RECORDINGS_SUBDIR = "slitlamp_recordings"


def _cmd_usb_status(_: argparse.Namespace) -> int:
    targets = find_usb_mount_targets()
    if not targets:
        print("No writable USB mount targets found.")
        return 1

    print("Writable USB targets:")
    for t in targets:
        meta = []
        if t.label:
            meta.append(f"label={t.label}")
        if t.fstype:
            meta.append(f"fstype={t.fstype}")
        if t.device:
            meta.append(f"dev={t.device}")
        suffix = f" ({', '.join(meta)})" if meta else ""
        print(f"- {t.mountpoint}{suffix}")
    return 0


def _cmd_camera_check(_: argparse.Namespace) -> int:
    try:
        cmd = camera_sanity_check()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"{cmd} is available.")
    return 0


def _cmd_gpio_check(args: argparse.Namespace) -> int:
    try:
        count = wait_for_button_presses(args.pin, seconds=args.seconds, pull_up=not args.pull_down)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Observed {count} button press(es) in {args.seconds}s on GPIO{args.pin}.")
    return 0


def _cmd_record_test(args: argparse.Namespace) -> int:
    target = choose_usb_target()
    if target is None:
        print(
            "No writable USB drive mounted. Recording is disabled until a USB drive is mounted.",
            file=sys.stderr,
        )
        return 2

    try:
        camera_sanity_check()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(target.mountpoint) / f"test_{stamp}.h264"

    print(f"Recording {args.seconds}s to: {out}")
    try:
        record_h264(out, duration_s=args.seconds)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Done.")
    return 0


def _cmd_record_service(args: argparse.Namespace) -> int:
    """Run the button-controlled recording service."""
    from . import recorder

    target = choose_usb_target()
    if target is None:
        print(
            "No writable USB drive mounted. Recording service requires a USB drive.",
            file=sys.stderr,
        )
        return 2

    try:
        camera_sanity_check()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    output_dir = Path(target.mountpoint) / RECORDINGS_SUBDIR

    print(f"Starting recording service...")
    print(f"  GPIO pin: {args.pin}")
    print(f"  Output: {output_dir}")
    print(f"  Press Ctrl+C to stop\n")

    return recorder.run(
        output_dir=output_dir,
        gpio_pin=args.pin,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slitcam", description="Slit lamp camera CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="cmd", required=True)

    usb = sub.add_parser("usb-status", help="List writable USB recording targets")
    usb.set_defaults(func=_cmd_usb_status)

    cam = sub.add_parser("camera-check", help="Verify libcamera tooling is available")
    cam.set_defaults(func=_cmd_camera_check)

    gpio = sub.add_parser("gpio-check", help="Listen for button presses")
    gpio.add_argument("--pin", type=int, default=17, help="GPIO pin number (BCM numbering)")
    gpio.add_argument("--seconds", type=int, default=10, help="How long to listen")
    gpio.add_argument(
        "--pull-down",
        action="store_true",
        help="Use pull-down instead of pull-up (default: pull-up)",
    )
    gpio.set_defaults(func=_cmd_gpio_check)

    rec = sub.add_parser("record-test", help="Record a short test video to USB")
    rec.add_argument("--seconds", type=int, default=10, help="Recording duration")
    rec.set_defaults(func=_cmd_record_test)

    svc = sub.add_parser(
        "record-service",
        help="Run button-controlled recording service (latching button)",
    )
    svc.add_argument(
        "--pin",
        type=int,
        default=DEFAULT_BUTTON_PIN,
        help=f"GPIO pin number for button (BCM numbering, default: {DEFAULT_BUTTON_PIN})",
    )
    svc.set_defaults(func=_cmd_record_service)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
