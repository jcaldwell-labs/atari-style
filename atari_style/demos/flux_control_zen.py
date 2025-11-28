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
        self.wave_speed = 0.45  # Moderate wave speed - bigger ripples
        self.damping = 0.86  # Balanced decay

        # Lattice grids
        self.current = [[0.0 for _ in range(width)] for _ in range(height)]
        self.previous = [[0.0 for _ in range(width)] for _ in range(height)]

        # Rain system - gentle for big ripples
        self.rain_rate = 1.5  # ~1.5 drops per second - fewer but bigger ripples

        # Delta tracking for criticality analysis
        self.coverage_history = []
        self.history_window = 30  # frames (~1 second at 30fps)

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

    def get_coverage_percent(self):
        """Calculate percentage of cells that are visually active (above render threshold)."""
        active_cells = 0
        total_cells = self.width * self.height
        for row in self.current:
            for value in row:
                if abs(value) >= 0.3:  # Same threshold as rendering
                    active_cells += 1
        return (active_cells / total_cells) * 100

    def update_coverage_history(self):
        """Track coverage over time for delta calculation."""
        coverage = self.get_coverage_percent()
        self.coverage_history.append(coverage)
        # Keep only recent history
        if len(self.coverage_history) > self.history_window:
            self.coverage_history.pop(0)

    def get_coverage_delta(self):
        """Rate of change of coverage per second."""
        if len(self.coverage_history) < 2:
            return 0.0
        # Compare oldest to newest in window
        oldest = self.coverage_history[0]
        newest = self.coverage_history[-1]
        # Frames in history / 30 fps = seconds elapsed
        time_span = len(self.coverage_history) / 30.0
        if time_span == 0:
            return 0.0
        return (newest - oldest) / time_span

    def get_activity_variance(self):
        """Measure of how much coverage fluctuates (standard deviation)."""
        if len(self.coverage_history) < 10:
            return 0.0
        mean = sum(self.coverage_history) / len(self.coverage_history)
        variance = sum((x - mean) ** 2 for x in self.coverage_history) / len(self.coverage_history)
        return variance ** 0.5


