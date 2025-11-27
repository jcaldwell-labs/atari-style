"""Flux Control Zen - Relaxed fluid dynamics with joystick panning."""

import time
import random
import math
from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


class FluidLattice:
    """Fluid simulation - larger area that can be panned."""

    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Fluid properties
        self.wave_speed = 0.3
        self.damping = 0.94

        # Lattice grids
        self.current = [[0.0 for _ in range(width)] for _ in range(height)]
        self.previous = [[0.0 for _ in range(width)] for _ in range(height)]

        # Rain system
        self.rain_rate = 2.0  # drops per second

    def add_drop(self, x, y, strength=10.0):
        """Add a water drop at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.current[y][x] += strength

    def drain_global(self, amount=0.7):
        """Drain all fluid by percentage."""
        multiplier = 1.0 - amount
        for y in range(self.height):
            for x in range(self.width):
                self.current[y][x] *= multiplier
                self.previous[y][x] *= multiplier

    def update(self, dt):
        """Update fluid simulation."""
        # Add random rain drops
        expected_drops = self.rain_rate * dt
        while expected_drops >= 1.0:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            self.add_drop(x, y, 10.0)
            expected_drops -= 1.0
        if random.random() < expected_drops:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            self.add_drop(x, y, 10.0)

        # Wave equation simulation
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                laplacian = (
                    self.current[y - 1][x] + self.current[y + 1][x] +
                    self.current[y][x - 1] + self.current[y][x + 1] -
                    4 * self.current[y][x]
                )

                new_value = (
                    2 * self.current[y][x] - self.previous[y][x] +
                    self.wave_speed * self.wave_speed * laplacian
                )

                new_value *= self.damping

                if abs(new_value) < 0.2:
                    new_value = 0.0

                self.previous[y][x] = self.current[y][x]
                self.current[y][x] = new_value

    def get_total_energy(self):
        """Calculate total fluid energy."""
        total = 0.0
        for row in self.current:
            for value in row:
                total += abs(value)
        return total


class FluxControlZen:
    """Zen mode - relaxed fluid control with joystick panning."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Display layout
        self.control_panel_height = 8
        self.view_height = self.renderer.height - self.control_panel_height
        self.view_width = self.renderer.width

        # Create larger fluid area (2x screen size for panning)
        self.fluid_width = self.view_width
        self.fluid_height = self.view_height * 2
        self.fluid = FluidLattice(self.fluid_width, self.fluid_height)

        # View position (for panning)
        self.view_x = 0.0
        self.view_y = float(self.fluid_height // 4)  # Start centered

        # Pan smoothing
        self.pan_speed = 30.0  # pixels per second at full joystick

        # Stats
        self.session_time = 0.0
        self.drains_used = 0
        self.drops_witnessed = 0

        # Drain cooldown (gentle limit)
        self.drain_cooldown = 0.0
        self.drain_ready = True

    def update(self, dt):
        """Update game state."""
        self.session_time += dt
        self.fluid.update(dt)

        # Update drain cooldown
        if self.drain_cooldown > 0:
            self.drain_cooldown -= dt
            if self.drain_cooldown <= 0:
                self.drain_ready = True

    def handle_pan(self, joy_x, joy_y):
        """Pan the view based on joystick input."""
        # joy_x and joy_y are -1 to 1
        # Pan the view (with bounds)
        self.view_y += joy_y * self.pan_speed * 0.016  # Assuming ~60fps

        # Clamp to valid range
        max_y = self.fluid_height - self.view_height
        self.view_y = max(0, min(max_y, self.view_y))

    def handle_drain(self):
        """Perform a drain action."""
        if self.drain_ready:
            self.fluid.drain_global(0.6)
            self.drains_used += 1
            self.drain_cooldown = 1.5  # 1.5 second cooldown
            self.drain_ready = False

    def draw(self):
        """Draw the zen interface."""
        self.renderer.clear_buffer()

        # Draw fluid view (top section)
        self._draw_fluid_view()

        # Draw control panel (bottom section)
        self._draw_control_panel()

        self.renderer.render()

    def _draw_fluid_view(self):
        """Draw the panned fluid view."""
        view_y_int = int(self.view_y)

        for screen_y in range(self.view_height):
            fluid_y = view_y_int + screen_y
            if fluid_y >= self.fluid_height:
                continue

            for screen_x in range(self.view_width):
                fluid_x = screen_x
                if fluid_x >= self.fluid_width:
                    continue

                value = self.fluid.current[fluid_y][fluid_x]

                # Map value to character and color (zen palette)
                if abs(value) < 0.3:
                    continue  # Empty
                elif abs(value) < 1.0:
                    char = '·'
                    color = Color.BLUE
                elif abs(value) < 2.0:
                    char = '∘'
                    color = Color.CYAN
                elif abs(value) < 4.0:
                    char = '○'
                    color = Color.BRIGHT_CYAN
                elif abs(value) < 6.0:
                    char = '◎'
                    color = Color.BRIGHT_WHITE
                else:
                    char = '●'
                    color = Color.WHITE

                self.renderer.set_pixel(screen_x, screen_y, char, color)

        # Draw subtle view position indicator on right edge
        indicator_y = int((self.view_y / (self.fluid_height - self.view_height)) * (self.view_height - 1))
        self.renderer.set_pixel(self.view_width - 1, indicator_y, '◆', Color.YELLOW)

    def _draw_control_panel(self):
        """Draw the control surface at the bottom."""
        panel_y = self.view_height

        # Separator line
        for x in range(self.view_width):
            self.renderer.set_pixel(x, panel_y, '═', Color.BLUE)

        # Panel background hint
        panel_y += 1

        # Left section: Session info
        self.renderer.draw_text(2, panel_y, "ZEN MODE", Color.BRIGHT_CYAN)
        self.renderer.draw_text(2, panel_y + 1,
                               f"Time: {int(self.session_time // 60)}:{int(self.session_time % 60):02d}",
                               Color.CYAN)
        self.renderer.draw_text(2, panel_y + 2,
                               f"Drains: {self.drains_used}",
                               Color.CYAN)

        # Center section: Energy display
        energy = self.fluid.get_total_energy()
        max_display = 3000
        energy_pct = min(100, (energy / max_display) * 100)

        center_x = self.view_width // 2 - 15
        self.renderer.draw_text(center_x, panel_y, "ENERGY", Color.WHITE)

        # Energy bar
        bar_width = 30
        filled = int((energy_pct / 100) * bar_width)
        bar_y = panel_y + 1

        self.renderer.set_pixel(center_x, bar_y, '[', Color.WHITE)
        for i in range(bar_width):
            if i < filled:
                if energy_pct > 80:
                    color = Color.BRIGHT_YELLOW
                elif energy_pct > 50:
                    color = Color.CYAN
                else:
                    color = Color.BLUE
                self.renderer.set_pixel(center_x + 1 + i, bar_y, '▓', color)
            else:
                self.renderer.set_pixel(center_x + 1 + i, bar_y, '░', Color.BLUE)
        self.renderer.set_pixel(center_x + 1 + bar_width, bar_y, ']', Color.WHITE)

        self.renderer.draw_text(center_x + bar_width + 3, bar_y,
                               f"{energy_pct:.0f}%", Color.WHITE)

        # Right section: Controls
        controls_x = self.view_width - 35
        self.renderer.draw_text(controls_x, panel_y, "CONTROLS", Color.WHITE)
        self.renderer.draw_text(controls_x, panel_y + 1,
                               "Joystick: Pan view", Color.CYAN)

        # Drain button status
        if self.drain_ready:
            self.renderer.draw_text(controls_x, panel_y + 2,
                                   "SPACE/BTN: DRAIN", Color.BRIGHT_GREEN)
        else:
            cooldown_pct = int((self.drain_cooldown / 1.5) * 100)
            self.renderer.draw_text(controls_x, panel_y + 2,
                                   f"Drain cooling... {cooldown_pct}%", Color.YELLOW)

        self.renderer.draw_text(controls_x, panel_y + 3,
                               "ESC: Exit", Color.CYAN)

        # View position hint
        view_pct = (self.view_y / (self.fluid_height - self.view_height)) * 100
        self.renderer.draw_text(controls_x, panel_y + 5,
                               f"View: {view_pct:.0f}%", Color.BLUE)

    def run(self):
        """Main loop."""
        self.renderer.enter_fullscreen()

        try:
            last_time = time.time()

            while True:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                # Handle input
                input_event = self.input_handler.get_input(timeout=0.016)

                if input_event == InputType.QUIT or input_event == InputType.BACK:
                    break

                if input_event == InputType.SELECT:
                    self.handle_drain()

                # Get joystick state for panning
                joy_state = self.input_handler.get_joystick_state()
                if joy_state:
                    self.handle_pan(joy_state.get('x', 0), joy_state.get('y', 0))

                # Keyboard panning fallback
                if input_event == InputType.UP:
                    self.handle_pan(0, -0.5)
                elif input_event == InputType.DOWN:
                    self.handle_pan(0, 0.5)

                # Update
                self.update(dt)

                # Draw
                self.draw()

                time.sleep(0.016)

        finally:
            self.renderer.exit_fullscreen()


def run_flux_zen():
    """Entry point for zen mode."""
    game = FluxControlZen()
    game.run()


if __name__ == "__main__":
    run_flux_zen()
