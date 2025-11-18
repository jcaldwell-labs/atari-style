"""Input handling for keyboard and joystick."""

import pygame
import time
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


class InputHandler:
    """Handles keyboard and joystick input."""

    def __init__(self):
        self.term = Terminal()
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.joystick_initialized = False
        self.previous_buttons = {}
        self._reconnection_frame_counter = 0
        self._last_reconnection_message_time = 0
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
        """Get joystick axis state (x, y) normalized to -1.0 to 1.0."""
        if not self.joystick_initialized:
            return (0.0, 0.0)

        pygame.event.pump()
        x = self.joystick.get_axis(0) if self.joystick.get_numaxes() > 0 else 0.0
        y = self.joystick.get_axis(1) if self.joystick.get_numaxes() > 1 else 0.0

        # Apply deadzone
        deadzone = 0.15
        x = x if abs(x) > deadzone else 0.0
        y = y if abs(y) > deadzone else 0.0

        return (x, y)

    def get_joystick_buttons(self) -> dict:
        """Get state of all joystick buttons."""
        if not self.joystick_initialized:
            return {}

        pygame.event.pump()
        buttons = {}
        for i in range(self.joystick.get_numbuttons()):
            buttons[i] = self.joystick.get_button(i)
        return buttons

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

    def cleanup(self):
        """Clean up resources.

        Note: We don't call pygame.quit() here because pygame is shared
        across all demos and the menu. Calling quit() would break joystick
        input when returning to the menu.
        """
        # Don't quit pygame - it's shared across demos
        pass
