"""Joystick Visualizer - Visual debugging tool for joystick input.

Displays real-time joystick state including:
- Analog stick position with radial direction line
- Button states with gamepad-style layout (A/B/X/Y/L/R)
- Axis values and deadzone visualization
"""

import time
import math
from ...engine.renderer import Renderer, Color
from ...engine.input_handler import InputHandler


# Button name mapping for common gamepad layouts
BUTTON_NAMES = {
    0: 'A',
    1: 'B',
    2: 'X',
    3: 'Y',
    4: 'LB',
    5: 'RB',
    6: 'Back',
    7: 'Start',
    8: 'LS',
    9: 'RS',
    10: 'LT',
    11: 'RT',
}


class JoystickViz:
    """Visual joystick state debugger."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True
        self.deadzone = 0.1

    def draw_stick(self, cx: int, cy: int, x: float, y: float, label: str):
        """Draw analog stick visualization.

        Args:
            cx, cy: Center position
            x, y: Stick values (-1 to 1)
            label: Stick label (e.g., "LEFT STICK")
        """
        radius = 12

        # Draw outer circle
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            px = int(cx + math.cos(rad) * radius)
            py = int(cy + math.sin(rad) * (radius // 2))
            if 0 <= px < self.renderer.width and 0 <= py < self.renderer.height:
                self.renderer.set_pixel(px, py, '·', Color.DARK_GRAY)

        # Draw crosshair axes
        for i in range(-radius, radius + 1):
            if 0 <= cx + i < self.renderer.width:
                self.renderer.set_pixel(cx + i, cy, '─', Color.DARK_GRAY)
            if 0 <= cy + i // 2 < self.renderer.height:
                self.renderer.set_pixel(cx, cy + i // 2, '│', Color.DARK_GRAY)

        # Draw center
        self.renderer.set_pixel(cx, cy, '┼', Color.YELLOW)

        # Draw deadzone circle
        dz_radius = int(radius * self.deadzone)
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            px = int(cx + math.cos(rad) * dz_radius)
            py = int(cy + math.sin(rad) * (dz_radius // 2))
            if 0 <= px < self.renderer.width and 0 <= py < self.renderer.height:
                self.renderer.set_pixel(px, py, '░', Color.RED)

        # Calculate stick position
        pos_x = int(cx + x * radius)
        pos_y = int(cy + y * (radius // 2))

        # Draw direction line from center to stick position
        magnitude = math.sqrt(x * x + y * y)
        if magnitude > self.deadzone:
            steps = int(magnitude * 15)
            for i in range(1, steps):
                t = i / steps
                lx = int(cx + x * radius * t)
                ly = int(cy + y * (radius // 2) * t)
                if 0 <= lx < self.renderer.width and 0 <= ly < self.renderer.height:
                    self.renderer.set_pixel(lx, ly, '·', Color.GREEN)

        # Draw stick position
        if 0 <= pos_x < self.renderer.width and 0 <= pos_y < self.renderer.height:
            color = Color.BRIGHT_GREEN if magnitude > self.deadzone else Color.BRIGHT_RED
            self.renderer.set_pixel(pos_x, pos_y, '●', color)

        # Draw label
        label_x = cx - len(label) // 2
        self.renderer.draw_text(label_x, cy - radius // 2 - 2, label, Color.CYAN)

        # Draw values
        val_text = f"X:{x:+.2f} Y:{y:+.2f}"
        val_x = cx - len(val_text) // 2
        self.renderer.draw_text(val_x, cy + radius // 2 + 2, val_text, Color.YELLOW)

    def draw_button(self, x: int, y: int, name: str, pressed: bool):
        """Draw a single button indicator.

        Args:
            x, y: Position
            name: Button name
            pressed: Whether button is pressed
        """
        if pressed:
            char = '█'
            color = Color.BRIGHT_GREEN
        else:
            char = '○'
            color = Color.WHITE

        # Draw button with name
        text = f"[{char}]{name}"
        self.renderer.draw_text(x, y, text, color)

    def draw_button_panel(self, x: int, y: int, buttons: dict):
        """Draw gamepad-style button layout.

        Args:
            x, y: Top-left position
            buttons: Button states dict
        """
        self.renderer.draw_text(x, y, "BUTTONS", Color.CYAN)

        # Face buttons (diamond layout)
        #       Y
        #     X   B
        #       A
        face_x = x + 8
        face_y = y + 3

        # Y button (top)
        self.draw_button(face_x, face_y, 'Y', buttons.get(3, False))
        # X button (left)
        self.draw_button(face_x - 5, face_y + 1, 'X', buttons.get(2, False))
        # B button (right)
        self.draw_button(face_x + 5, face_y + 1, 'B', buttons.get(1, False))
        # A button (bottom)
        self.draw_button(face_x, face_y + 2, 'A', buttons.get(0, False))

        # Shoulder buttons
        self.draw_button(x, y + 6, 'LB', buttons.get(4, False))
        self.draw_button(x + 12, y + 6, 'RB', buttons.get(5, False))

        # Trigger buttons (if available)
        self.draw_button(x, y + 7, 'LT', buttons.get(10, False))
        self.draw_button(x + 12, y + 7, 'RT', buttons.get(11, False))

        # System buttons
        self.draw_button(x, y + 9, 'Back', buttons.get(6, False))
        self.draw_button(x + 10, y + 9, 'Start', buttons.get(7, False))

        # Stick clicks
        self.draw_button(x, y + 10, 'LS', buttons.get(8, False))
        self.draw_button(x + 10, y + 10, 'RS', buttons.get(9, False))

    def draw_all_buttons_raw(self, x: int, y: int, buttons: dict):
        """Draw raw button state list.

        Args:
            x, y: Top-left position
            buttons: Button states dict
        """
        self.renderer.draw_text(x, y, "RAW BUTTONS", Color.CYAN)

        for i, (btn_id, pressed) in enumerate(sorted(buttons.items())):
            if i >= 16:
                break
            row = i % 8
            col = i // 8
            btn_x = x + col * 12
            btn_y = y + 2 + row

            name = BUTTON_NAMES.get(btn_id, str(btn_id))
            char = '█' if pressed else '○'
            color = Color.BRIGHT_GREEN if pressed else Color.DARK_GRAY
            self.renderer.draw_text(btn_x, btn_y, f"{btn_id}:{char} {name}", color)

    def draw(self):
        """Render the joystick visualization."""
        self.renderer.clear_buffer()

        # Title
        title = "JOYSTICK VISUALIZER"
        self.renderer.draw_text(
            (self.renderer.width - len(title)) // 2, 1,
            title, Color.BRIGHT_CYAN
        )

        # Get joystick info
        info = self.input_handler.verify_joystick()

        if not info['connected']:
            # No joystick message
            msg = "NO JOYSTICK DETECTED"
            self.renderer.draw_text(
                (self.renderer.width - len(msg)) // 2,
                self.renderer.height // 2,
                msg, Color.BRIGHT_RED
            )
            hint = "Connect a joystick and restart"
            self.renderer.draw_text(
                (self.renderer.width - len(hint)) // 2,
                self.renderer.height // 2 + 2,
                hint, Color.YELLOW
            )
        else:
            # Connection info
            status = f"Connected: {info['name']}"
            self.renderer.draw_text(
                (self.renderer.width - len(status)) // 2, 3,
                status, Color.GREEN
            )

            axes_info = f"Axes: {info['axes']}  Buttons: {info['buttons']}"
            self.renderer.draw_text(
                (self.renderer.width - len(axes_info)) // 2, 4,
                axes_info, Color.DARK_GRAY
            )

            # Get current state
            x, y = self.input_handler.get_joystick_state()
            buttons = self.input_handler.get_joystick_buttons()

            # Draw stick visualization (left side)
            stick_cx = self.renderer.width // 4
            stick_cy = self.renderer.height // 2
            self.draw_stick(stick_cx, stick_cy, x, y, "STICK")

            # Draw button panel (center-right)
            panel_x = self.renderer.width // 2 + 5
            panel_y = 7
            self.draw_button_panel(panel_x, panel_y, buttons)

            # Draw raw button list (far right)
            raw_x = self.renderer.width - 25
            raw_y = 7
            self.draw_all_buttons_raw(raw_x, raw_y, buttons)

            # Draw deadzone indicator
            dz_text = f"Deadzone: {self.deadzone:.0%}"
            self.renderer.draw_text(5, self.renderer.height - 6, dz_text, Color.DARK_GRAY)

            # Magnitude
            mag = math.sqrt(x * x + y * y)
            mag_text = f"Magnitude: {mag:.2f}"
            mag_color = Color.BRIGHT_GREEN if mag > self.deadzone else Color.RED
            self.renderer.draw_text(5, self.renderer.height - 5, mag_text, mag_color)

            # Direction angle
            if mag > self.deadzone:
                angle = math.degrees(math.atan2(y, x))
                dir_text = f"Direction: {angle:+.0f}°"
                self.renderer.draw_text(5, self.renderer.height - 4, dir_text, Color.YELLOW)

        # Footer
        footer = "Press ESC or Q to exit"
        self.renderer.draw_text(
            (self.renderer.width - len(footer)) // 2,
            self.renderer.height - 2,
            footer, Color.DARK_GRAY
        )

        self.renderer.render()

    def handle_input(self):
        """Handle keyboard input for exit only."""
        # Only check keyboard - allow all joystick input to be tested
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.01)
            if key:
                if key.name == 'KEY_ESCAPE' or key.lower() == 'q':
                    self.running = False

    def run(self):
        """Main loop."""
        try:
            self.renderer.enter_fullscreen()

            while self.running:
                self.draw()
                self.handle_input()
                time.sleep(0.016)  # ~60 FPS for responsive input

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_joystick_viz():
    """Entry point for joystick visualizer."""
    viz = JoystickViz()
    viz.run()
