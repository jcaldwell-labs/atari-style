"""Joystick connection verification and testing."""

import time
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType


class JoystickTest:
    """Visual joystick testing interface."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True

    def draw_crosshair(self, cx: int, cy: int, x: float, y: float):
        """Draw joystick position crosshair."""
        # Draw center reference
        self.renderer.draw_text(cx - 1, cy, '┼', Color.YELLOW)

        # Draw axes
        for i in range(-20, 21):
            self.renderer.set_pixel(cx + i, cy, '─', Color.CYAN)
            self.renderer.set_pixel(cx, cy + i // 2, '│', Color.CYAN)

        # Draw current position
        pos_x = int(cx + x * 20)
        pos_y = int(cy + y * 10)
        if 0 <= pos_x < self.renderer.width and 0 <= pos_y < self.renderer.height:
            self.renderer.set_pixel(pos_x, pos_y, '●', Color.BRIGHT_GREEN)

            # Draw line from center to position
            steps = 20
            for i in range(steps):
                t = i / steps
                lx = int(cx + x * 20 * t)
                ly = int(cy + y * 10 * t)
                if 0 <= lx < self.renderer.width and 0 <= ly < self.renderer.height:
                    self.renderer.set_pixel(lx, ly, '·', Color.GREEN)

    def draw_button_indicator(self, x: int, y: int, button_num: int, pressed: bool):
        """Draw a button state indicator."""
        color = Color.BRIGHT_GREEN if pressed else Color.WHITE
        char = '█' if pressed else '□'
        self.renderer.draw_text(x, y, f"BTN {button_num}: {char}", color)

    def draw(self):
        """Render the joystick test interface."""
        self.renderer.clear_buffer()

        # Draw title
        title = "JOYSTICK VERIFICATION"
        self.renderer.draw_text((self.renderer.width - len(title)) // 2, 2, title, Color.BRIGHT_CYAN)

        # Get joystick info
        info = self.input_handler.verify_joystick()

        # Connection status
        if info['connected']:
            status = f"CONNECTED: {info['name']}"
            color = Color.BRIGHT_GREEN
        else:
            status = "NO JOYSTICK DETECTED"
            color = Color.BRIGHT_RED

        self.renderer.draw_text((self.renderer.width - len(status)) // 2, 4, status, color)

        if info['connected']:
            # Draw joystick state
            cx = self.renderer.width // 2
            cy = self.renderer.height // 2

            # Get current axis values
            x, y = self.input_handler.get_joystick_state()

            # Draw crosshair
            self.draw_crosshair(cx, cy, x, y)

            # Draw axis values
            self.renderer.draw_text(5, 8, f"X Axis: {x:+.2f}", Color.YELLOW)
            self.renderer.draw_text(5, 9, f"Y Axis: {y:+.2f}", Color.YELLOW)

            # Draw button states
            buttons = self.input_handler.get_joystick_buttons()
            button_y = 11
            for i in range(min(8, len(buttons))):
                self.draw_button_indicator(5, button_y + i, i, buttons.get(i, False))

            # Draw info
            self.renderer.draw_text(5, 6, f"Axes: {info['axes']}", Color.CYAN)
            self.renderer.draw_text(5, 7, f"Buttons: {info['buttons']}", Color.CYAN)

            # Draw visual button panel on right
            if buttons:
                panel_x = self.renderer.width - 25
                panel_y = 8
                self.renderer.draw_text(panel_x, panel_y, "BUTTON PANEL", Color.MAGENTA)

                # Draw button grid
                for i, (btn_id, pressed) in enumerate(list(buttons.items())[:12]):
                    grid_x = panel_x + (i % 4) * 5
                    grid_y = panel_y + 2 + (i // 4) * 2
                    color = Color.BRIGHT_GREEN if pressed else Color.WHITE
                    char = '█' if pressed else '□'
                    self.renderer.draw_text(grid_x, grid_y, f"{btn_id}:{char}", color)

        # Draw instructions
        instructions = [
            "Move joystick to test axes",
            "Press ALL buttons to test",
            "Press KEYBOARD ESC/Q to exit"
        ]
        for i, text in enumerate(instructions):
            self.renderer.draw_text((self.renderer.width - len(text)) // 2,
                                   self.renderer.height - 5 + i, text, Color.CYAN)

        self.renderer.render()

    def handle_input(self):
        """Handle user input - ONLY keyboard, to allow testing all joystick buttons."""
        # Only check keyboard for exit - don't use get_input() because it maps
        # joystick buttons which we want to test freely
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.01)

            if key:
                if key.name == 'KEY_ESCAPE' or key.lower() == 'q':
                    self.running = False

    def run(self):
        """Run the joystick test."""
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            while self.running:
                self.draw()
                self.handle_input()
                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()


def run_joystick_test():
    """Entry point for joystick test."""
    test = JoystickTest()
    test.run()
