"""Flux Control - Energy management game based on wave simulation."""

import time
import random
import math
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType


class FluxControl:
    """Energy management game using fluid lattice wave mechanics.

    The goal is to survive by preventing energy overload while managing
    wave propagation in a fluid lattice simulation.
    """

    # Game states
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GAME_OVER = 2

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.width = self.renderer.width // 2
        self.height = self.renderer.height

        # Game state
        self.state = self.STATE_MENU
        self.score = 0
        self.survival_time = 0.0
        self.high_score = 0

        # Wave simulation lattice (from FluidLattice)
        self.current = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.previous = [[0.0 for _ in range(self.width)] for _ in range(self.height)]

        # Wave parameters
        self.rain_rate = 0.4  # Auto-drop frequency
        self.wave_speed = 0.3
        self.drop_strength = 10.0
        self.damping = 0.95

        # Energy management
        self.energy_threshold = 500.0  # Game over if exceeded for too long
        self.current_energy = 0.0
        self.energy_history = []  # Track energy over time
        self.warning_time = 0.0  # How long we've been over threshold
        self.warning_threshold = 3.0  # Seconds over threshold before game over

        # Drain ability
        self.drain_cooldown_max = 5.0  # 5 second cooldown
        self.drain_cooldown = 0.0  # Current cooldown timer
        self.drain_reduction = 0.3  # Reduce values to 30% (70% drain)

        # Visual effects
        self.flash_timer = 0.0
        self.flash_duration = 0.2

        # Frame timing
        self.last_time = time.time()

    def reset_game(self):
        """Reset game state for new game."""
        self.state = self.STATE_PLAYING
        self.score = 0
        self.survival_time = 0.0
        self.current_energy = 0.0
        self.energy_history = []
        self.warning_time = 0.0
        self.drain_cooldown = 0.0
        self.flash_timer = 0.0

        # Clear lattice
        for y in range(self.height):
            for x in range(self.width):
                self.current[y][x] = 0.0
                self.previous[y][x] = 0.0

        self.last_time = time.time()

    def calculate_energy(self):
        """Calculate total energy in the system (sum of absolute values)."""
        total = 0.0
        for y in range(self.height):
            for x in range(self.width):
                total += abs(self.current[y][x])
        return total

    def activate_drain(self):
        """Drain energy from the system (reduce all wave values by 70%)."""
        if self.drain_cooldown > 0:
            return  # Cooldown not ready

        # Apply drain to all cells
        for y in range(self.height):
            for x in range(self.width):
                self.current[y][x] *= self.drain_reduction
                self.previous[y][x] *= self.drain_reduction

        # Start cooldown
        self.drain_cooldown = self.drain_cooldown_max
        self.flash_timer = self.flash_duration

    def update_wave_simulation(self, dt: float):
        """Update the fluid lattice wave simulation."""
        # Add random energy drops
        if random.random() < self.rain_rate * dt:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            self.current[y][x] += self.drop_strength

        # Wave equation simulation
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                # Calculate Laplacian (neighbors)
                laplacian = (
                    self.current[y - 1][x] + self.current[y + 1][x] +
                    self.current[y][x - 1] + self.current[y][x + 1] -
                    4 * self.current[y][x]
                )

                # Wave equation: d²u/dt² = c² ∇²u
                new_value = (
                    2 * self.current[y][x] - self.previous[y][x] +
                    self.wave_speed * self.wave_speed * laplacian
                )

                # Apply damping
                new_value *= self.damping

                # Zero out small values to prevent accumulation
                if abs(new_value) < 0.2:
                    new_value = 0.0

                # Update
                self.previous[y][x] = self.current[y][x]
                self.current[y][x] = new_value

    def update(self, dt: float):
        """Update game state."""
        if self.state == self.STATE_MENU:
            # Just waiting for input
            pass

        elif self.state == self.STATE_PLAYING:
            # Update survival time and score
            self.survival_time += dt
            self.score = int(self.survival_time)

            # Update wave simulation
            self.update_wave_simulation(dt)

            # Calculate current energy
            self.current_energy = self.calculate_energy()
            self.energy_history.append(self.current_energy)
            if len(self.energy_history) > 100:
                self.energy_history.pop(0)

            # Check for overload condition
            if self.current_energy > self.energy_threshold:
                self.warning_time += dt
                if self.warning_time >= self.warning_threshold:
                    # Game over!
                    self.state = self.STATE_GAME_OVER
                    if self.score > self.high_score:
                        self.high_score = self.score
            else:
                # Reset warning timer if we drop below threshold
                self.warning_time = 0.0

            # Update drain cooldown
            if self.drain_cooldown > 0:
                self.drain_cooldown = max(0, self.drain_cooldown - dt)

            # Update flash effect
            if self.flash_timer > 0:
                self.flash_timer = max(0, self.flash_timer - dt)

    def handle_input(self):
        """Handle user input."""
        # Check for drain activation (SPACE or button 0)
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)
            if key == ' ' and self.state == self.STATE_PLAYING:
                self.activate_drain()
            elif key.lower() == 'r' and self.state == self.STATE_GAME_OVER:
                self.reset_game()

        # Check joystick button
        buttons = self.input_handler.get_joystick_buttons()
        if buttons.get(0) and self.state == self.STATE_PLAYING:
            self.activate_drain()

        # Handle menu/quit input
        input_type = self.input_handler.get_input(timeout=0.001)

        if input_type == InputType.QUIT or input_type == InputType.BACK:
            return False  # Exit game

        if input_type == InputType.SELECT:
            if self.state == self.STATE_MENU:
                self.reset_game()
            elif self.state == self.STATE_GAME_OVER:
                self.reset_game()

        return True

    def draw_energy_bar(self):
        """Draw the energy meter at the top of the screen."""
        bar_height = 3
        bar_width = self.renderer.width - 4
        bar_x = 2
        bar_y = 1

        # Draw border
        self.renderer.draw_border(bar_x, bar_y, bar_width, bar_height, Color.CYAN)

        # Calculate fill percentage
        fill_ratio = min(1.0, self.current_energy / self.energy_threshold)
        filled_width = int((bar_width - 2) * fill_ratio)

        # Draw filled portion with color based on energy level
        if fill_ratio > 0.8:
            color = Color.BRIGHT_RED
        elif fill_ratio > 0.6:
            color = Color.BRIGHT_YELLOW
        elif fill_ratio > 0.4:
            color = Color.YELLOW
        else:
            color = Color.BRIGHT_GREEN

        for x in range(filled_width):
            self.renderer.set_pixel(bar_x + 1 + x, bar_y + 1, '█', color)

        # Draw threshold marker
        threshold_x = bar_x + 1 + (bar_width - 2)
        if threshold_x < self.renderer.width:
            self.renderer.set_pixel(threshold_x, bar_y, '▼', Color.BRIGHT_RED)
            self.renderer.set_pixel(threshold_x, bar_y + 2, '▲', Color.BRIGHT_RED)

        # Draw energy value
        energy_text = f"ENERGY: {int(self.current_energy)}/{int(self.energy_threshold)}"
        text_x = bar_x + (bar_width - len(energy_text)) // 2
        self.renderer.draw_text(text_x, bar_y - 1, energy_text, Color.BRIGHT_CYAN)

    def draw_cooldown_indicator(self):
        """Draw the drain cooldown indicator at the bottom."""
        indicator_y = self.renderer.height - 2
        indicator_width = 40
        indicator_x = (self.renderer.width - indicator_width) // 2

        # Draw label
        label = "DRAIN: "
        self.renderer.draw_text(indicator_x, indicator_y, label, Color.BRIGHT_CYAN)

        # Draw cooldown bar or READY message
        if self.drain_cooldown > 0:
            # Cooldown in progress
            cooldown_ratio = self.drain_cooldown / self.drain_cooldown_max
            cooldown_width = int((indicator_width - len(label)) * cooldown_ratio)
            bar = "[" + "=" * cooldown_width + " " * (indicator_width - len(label) - cooldown_width - 2) + "]"
            self.renderer.draw_text(indicator_x + len(label), indicator_y, bar, Color.YELLOW)

            # Draw time remaining
            time_text = f"{self.drain_cooldown:.1f}s"
            self.renderer.draw_text(indicator_x + len(label) + indicator_width - len(label), indicator_y + 1, time_text, Color.YELLOW)
        else:
            # Ready to drain
            ready_text = "[READY] Press SPACE/Button 0"
            self.renderer.draw_text(indicator_x + len(label), indicator_y, ready_text, Color.BRIGHT_GREEN)

    def draw_wave_field(self):
        """Draw the fluid lattice wave field."""
        for y in range(self.height):
            for x in range(self.width):
                value = self.current[y][x]

                # Map value to character and color
                if abs(value) < 0.3:
                    char = ' '
                    color = None
                elif abs(value) < 1.5:
                    char = '·'
                    color = Color.BLUE if value > 0 else Color.CYAN
                elif abs(value) < 3.0:
                    char = '○'
                    color = Color.CYAN if value > 0 else Color.GREEN
                elif abs(value) < 5.0:
                    char = '●'
                    color = Color.BRIGHT_CYAN if value > 0 else Color.BRIGHT_BLUE
                else:
                    char = '█'
                    color = Color.BRIGHT_WHITE if value > 0 else Color.BRIGHT_CYAN

                if color:
                    self.renderer.set_pixel(x * 2, y, char, color)

    def draw_warning_border(self):
        """Draw flashing border when energy is too high."""
        if self.current_energy <= self.energy_threshold * 0.8:
            return  # No warning needed

        # Flash effect - alternate visibility
        flash_speed = 4.0  # Hz
        if int(time.time() * flash_speed) % 2 == 0:
            color = Color.BRIGHT_RED

            # Draw border around entire screen
            for x in range(self.renderer.width):
                self.renderer.set_pixel(x, 0, '█', color)
                self.renderer.set_pixel(x, self.renderer.height - 1, '█', color)

            for y in range(self.renderer.height):
                self.renderer.set_pixel(0, y, '█', color)
                self.renderer.set_pixel(self.renderer.width - 1, y, '█', color)

            # Warning text
            warning = "OVERLOAD WARNING"
            warning_x = (self.renderer.width - len(warning)) // 2
            self.renderer.draw_text(warning_x, self.renderer.height // 2, warning, Color.BRIGHT_RED)

            # Show warning time
            if self.warning_time > 0:
                time_left = self.warning_threshold - self.warning_time
                time_text = f"Overload in: {time_left:.1f}s"
                time_x = (self.renderer.width - len(time_text)) // 2
                self.renderer.draw_text(time_x, self.renderer.height // 2 + 1, time_text, Color.BRIGHT_YELLOW)

    def draw_hud(self):
        """Draw heads-up display information."""
        # Score/Time
        score_text = f"TIME: {int(self.survival_time)}s"
        self.renderer.draw_text(2, self.renderer.height - 4, score_text, Color.BRIGHT_WHITE)

        # High score
        if self.high_score > 0:
            high_text = f"BEST: {self.high_score}s"
            self.renderer.draw_text(2, self.renderer.height - 3, high_text, Color.BRIGHT_YELLOW)

        # Controls (top right)
        controls = [
            "SPACE/BTN0: Drain",
            "ESC/Q: Exit"
        ]
        for i, control in enumerate(controls):
            self.renderer.draw_text(self.renderer.width - len(control) - 2, i, control, Color.CYAN)

    def draw_menu(self):
        """Draw the main menu screen."""
        title = "FLUX CONTROL"
        subtitle = "Energy Management Game"

        # Title
        title_x = (self.renderer.width - len(title)) // 2
        self.renderer.draw_text(title_x, self.renderer.height // 2 - 5, title, Color.BRIGHT_CYAN)

        # Subtitle
        subtitle_x = (self.renderer.width - len(subtitle)) // 2
        self.renderer.draw_text(subtitle_x, self.renderer.height // 2 - 3, subtitle, Color.CYAN)

        # Instructions
        instructions = [
            "",
            "Prevent energy overload by draining the system",
            "Energy builds up from random wave drops",
            "Stay below threshold or survive for 3 seconds",
            "",
            "Controls:",
            "  SPACE / Button 0 - Drain (70% reduction)",
            "  Drain has 5 second cooldown",
            "",
            "Press SPACE or Button 0 to start"
        ]

        start_y = self.renderer.height // 2 - 1
        for i, line in enumerate(instructions):
            if line:
                line_x = (self.renderer.width - len(line)) // 2
                color = Color.BRIGHT_YELLOW if "Press" in line else Color.WHITE
                self.renderer.draw_text(line_x, start_y + i, line, color)

        # High score
        if self.high_score > 0:
            high_text = f"High Score: {self.high_score}s"
            high_x = (self.renderer.width - len(high_text)) // 2
            self.renderer.draw_text(high_x, self.renderer.height - 3, high_text, Color.BRIGHT_GREEN)

    def draw_game_over(self):
        """Draw game over screen."""
        # Semi-transparent overlay effect (draw some chars)
        for y in range(self.renderer.height):
            for x in range(0, self.renderer.width, 4):
                if (x + y) % 8 == 0:
                    self.renderer.set_pixel(x, y, '░', Color.BLUE)

        # Game over text
        game_over = "ENERGY OVERLOAD"
        game_over_x = (self.renderer.width - len(game_over)) // 2
        self.renderer.draw_text(game_over_x, self.renderer.height // 2 - 3, game_over, Color.BRIGHT_RED)

        # Score
        score_text = f"Survived: {self.score}s"
        score_x = (self.renderer.width - len(score_text)) // 2
        self.renderer.draw_text(score_x, self.renderer.height // 2 - 1, score_text, Color.BRIGHT_WHITE)

        # High score indicator
        if self.score == self.high_score and self.high_score > 0:
            new_high = "NEW HIGH SCORE!"
            new_high_x = (self.renderer.width - len(new_high)) // 2
            self.renderer.draw_text(new_high_x, self.renderer.height // 2 + 1, new_high, Color.BRIGHT_YELLOW)

        # Restart prompt
        restart = "Press R or SPACE to restart"
        restart_x = (self.renderer.width - len(restart)) // 2
        self.renderer.draw_text(restart_x, self.renderer.height // 2 + 3, restart, Color.BRIGHT_GREEN)

        # Exit prompt
        exit_text = "Press ESC/Q to exit"
        exit_x = (self.renderer.width - len(exit_text)) // 2
        self.renderer.draw_text(exit_x, self.renderer.height // 2 + 5, exit_text, Color.CYAN)

    def draw(self):
        """Draw the game."""
        self.renderer.clear_buffer()

        if self.state == self.STATE_MENU:
            self.draw_menu()

        elif self.state == self.STATE_PLAYING:
            # Draw wave field
            self.draw_wave_field()

            # Draw warning border if energy is high
            self.draw_warning_border()

            # Draw energy bar
            self.draw_energy_bar()

            # Draw cooldown indicator
            self.draw_cooldown_indicator()

            # Draw HUD
            self.draw_hud()

        elif self.state == self.STATE_GAME_OVER:
            # Draw final wave state
            self.draw_wave_field()

            # Draw game over overlay
            self.draw_game_over()

        self.renderer.render()

    def run(self):
        """Main game loop."""
        self.renderer.enter_fullscreen()

        try:
            running = True

            while running:
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time

                # Cap dt to prevent huge jumps
                dt = min(dt, 0.1)

                # Handle input
                if not self.handle_input():
                    running = False

                # Update game
                self.update(dt)

                # Draw
                self.draw()

                # Frame rate limiting (~60 FPS)
                time.sleep(0.016)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_flux_control():
    """Entry point for Flux Control game."""
    game = FluxControl()
    game.run()


if __name__ == "__main__":
    run_flux_control()