class FluxControlZen:
    """Zen mode - relaxed fluid control with joystick panning."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Display layout
        self.control_panel_height = 8
        self.view_height = self.renderer.height - self.control_panel_height
        self.view_width = self.renderer.width

        # Create larger fluid area (2x screen size in both directions for panning)
        self.fluid_width = self.view_width * 2
        self.fluid_height = self.view_height * 2
        self.fluid = FluidLattice(self.fluid_width, self.fluid_height)

        # View position (for panning) - start centered
        self.view_x = float(self.fluid_width // 4)
        self.view_y = float(self.fluid_height // 4)

        # Pan smoothing
        self.pan_speed = 30.0  # pixels per second at full joystick

        # Stats
        self.session_time = 0.0
        self.drains_used = 0
        self.drops_witnessed = 0

        # Drain cooldown (very short - drain freely)
        self.drain_cooldown = 0.0
        self.drain_ready = True
        self.drain_cooldown_time = 0.25  # Quick 0.25 second cooldown

    def update(self, dt):
        """Update game state."""
        self.session_time += dt
        self.fluid.update(dt)

        # Update drain cooldown
        if self.drain_cooldown > 0:
            self.drain_cooldown -= dt
            if self.drain_cooldown <= 0:
                self.drain_ready = True

        # No auto-drain - player controls draining with SPACE/button

    def handle_pan(self, joy_x, joy_y):
        """Pan the view based on joystick input."""
        # joy_x and joy_y are -1 to 1
        # Pan the view (with bounds)
        self.view_x += joy_x * self.pan_speed * 0.016  # Assuming ~60fps
        self.view_y += joy_y * self.pan_speed * 0.016

        # Clamp to valid range
        max_x = self.fluid_width - self.view_width
        max_y = self.fluid_height - self.view_height
        self.view_x = max(0, min(max_x, self.view_x))
        self.view_y = max(0, min(max_y, self.view_y))

    def handle_drain(self):
        """Perform a drain action."""
        if self.drain_ready:
            self.fluid.drain_global(0.9)  # 90% drain - very effective
            self.drains_used += 1
            self.drain_cooldown = self.drain_cooldown_time
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
        view_x_int = int(self.view_x)
        view_y_int = int(self.view_y)

        for screen_y in range(self.view_height):
            fluid_y = view_y_int + screen_y
            if fluid_y >= self.fluid_height:
                continue

            for screen_x in range(self.view_width):
                fluid_x = view_x_int + screen_x
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

        # Draw subtle view position indicators
        max_x = self.fluid_width - self.view_width
        max_y = self.fluid_height - self.view_height

        # Y indicator on right edge
        if max_y > 0:
            indicator_y = int((self.view_y / max_y) * (self.view_height - 1))
            self.renderer.set_pixel(self.view_width - 1, indicator_y, '◆', Color.YELLOW)

        # X indicator on bottom edge
        if max_x > 0:
            indicator_x = int((self.view_x / max_x) * (self.view_width - 1))
            self.renderer.set_pixel(indicator_x, self.view_height - 1, '◆', Color.YELLOW)

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

        # Center section: Coverage display (actual screen coverage)
        coverage_pct = self.fluid.get_coverage_percent()

        center_x = self.view_width // 2 - 15
        self.renderer.draw_text(center_x, panel_y, "COVERAGE", Color.WHITE)

        # Coverage bar
        bar_width = 30
        filled = int((coverage_pct / 100) * bar_width)
        bar_y = panel_y + 1

        self.renderer.set_pixel(center_x, bar_y, '[', Color.WHITE)
        for i in range(bar_width):
            if i < filled:
                if coverage_pct > 80:
                    color = Color.BRIGHT_YELLOW
                elif coverage_pct > 50:
                    color = Color.CYAN
                else:
                    color = Color.BLUE
                self.renderer.set_pixel(center_x + 1 + i, bar_y, '▓', color)
            else:
                self.renderer.set_pixel(center_x + 1 + i, bar_y, '░', Color.BLUE)
        self.renderer.set_pixel(center_x + 1 + bar_width, bar_y, ']', Color.WHITE)

        self.renderer.draw_text(center_x + bar_width + 3, bar_y,
                               f"{coverage_pct:.0f}%", Color.WHITE)

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
            cooldown_pct = int((self.drain_cooldown / self.drain_cooldown_time) * 100)
            self.renderer.draw_text(controls_x, panel_y + 2,
                                   f"Drain: {cooldown_pct}%", Color.YELLOW)

        self.renderer.draw_text(controls_x, panel_y + 3,
                               "ESC: Exit", Color.CYAN)

        # View position hint (X, Y)
        max_x = self.fluid_width - self.view_width
        max_y = self.fluid_height - self.view_height
        view_x_pct = (self.view_x / max_x * 100) if max_x > 0 else 50
        view_y_pct = (self.view_y / max_y * 100) if max_y > 0 else 50
        self.renderer.draw_text(controls_x, panel_y + 5,
                               f"View: {view_x_pct:.0f}%,{view_y_pct:.0f}%", Color.BLUE)

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
                jx, jy = self.input_handler.get_joystick_state()
                if abs(jx) > 0.1 or abs(jy) > 0.1:
                    self.handle_pan(jx, jy)

                # Keyboard panning fallback
                if input_event == InputType.UP:
                    self.handle_pan(0, -0.5)
                elif input_event == InputType.DOWN:
                    self.handle_pan(0, 0.5)
                elif input_event == InputType.LEFT:
                    self.handle_pan(-0.5, 0)
                elif input_event == InputType.RIGHT:
                    self.handle_pan(0.5, 0)

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


def run_flux_zen_demo(duration: int = 60):
    """Auto-demo for video recording - pans and drains automatically."""
    game = FluxControlZen()
    game.renderer.enter_fullscreen()

    try:
        start_time = time.time()
        last_time = start_time
        last_drain_time = 0

        while time.time() - start_time < duration:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            elapsed = current_time - start_time

            # Gentle 2D panning using sine waves for smooth circular motion
            # X: slow oscillation (12 second period)
            # Y: slightly faster oscillation (8 second period)
            pan_x = math.sin(elapsed * 2 * math.pi / 12) * 0.3
            pan_y = math.sin(elapsed * 2 * math.pi / 8) * 0.3

            # Apply gentle pan
            game.handle_pan(pan_x, pan_y)

            # Drain every 10 seconds to let screen fill up more
            if elapsed - last_drain_time > 10.0:
                game.handle_drain()
                last_drain_time = elapsed

            # Update simulation
            game.update(dt)

            # Draw
            game.draw()

            time.sleep(0.016)

    finally:
        game.renderer.exit_fullscreen()


if __name__ == "__main__":
    run_flux_zen()
