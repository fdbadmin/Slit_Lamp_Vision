from __future__ import annotations

import signal
import shutil
import subprocess
import os
import shlex
from pathlib import Path

# Default recording parameters
DEFAULT_FPS = 25


def have_libcamera_vid() -> bool:
    return shutil.which("libcamera-vid") is not None


def have_rpicam_vid() -> bool:
    """Check for rpicam-vid (newer Raspberry Pi OS Bookworm tool)."""
    return shutil.which("rpicam-vid") is not None


def get_camera_command() -> str:
    """Return the available camera recording command."""
    if have_rpicam_vid():
        return "rpicam-vid"
    if have_libcamera_vid():
        return "libcamera-vid"
    raise RuntimeError(
        "No camera tool found. Install rpicam-apps or libcamera-apps via apt on the Pi."
    )


def get_extra_camera_args() -> list[str]:
    """Optional extra args passed through to rpicam-vid/libcamera-vid.

    This is useful for tuning Camera Module 3 settings (e.g. autofocus, resolution)
    without changing code.

    Example:
        SLITCAM_CAMERA_ARGS='--autofocus-mode continuous --width 1920 --height 1080'
    """
    raw = os.environ.get("SLITCAM_CAMERA_ARGS", "").strip()
    if not raw:
        return []
    return shlex.split(raw)


def start_recording(
    output_path: Path,
    framerate: int = DEFAULT_FPS,
) -> subprocess.Popen:
    """Start indefinite H.264 recording, returning the subprocess handle.

    Recording continues until stop_recording() is called.
    Uses rpicam-vid (preferred) or libcamera-vid with -t 0 for indefinite recording.

    Args:
        output_path: Path to write the .h264 file
        framerate: Frames per second (default 25)

    Returns:
        subprocess.Popen handle - pass this to stop_recording() to stop
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = get_camera_command()
    args = [
        cmd,
        "-t", "0",  # Indefinite recording
        "--codec", "h264",
        "--framerate", str(framerate),
        "--inline",  # Include SPS/PPS headers for easier conversion
        "--nopreview",
        "-o", str(output_path),
    ]

    args += get_extra_camera_args()

    proc = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    return proc


def stop_recording(proc: subprocess.Popen, timeout: float = 5.0) -> None:
    """Stop a recording subprocess gracefully.

    Sends SIGINT first (graceful stop), then SIGTERM if timeout expires.

    Args:
        proc: The subprocess.Popen handle from start_recording()
        timeout: Seconds to wait for graceful shutdown before forcing
    """
    if proc is None or proc.poll() is not None:
        return  # Already stopped

    # Send SIGINT for graceful stop (allows rpicam-vid to finalize file)
    proc.send_signal(signal.SIGINT)

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        # Force terminate if graceful stop didn't work
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def convert_to_mp4(h264_path: Path, delete_h264: bool = False) -> Path:
    """Convert H.264 file to MP4 using ffmpeg fast remux.

    Uses -c copy for fast conversion (no re-encoding).

    Args:
        h264_path: Path to the .h264 file
        delete_h264: If True, delete the .h264 file after successful conversion

    Returns:
        Path to the created .mp4 file
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found. Install via: sudo apt install ffmpeg")

    mp4_path = h264_path.with_suffix(".mp4")

    # Fast remux: -c copy means no re-encoding
    # -fflags +genpts generates presentation timestamps
    subprocess.run(
        [
            "ffmpeg",
            "-y",  # Overwrite output
            "-fflags", "+genpts",
            "-r", str(DEFAULT_FPS),
            "-i", str(h264_path),
            "-c", "copy",
            str(mp4_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        check=True,
    )

    # Sync to ensure data is written to USB
    subprocess.run(["sync"], check=False)

    if delete_h264 and mp4_path.exists():
        h264_path.unlink()

    return mp4_path


def record_h264(
    output_path: Path,
    duration_s: int = 10,
    width: int | None = None,
    height: int | None = None,
    framerate: int | None = None,
) -> None:
    """Record an H.264 stream to output_path using libcamera-vid.

    Notes:
    - This produces a .h264 elementary stream by default.
    - Later phases can convert to .mp4 via ffmpeg if desired.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use newer rpicam-vid if available, fall back to libcamera-vid
    try:
        cmd_name = get_camera_command()
    except RuntimeError:
        raise RuntimeError("No camera tool found. Install rpicam-apps or libcamera-apps via apt on the Pi.")

    cmd: list[str] = [
        cmd_name,
        "-t",
        str(int(duration_s * 1000)),
        "-o",
        str(output_path),
    ]

    cmd += get_extra_camera_args()

    if width is not None:
        cmd += ["--width", str(width)]
    if height is not None:
        cmd += ["--height", str(height)]
    if framerate is not None:
        cmd += ["--framerate", str(framerate)]

    subprocess.run(cmd, check=True)


def camera_sanity_check() -> str:
    """Verify that a camera recording tool is available.

    Returns:
        The selected camera command (e.g. "rpicam-vid" or "libcamera-vid").
    """
    try:
        return get_camera_command()
    except RuntimeError:
        raise RuntimeError(
            "No camera tool found (rpicam-vid or libcamera-vid). "
            "On Raspberry Pi OS, install: sudo apt install rpicam-apps"
        )
