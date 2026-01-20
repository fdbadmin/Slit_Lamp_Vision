from __future__ import annotations

import os
import time
from typing import Callable

# Default GPIO pin for the latching button
DEFAULT_BUTTON_PIN = 17


class LatchingButton:
    """A latching (maintained) button that tracks ON/OFF state.

    Calls on_pressed when button transitions to ON (pressed).
    Calls on_released when button transitions to OFF (released).

    Supports SLITCAM_FAKE_GPIO=1 env var for desktop testing.
    """

    def __init__(
        self,
        gpio_pin: int = DEFAULT_BUTTON_PIN,
        pull_up: bool = True,
        bounce_time: float = 0.05,
        on_pressed: Callable[[], None] | None = None,
        on_released: Callable[[], None] | None = None,
    ) -> None:
        self.gpio_pin = gpio_pin
        self.pull_up = pull_up
        self.bounce_time = bounce_time
        self.on_pressed = on_pressed
        self.on_released = on_released

        self._fake_mode = os.environ.get("SLITCAM_FAKE_GPIO") == "1"
        self._button = None
        self._last_state: bool | None = None

        if not self._fake_mode:
            try:
                from gpiozero import Button  # type: ignore

                self._button = Button(gpio_pin, pull_up=pull_up, bounce_time=bounce_time)
            except Exception as exc:
                raise RuntimeError(
                    "gpiozero not available. Install on the Pi with: sudo apt install python3-gpiozero"
                ) from exc

    @property
    def is_pressed(self) -> bool:
        """Return True if button is currently in the ON (pressed) state."""
        if self._fake_mode:
            return False
        return self._button.is_pressed if self._button else False

    def poll(self) -> None:
        """Check button state and call callbacks if state changed.

        Call this in a loop with a small sleep interval (e.g., 50ms).
        """
        current_state = self.is_pressed

        if self._last_state is None:
            # First poll - just record state, don't trigger callbacks
            self._last_state = current_state
            return

        if current_state != self._last_state:
            self._last_state = current_state
            if current_state and self.on_pressed:
                self.on_pressed()
            elif not current_state and self.on_released:
                self.on_released()

    def check_initial_state(self) -> bool:
        """Check and return initial button state, triggering on_pressed if ON.

        Call this once at startup to handle case where button is already ON.
        Returns True if button was pressed and on_pressed was called.
        """
        current_state = self.is_pressed
        self._last_state = current_state

        if current_state and self.on_pressed:
            self.on_pressed()
            return True
        return False

    def close(self) -> None:
        """Release GPIO resources."""
        if self._button:
            self._button.close()
            self._button = None


def wait_for_button_presses(
    gpio_pin: int,
    seconds: int = 10,
    pull_up: bool = True,
) -> int:
    """Listen for button presses for a fixed window.

    Returns the number of presses observed.

    On macOS dev (or when SLITCAM_FAKE_GPIO=1), this runs in a fake mode.
    """

    if os.environ.get("SLITCAM_FAKE_GPIO") == "1":
        # Simulate: no presses.
        time.sleep(seconds)
        return 0

    try:
        from gpiozero import Button  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "gpiozero not available. Install on the Pi with: sudo apt install python3-gpiozero"
        ) from exc

    presses = 0

    def on_press() -> None:
        nonlocal presses
        presses += 1

    button = Button(gpio_pin, pull_up=pull_up, bounce_time=0.05)
    button.when_pressed = on_press

    # Run a simple timed loop.
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        time.sleep(0.05)

    button.close()
    return presses
