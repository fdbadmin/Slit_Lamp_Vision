"""Button-controlled video recording service.

This module implements the main recording service that:
- Monitors a latching button for ON/OFF state changes
- Starts recording when button is pressed (ON)
- Stops recording and converts to MP4 when button is released (OFF)
- Handles graceful shutdown on SIGTERM/SIGINT
"""
from __future__ import annotations

import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from .camera import convert_to_mp4, start_recording, stop_recording
from .gpio_io import DEFAULT_BUTTON_PIN, LatchingButton

# Polling interval in seconds
POLL_INTERVAL = 0.05  # 50ms


class RecordingService:
    """Main recording service that ties button events to camera control."""

    def __init__(
        self,
        output_dir: Path,
        gpio_pin: int = DEFAULT_BUTTON_PIN,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the recording service.

        Args:
            output_dir: Directory to save recordings
            gpio_pin: GPIO pin for the latching button (BCM numbering)
            on_status: Optional callback for status messages (default: print)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._status = on_status or print
        self._running = False
        self._proc: subprocess.Popen | None = None
        self._current_h264: Path | None = None

        # Set up button with callbacks
        self._button = LatchingButton(
            gpio_pin=gpio_pin,
            on_pressed=self._on_button_pressed,
            on_released=self._on_button_released,
        )

    def _on_button_pressed(self) -> None:
        """Called when button transitions to ON - start recording."""
        if self._proc is not None and self._proc.poll() is None:
            self._status("Already recording, ignoring press")
            return

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_h264 = self.output_dir / f"rec_{timestamp}.h264"

        self._status(f"START -> {self._current_h264}")
        try:
            self._proc = start_recording(self._current_h264)
        except Exception as exc:
            self._status(f"ERROR starting recording: {exc}")
            self._proc = None
            self._current_h264 = None

    def _on_button_released(self) -> None:
        """Called when button transitions to OFF - stop recording and convert."""
        if self._proc is None or self._proc.poll() is not None:
            self._status("Not recording, ignoring release")
            return

        self._status("STOP...")
        try:
            stop_recording(self._proc)
        except Exception as exc:
            self._status(f"ERROR stopping recording: {exc}")
        finally:
            self._proc = None

        # Convert to MP4
        if self._current_h264 and self._current_h264.exists():
            mp4_path = self._current_h264.with_suffix(".mp4")
            self._status(f"MP4 -> {mp4_path}")
            try:
                convert_to_mp4(self._current_h264, delete_h264=False)
            except Exception as exc:
                self._status(f"ERROR converting to MP4: {exc}")
        self._current_h264 = None

    def _handle_shutdown(self, signum: int, frame) -> None:
        """Handle SIGTERM/SIGINT for graceful shutdown."""
        sig_name = signal.Signals(signum).name
        self._status(f"\nReceived {sig_name}, shutting down...")
        self._running = False

    def run(self) -> int:
        """Run the recording service main loop.

        Returns:
            Exit code (0 for success)
        """
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        self._status("Ready. Latching switch: ON=start, OFF=stop+mp4")
        self._status(f"Output directory: {self.output_dir}")

        # Check initial button state - start recording if already ON
        if self._button.check_initial_state():
            self._status("Button was ON at startup, recording started")

        self._running = True
        try:
            while self._running:
                self._button.poll()
                time.sleep(POLL_INTERVAL)
        finally:
            # Clean up: stop any active recording
            if self._proc is not None and self._proc.poll() is None:
                self._status("Stopping active recording...")
                self._on_button_released()

            self._button.close()
            self._status("Service stopped.")

        return 0


def run(
    output_dir: Path,
    gpio_pin: int = DEFAULT_BUTTON_PIN,
    on_status: Callable[[str], None] | None = None,
) -> int:
    """Convenience function to create and run the recording service.

    Args:
        output_dir: Directory to save recordings
        gpio_pin: GPIO pin for the latching button (BCM numbering)
        on_status: Optional callback for status messages

    Returns:
        Exit code (0 for success)
    """
    service = RecordingService(
        output_dir=output_dir,
        gpio_pin=gpio_pin,
        on_status=on_status,
    )
    return service.run()
