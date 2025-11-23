"""Input handling for keyboard and joystick."""

import pygame
import time
import signal
import sys
import threading
from blessed import Terminal
from typing import Optional, Tuple
from enum import Enum


class InputType(Enum):
    """Types of input events."""
    NONE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    SELECT = 5
    BACK = 6
    QUIT = 7


# Global registry for signal handler cleanup
_input_handler_instances = []
_signal_handlers_registered = False
_cleanup_lock = threading.Lock()


def _signal_handler(signum, frame):
    """Handle SIGINT and SIGTERM for clean joystick shutdown.

    This prevents USB device lockup by ensuring pygame joystick resources
    are properly released when the program is interrupted.
    """
    with _cleanup_lock:
        for handler in _input_handler_instances:
            try:
                handler._emergency_cleanup()
            except Exception:
                pass  # Ignore cleanup errors during emergency shutdown

    # Exit cleanly
    sys.exit(0)


class InputHandler:
    """Handles keyboard and joystick input."""

    def __init__(self):
        global _signal_handlers_registered

        self.term = Terminal()
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.joystick_initialized = False
        self.previous_buttons = {}
        self._reconnection_frame_counter = 0
        self._last_reconnection_message_time = 0
        self._joystick_healthy = True
        self._last_health_check = 0

        # Register this instance for signal handler cleanup
        with _cleanup_lock:
            _input_handler_instances.append(self)

            # Register signal handlers once globally
            if not _signal_handlers_registered:
                signal.signal(signal.SIGINT, _signal_handler)
                signal.signal(signal.SIGTERM, _signal_handler)
                _signal_handlers_registered = True

        self._init_joystick()

    def _init_joystick(self, silent: bool = False):
        """Initialize joystick if available.

        Args:
            silent: If True, suppress status messages (for reconnection attempts)
        """
        try:
            pygame.init()
            pygame.joystick.init()

            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                self.joystick_initialized = True

                if not silent:
                    print(f"Joystick detected: {self.joystick.get_name()}")

                # Let joystick state settle and initialize button tracking
                time.sleep(0.1)
                pygame.event.pump()
                for i in range(self.joystick.get_numbuttons()):
                    self.previous_buttons[i] = self.joystick.get_button(i)
            else:
                if not silent:
                    print("No joystick detected. Using keyboard only.")
        except Exception as e:
            if not silent:
                print(f"Failed to initialize joystick: {e}")
            self.joystick_initialized = False

    def _check_joystick_health(self) -> bool:
        """Check if joystick device is healthy and responsive.

        Performs periodic health checks to detect USB device issues before
        they cause system lockup. Returns True if healthy, False otherwise.
        """
        if not self.joystick_initialized or not self.joystick:
            return False

        # Only check health every 1 second to avoid performance impact
        current_time = time.time()
        if current_time - self._last_health_check < 1.0:
            return self._joystick_healthy

        self._last_health_check = current_time

        try:
            # Test basic device operations with timeout protection
            # If the device is unresponsive, these will fail
            _ = self.joystick.get_numaxes()
            _ = self.joystick.get_numbuttons()

            self._joystick_healthy = True
            return True

        except (pygame.error, OSError, IOError) as e:
            # Device is unhealthy - mark for reconnection
            self._joystick_healthy = False
            self.joystick_initialized = False

            try:
                self.joystick.quit()
            except Exception:
                pass

            self.joystick = None
            return False

    def _attempt_joystick_reconnection(self):
        """Attempt to reconnect joystick if disconnected (e.g., after WSL USB passthrough loss).

        This method is called periodically when the joystick is not initialized.
        It attempts reconnection approximately once per second (every 30 frames at 30 FPS).
        """
        if self.joystick_initialized:
            return  # Already connected

        self._reconnection_frame_counter += 1

        # Try reconnection every 30 frames (~1 second at 30 FPS)
        if self._reconnection_frame_counter % 30 == 0:
            try:
                # Clean up any previous joystick state
                if self.joystick:
                    try:
                        self.joystick.quit()
                    except:
                        pass
                    self.joystick = None

                # Reinitialize pygame joystick subsystem
                pygame.joystick.quit()
                pygame.joystick.init()

                # Check if joystick is now available
                if pygame.joystick.get_count() > 0:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self.joystick_initialized = True
                    self._joystick_healthy = True

                    # Show reconnection message (throttled to once per 5 seconds)
                    current_time = time.time()
                    if current_time - self._last_reconnection_message_time > 5:
                        print(f"\n✓ Joystick reconnected: {self.joystick.get_name()}")
                        self._last_reconnection_message_time = current_time

                    # Initialize button tracking
                    time.sleep(0.1)
                    pygame.event.pump()
                    self.previous_buttons = {}
                    for i in range(self.joystick.get_numbuttons()):
                        self.previous_buttons[i] = self.joystick.get_button(i)

            except Exception:
                # Silent failure - will try again in 30 frames
                pass

    def get_joystick_state(self) -> Tuple[float, float]:
        """Get joystick axis state (x, y) normalized to -1.0 to 1.0.

        Includes health checks and timeout protection to prevent USB device lockup.
        """
        # Health check before device access
        if not self._check_joystick_health():
            return (0.0, 0.0)

        try:
            pygame.event.pump()
            x = self.joystick.get_axis(0) if self.joystick.get_numaxes() > 0 else 0.0
            y = self.joystick.get_axis(1) if self.joystick.get_numaxes() > 1 else 0.0

            # Apply deadzone
            deadzone = 0.15
            x = x if abs(x) > deadzone else 0.0
            y = y if abs(y) > deadzone else 0.0

            return (x, y)

        except (pygame.error, OSError, IOError) as e:
            # Device access failed - mark unhealthy
            self._joystick_healthy = False
            self.joystick_initialized = False
            return (0.0, 0.0)

    def get_joystick_buttons(self) -> dict:
        """Get state of all joystick buttons.

        Includes health checks and timeout protection to prevent USB device lockup.
        """
        # Health check before device access
        if not self._check_joystick_health():
            return {}

        try:
            pygame.event.pump()
            buttons = {}
            for i in range(self.joystick.get_numbuttons()):
                buttons[i] = self.joystick.get_button(i)
            return buttons

        except (pygame.error, OSError, IOError) as e:
            # Device access failed - mark unhealthy
            self._joystick_healthy = False
            self.joystick_initialized = False
            return {}

    def get_input(self, timeout: float = 0.1) -> InputType:
        """Get input from keyboard or joystick."""
        # Attempt joystick reconnection if disconnected
        self._attempt_joystick_reconnection()

        # Check keyboard input
        with self.term.cbreak():
            key = self.term.inkey(timeout=timeout)

            if key:
                if key.name == 'KEY_UP' or key.lower() == 'w':
                    return InputType.UP
                elif key.name == 'KEY_DOWN' or key.lower() == 's':
                    return InputType.DOWN
                elif key.name == 'KEY_LEFT' or key.lower() == 'a':
                    return InputType.LEFT
                elif key.name == 'KEY_RIGHT' or key.lower() == 'd':
                    return InputType.RIGHT
                elif key.name == 'KEY_ENTER' or key == ' ':
                    return InputType.SELECT
                elif key.name == 'KEY_ESCAPE' or key.lower() == 'q':
                    return InputType.BACK
                elif key.lower() == 'x':
                    return InputType.QUIT

        # Check joystick input
        if self.joystick_initialized:
            pygame.event.pump()
            x, y = self.get_joystick_state()

            # Convert axis to digital input
            threshold = 0.5
            if y < -threshold:
                return InputType.UP
            elif y > threshold:
                return InputType.DOWN
            elif x < -threshold:
                return InputType.LEFT
            elif x > threshold:
                return InputType.RIGHT

            # Check buttons - only trigger on new press, not held
            buttons = self.get_joystick_buttons()

            # Detect button press (transition from not pressed to pressed)
            for btn_id, is_pressed in buttons.items():
                was_pressed = self.previous_buttons.get(btn_id, False)

                if is_pressed and not was_pressed:  # New press
                    self.previous_buttons = buttons.copy()

                    if btn_id == 0:  # Button 0 (usually A/Cross)
                        return InputType.SELECT
                    elif btn_id == 1:  # Button 1 (usually B/Circle)
                        return InputType.BACK

            # Update previous button state
            self.previous_buttons = buttons.copy()

        return InputType.NONE

    def verify_joystick(self) -> dict:
        """Return joystick information for verification."""
        info = {
            'connected': self.joystick_initialized,
            'name': self.joystick.get_name() if self.joystick_initialized else None,
            'axes': self.joystick.get_numaxes() if self.joystick_initialized else 0,
            'buttons': self.joystick.get_numbuttons() if self.joystick_initialized else 0,
        }
        return info

    def _emergency_cleanup(self):
        """Emergency cleanup for signal handler.

        Quickly releases USB joystick resources to prevent device lockup.
        Called from signal handler during Ctrl+C or SIGTERM.
        """
        if self.joystick:
            try:
                self.joystick.quit()
            except Exception:
                pass
            self.joystick = None

        try:
            pygame.joystick.quit()
        except Exception:
            pass

        self.joystick_initialized = False

    def cleanup(self):
        """Clean up joystick resources properly.

        Ensures USB device is released cleanly to prevent system lockup.
        Safe to call even if joystick was never initialized.
        """
        with _cleanup_lock:
            # Remove from global registry
            if self in _input_handler_instances:
                _input_handler_instances.remove(self)

            # Clean up joystick
            if self.joystick:
                try:
                    self.joystick.quit()
                except Exception:
                    pass
                self.joystick = None

            # Quit joystick subsystem if no other handlers exist
            if not _input_handler_instances:
                try:
                    pygame.joystick.quit()
                except Exception:
                    pass

            self.joystick_initialized = False
            self._joystick_healthy = False
