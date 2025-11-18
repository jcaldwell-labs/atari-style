"""Starfield demo with joystick-controlled parameters."""

import random
import time
from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


class Star:
    """Represents a star in 3D space."""

    def __init__(self, width: int, height: int):
        self.x = random.uniform(-width, width)
        self.y = random.uniform(-height, height)
        self.z = random.uniform(1, width)

    def update(self, speed: float, width: int, height: int):
        """Update star position."""
        self.z -= speed
        if self.z <= 0:
            self.x = random.uniform(-width, width)
            self.y = random.uniform(-height, height)
            self.z = width

    def project(self, width: int, height: int):
        """Project 3D position to 2D screen coordinates."""
        # Perspective projection
        k = 128 / self.z
        x = int(self.x * k + width / 2)
        y = int(self.y * k + height / 2)
        return x, y, k


class StarfieldDemo:
    """Interactive starfield demo."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.stars = []
        self.running = True

        # Animation parameters
        self.base_speed = 2.0
        self.speed_multiplier = 1.0
        self.warp_speed = 1.0
        self.color_mode = 0  # 0: white, 1: rainbow, 2: speed-based

        # Initialize stars
        num_stars = 200
        for _ in range(num_stars):
            self.stars.append(Star(self.renderer.width, self.renderer.height))

    def get_star_color(self, star: Star, depth: float) -> str:
        """Determine star color based on mode."""
        if self.color_mode == 0:
            # Monochrome based on depth
            if depth > 2:
                return Color.BRIGHT_WHITE
            elif depth > 1:
                return Color.WHITE
            else:
                return Color.CYAN
        elif self.color_mode == 1:
            # Rainbow based on position
            colors = [Color.RED, Color.YELLOW, Color.GREEN, Color.CYAN, Color.BLUE, Color.MAGENTA]
            idx = int(abs(star.x + star.y) * 0.1) % len(colors)
            return colors[idx]
        else:  # color_mode == 2
            # Speed-based coloring
            if self.warp_speed > 3:
                return Color.BRIGHT_CYAN
            elif self.warp_speed > 2:
                return Color.BRIGHT_BLUE
            elif self.warp_speed > 1.5:
                return Color.BLUE
            else:
                return Color.WHITE

    def get_star_char(self, depth: float) -> str:
        """Get character to draw based on star depth (brightness)."""
        if depth > 3:
            return '█'
        elif depth > 2:
            return '●'
        elif depth > 1:
            return '·'
        else:
            return '.'

    def draw(self):
        """Render the starfield."""
        self.renderer.clear_buffer()

        # Draw stars
        for star in self.stars:
            x, y, depth = star.project(self.renderer.width, self.renderer.height)

            if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                char = self.get_star_char(depth)
                color = self.get_star_color(star, depth)

                # Draw motion trails at high speed
                if self.warp_speed > 2.5:
                    trail_length = int(self.warp_speed)
                    for i in range(trail_length):
                        trail_x = x - i
                        if 0 <= trail_x < self.renderer.width:
                            self.renderer.set_pixel(trail_x, y, '-', color)

                self.renderer.set_pixel(x, y, char, color)

        # Draw HUD
        hud_y = 1
        self.renderer.draw_text(2, hud_y, f"Speed: {self.warp_speed:.1f}x", Color.YELLOW)
        self.renderer.draw_text(2, hud_y + 1, f"Stars: {len(self.stars)}", Color.YELLOW)

        color_mode_names = ["Monochrome", "Rainbow", "Speed-based"]
        self.renderer.draw_text(2, hud_y + 2, f"Color: {color_mode_names[self.color_mode]}", Color.YELLOW)

        # Draw controls
        controls = [
            "Controls:",
            "Arrow/WASD/Joy: Speed",
            "Space: Toggle Color",
            "ESC/Q: Exit"
        ]
        for i, text in enumerate(controls):
            self.renderer.draw_text(self.renderer.width - 25, hud_y + i, text, Color.CYAN)

        self.renderer.render()

    def update(self):
        """Update starfield animation."""
        for star in self.stars:
            star.update(self.base_speed * self.warp_speed, self.renderer.width, self.renderer.height)

    def handle_input(self):
        """Handle user input to control parameters."""
        input_type = self.input_handler.get_input(timeout=0.01)

        # Speed control
        if input_type == InputType.UP:
            self.warp_speed = min(5.0, self.warp_speed + 0.1)
        elif input_type == InputType.DOWN:
            self.warp_speed = max(0.1, self.warp_speed - 0.1)
        elif input_type == InputType.RIGHT:
            self.warp_speed = min(5.0, self.warp_speed + 0.05)
        elif input_type == InputType.LEFT:
            self.warp_speed = max(0.1, self.warp_speed - 0.05)

        # Toggle color mode
        if input_type == InputType.SELECT:
            self.color_mode = (self.color_mode + 1) % 3
            time.sleep(0.2)  # Debounce

        # Exit
        if input_type == InputType.QUIT or input_type == InputType.BACK:
            self.running = False

        # Check joystick for analog control
        x, y = self.input_handler.get_joystick_state()
        if abs(y) > 0.1:
            # Vertical axis controls speed
            self.warp_speed = max(0.1, min(5.0, self.warp_speed - y * 0.05))

    def run(self):
        """Run the starfield demo."""
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            while self.running:
                self.draw()
                self.update()
                self.handle_input()
                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()


def run_starfield():
    """Entry point for starfield demo."""
    demo = StarfieldDemo()
    demo.run()
