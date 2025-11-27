"""Rhythm-Based Flux Control - timing-based fluid dynamics game."""

import time
import random
import math
from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


class BeatSystem:
    """Manages the rhythm beat timing and accuracy tracking."""

    def __init__(self, initial_interval=2.0):
        """Initialize beat system.

        Args:
            initial_interval: Time between beats in seconds
        """
        self.beat_interval = initial_interval  # Seconds per beat
        self.beat_window = 0.3  # Perfect/Good timing window (seconds)
        self.perfect_window = 0.1  # Perfect timing window (seconds)

        self.last_beat_time = 0.0
        self.next_beat_time = 0.0
        self.time_since_start = 0.0

        # Beat visual state
        self.beat_progress = 0.0  # 0.0 to 1.0 progress to next beat
        self.beat_flash = 0.0  # Flash intensity on beat

        # Timing stats
        self.perfect_count = 0
        self.good_count = 0
        self.miss_count = 0
        self.total_attempts = 0

    def update(self, dt):
        """Update beat timing."""
        self.time_since_start += dt

        # Calculate beat progress
        elapsed = self.time_since_start - self.last_beat_time
        self.beat_progress = elapsed / self.beat_interval

        # Check for beat trigger
        if self.beat_progress >= 1.0:
            self._trigger_beat()

        # Decay beat flash
        if self.beat_flash > 0:
            self.beat_flash = max(0, self.beat_flash - dt * 3.0)

    def _trigger_beat(self):
        """Trigger a beat event."""
        self.last_beat_time = self.time_since_start
        self.next_beat_time = self.last_beat_time + self.beat_interval
        self.beat_progress = 0.0
        self.beat_flash = 1.0

    def check_timing(self):
        """Check timing accuracy of a drain attempt.

        Returns:
            tuple: (accuracy_type, time_delta) where accuracy_type is 'perfect', 'good', or 'miss'
        """
        # Calculate how far we are from the beat
        time_to_beat = abs(self.beat_progress - 1.0) * self.beat_interval

        self.total_attempts += 1

        if time_to_beat <= self.perfect_window:
            self.perfect_count += 1
            return ('perfect', time_to_beat)
        elif time_to_beat <= self.beat_window:
            self.good_count += 1
            return ('good', time_to_beat)
        else:
            self.miss_count += 1
            return ('miss', time_to_beat)

    def increase_tempo(self, amount=0.1):
        """Increase tempo by decreasing beat interval."""
        self.beat_interval = max(0.8, self.beat_interval - amount)

    def get_bpm(self):
        """Get current tempo in beats per minute."""
        return 60.0 / self.beat_interval if self.beat_interval > 0 else 0


class FluidLattice:
    """Simplified fluid simulation for the rhythm game."""

    def __init__(self, width, height):
        """Initialize fluid lattice.

        Args:
            width: Lattice width
            height: Lattice height
        """
        self.width = width
        self.height = height

        # Fluid properties
        self.wave_speed = 0.3
        self.damping = 0.92  # Lower = faster decay, more forgiving

        # Lattice grids
        self.current = [[0.0 for _ in range(width)] for _ in range(height)]
        self.previous = [[0.0 for _ in range(width)] for _ in range(height)]

        # Rain system - drops per second (not per frame!)
        self.rain_rate = 3.0  # ~3 drops per second

    def add_drop(self, x, y, strength=8.0):
        """Add a water drop at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.current[y][x] += strength

    def drain_global(self, effectiveness):
        """Drain all fluid globally based on effectiveness (0.0 to 1.0).

        Args:
            effectiveness: 0.0 to 1.0, how much to reduce all values
        """
        # effectiveness 0.9 = reduce to 10% (multiply by 0.1)
        # effectiveness 0.6 = reduce to 40% (multiply by 0.4)
        # effectiveness 0.3 = reduce to 70% (multiply by 0.7)
        multiplier = 1.0 - effectiveness
        for y in range(self.height):
            for x in range(self.width):
                self.current[y][x] *= multiplier
                self.previous[y][x] *= multiplier

    def update(self, dt):
        """Update fluid simulation."""
        # Add random rain drops (rate is drops per second)
        # Use Poisson-like spawning: expected drops = rate * dt
        expected_drops = self.rain_rate * dt
        # Always spawn if >= 1 expected, otherwise probabilistic
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

                # Zero out small values
                if abs(new_value) < 0.2:
                    new_value = 0.0

                # Update
                self.previous[y][x] = self.current[y][x]
                self.current[y][x] = new_value

    def get_total_energy(self):
        """Calculate total fluid energy (for game over condition)."""
        total = 0.0
        for row in self.current:
            for value in row:
                total += abs(value)
        return total


class RhythmFluxControl:
    """Rhythm-based fluid control game."""

    def __init__(self):
        """Initialize the game."""
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Game dimensions
        self.game_width = self.renderer.width // 2
        self.game_height = self.renderer.height - 10  # Leave room for UI

        # Game systems
        self.beat_system = BeatSystem(initial_interval=2.0)
        self.fluid = FluidLattice(self.game_width, self.game_height)

        # Game state
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.survival_time = 0.0
        self.game_over = False
        self.game_over_time = 0

        # Tempo progression
        self.last_tempo_increase = 0.0
        self.tempo_increase_interval = 30.0  # Increase tempo every 30 seconds

        # Visual effects
        self.drain_flash = 0.0
        self.drain_flash_color = Color.WHITE
        self.last_feedback = ""
        self.feedback_timer = 0.0

        # Difficulty threshold - higher = more forgiving
        self.max_energy = 2500.0  # Game over if fluid energy exceeds this

    def update(self, dt):
        """Update game state."""
        if self.game_over:
            self.game_over_time += dt
            return

        # Update systems
        self.beat_system.update(dt)
        self.fluid.update(dt)
        self.survival_time += dt

        # Decay visual effects
        if self.drain_flash > 0:
            self.drain_flash = max(0, self.drain_flash - dt * 4.0)

        if self.feedback_timer > 0:
            self.feedback_timer -= dt

        # Tempo progression
        if self.survival_time - self.last_tempo_increase >= self.tempo_increase_interval:
            self.beat_system.increase_tempo(0.1)
            self.last_tempo_increase = self.survival_time
            self.last_feedback = f"TEMPO UP! {self.beat_system.get_bpm():.0f} BPM"
            self.feedback_timer = 2.0

        # Check game over condition
        energy = self.fluid.get_total_energy()
        if energy > self.max_energy:
            self.game_over = True

    def handle_drain(self):
        """Handle drain attempt - check timing and apply effect."""
        accuracy, time_delta = self.beat_system.check_timing()

        # Calculate drain effectiveness and points
        if accuracy == 'perfect':
            effectiveness = 0.9
            points = 100
            self.combo += 1
            self.drain_flash_color = Color.BRIGHT_WHITE
            self.last_feedback = f"PERFECT! +{points}"
        elif accuracy == 'good':
            effectiveness = 0.6
            points = 25
            self.combo += 1
            self.drain_flash_color = Color.BRIGHT_CYAN
            self.last_feedback = f"GOOD! +{points}"
        else:
            effectiveness = 0.3
            points = 0
            self.combo = 0  # Break combo on miss
            self.drain_flash_color = Color.RED
            self.last_feedback = "MISS!"

        # Apply combo multiplier
        combo_multiplier = min(8, 1 + self.combo // 3)
        total_points = points * combo_multiplier

        if points > 0 and combo_multiplier > 1:
            self.last_feedback += f" x{combo_multiplier}"

        self.score += total_points
        self.max_combo = max(self.max_combo, self.combo)

        # Visual feedback
        self.drain_flash = 1.0
        self.feedback_timer = 1.0

        # Apply global drain effect based on timing accuracy
        self.fluid.drain_global(effectiveness)

    def draw(self):
        """Draw the game."""
        self.renderer.clear_buffer()

        # Draw fluid lattice
        self._draw_fluid()

        # Draw beat indicator
        self._draw_beat_indicator()

        # Draw UI
        self._draw_ui()

        # Draw game over screen
        if self.game_over:
            self._draw_game_over()

        self.renderer.render()

    def _draw_fluid(self):
        """Draw the fluid simulation."""
        for y in range(self.game_height):
            for x in range(self.game_width):
                value = self.fluid.current[y][x]

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

        # Draw drain flash overlay
        if self.drain_flash > 0:
            self._draw_flash_border()

    def _draw_flash_border(self):
        """Draw a brief flash border on successful drain."""
        if self.drain_flash < 0.3:  # Only show for brief moment
            return

        width = self.game_width * 2
        height = self.game_height

        # Top and bottom
        for x in range(width):
            self.renderer.set_pixel(x, 0, '═', self.drain_flash_color)
            self.renderer.set_pixel(x, height - 1, '═', self.drain_flash_color)

        # Left and right
        for y in range(height):
            self.renderer.set_pixel(0, y, '║', self.drain_flash_color)
            self.renderer.set_pixel(width - 1, y, '║', self.drain_flash_color)

    def _draw_beat_indicator(self):
        """Draw the visual beat indicator."""
        # Draw pulsing border that contracts on beat
        progress = self.beat_system.beat_progress

        # Calculate border inset based on beat progress
        # Progress goes 0->1, we want border to pulse inward near 1
        pulse_strength = math.sin(progress * math.pi * 2) * 0.5 + 0.5
        max_inset = 3
        inset = int(pulse_strength * max_inset)

        width = self.game_width * 2
        height = self.game_height

        # Determine color based on proximity to beat
        if progress > 0.85:  # Near the beat
            border_color = Color.BRIGHT_YELLOW
        elif progress > 0.7:
            border_color = Color.YELLOW
        else:
            border_color = Color.CYAN

        # Draw the border with inset
        for x in range(inset, width - inset):
            self.renderer.set_pixel(x, inset, '─', border_color)
            self.renderer.set_pixel(x, height - 1 - inset, '─', border_color)

        for y in range(inset, height - inset):
            self.renderer.set_pixel(inset, y, '│', border_color)
            self.renderer.set_pixel(width - 1 - inset, y, '│', border_color)

        # Draw beat marker (shrinking ring)
        self._draw_beat_marker(progress)

    def _draw_beat_marker(self, progress):
        """Draw a shrinking ring that indicates when to press."""
        center_x = self.game_width
        center_y = self.game_height // 2

        # Ring radius shrinks as we approach the beat
        max_radius = 15
        min_radius = 3
        radius = int(max_radius - (progress * (max_radius - min_radius)))

        # Color based on timing window
        if 1.0 - progress <= self.beat_system.perfect_window / self.beat_system.beat_interval:
            color = Color.BRIGHT_WHITE  # Perfect window
        elif 1.0 - progress <= self.beat_system.beat_window / self.beat_system.beat_interval:
            color = Color.BRIGHT_GREEN  # Good window
        else:
            color = Color.CYAN

        # Draw the ring
        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            x = int(center_x + radius * math.cos(rad))
            y = int(center_y + radius * 0.5 * math.sin(rad))  # Aspect ratio correction

            if 0 <= x < self.renderer.width and 0 <= y < self.game_height:
                self.renderer.set_pixel(x, y, '○', color)

        # Draw center target
        self.renderer.set_pixel(center_x, center_y, '╬', Color.BRIGHT_RED)

    def _draw_ui(self):
        """Draw game UI."""
        ui_y = self.game_height + 1

        # Draw separator
        for x in range(self.renderer.width):
            self.renderer.set_pixel(x, ui_y - 1, '═', Color.WHITE)

        # Score and combo
        self.renderer.draw_text(2, ui_y, f"SCORE: {self.score}", Color.BRIGHT_WHITE)

        combo_text = f"COMBO: {self.combo}"
        if self.combo > 0:
            combo_color = Color.BRIGHT_YELLOW if self.combo >= 9 else Color.BRIGHT_GREEN
            self.renderer.draw_text(2, ui_y + 1, combo_text, combo_color)
        else:
            self.renderer.draw_text(2, ui_y + 1, combo_text, Color.WHITE)

        # Tempo and time
        tempo_text = f"BPM: {self.beat_system.get_bpm():.0f}"
        self.renderer.draw_text(2, ui_y + 2, tempo_text, Color.CYAN)

        time_text = f"TIME: {int(self.survival_time)}s"
        self.renderer.draw_text(2, ui_y + 3, time_text, Color.CYAN)

        # Stats
        stats_x = 30
        self.renderer.draw_text(stats_x, ui_y,
                               f"Perfect: {self.beat_system.perfect_count}",
                               Color.BRIGHT_WHITE)
        self.renderer.draw_text(stats_x, ui_y + 1,
                               f"Good: {self.beat_system.good_count}",
                               Color.BRIGHT_GREEN)
        self.renderer.draw_text(stats_x, ui_y + 2,
                               f"Miss: {self.beat_system.miss_count}",
                               Color.RED)

        # Energy meter
        energy = self.fluid.get_total_energy()
        energy_pct = min(100, (energy / self.max_energy) * 100)

        meter_x = 60
        meter_width = 30
        filled = int((energy_pct / 100.0) * meter_width)

        self.renderer.draw_text(meter_x, ui_y, "FLUX:", Color.WHITE)
        self.renderer.set_pixel(meter_x + 6, ui_y, '[', Color.WHITE)

        for i in range(meter_width):
            if i < filled:
                if energy_pct > 80:
                    color = Color.BRIGHT_RED
                elif energy_pct > 50:
                    color = Color.YELLOW
                else:
                    color = Color.GREEN
                self.renderer.set_pixel(meter_x + 7 + i, ui_y, '█', color)
            else:
                self.renderer.set_pixel(meter_x + 7 + i, ui_y, '─', Color.BLUE)

        self.renderer.set_pixel(meter_x + 7 + meter_width, ui_y, ']', Color.WHITE)
        self.renderer.draw_text(meter_x + 8 + meter_width, ui_y, f"{energy_pct:.0f}%", Color.WHITE)

        # Feedback message
        if self.feedback_timer > 0:
            msg_x = self.renderer.width // 2 - len(self.last_feedback) // 2
            self.renderer.draw_text(msg_x, ui_y + 1, self.last_feedback, Color.BRIGHT_YELLOW)

        # Controls
        controls_y = ui_y + 5
        self.renderer.draw_text(2, controls_y,
                               "SPACE/BTN: Drain (hit on beat!)  |  ESC/Q: Quit",
                               Color.CYAN)

        # Best combo
        if self.max_combo > 0:
            best_text = f"BEST COMBO: {self.max_combo}"
            self.renderer.draw_text(stats_x, ui_y + 3, best_text, Color.MAGENTA)

    def _draw_game_over(self):
        """Draw game over screen."""
        # Semi-transparent overlay
        overlay_width = 50
        overlay_height = 15
        overlay_x = (self.renderer.width - overlay_width) // 2
        overlay_y = (self.game_height - overlay_height) // 2

        # Background
        for y in range(overlay_height):
            for x in range(overlay_width):
                self.renderer.set_pixel(overlay_x + x, overlay_y + y, '░', Color.BLUE)

        # Border
        self.renderer.draw_border(overlay_x, overlay_y, overlay_width, overlay_height, Color.BRIGHT_RED)

        # Text
        title = "FLUX OVERFLOW!"
        self.renderer.draw_text(overlay_x + (overlay_width - len(title)) // 2,
                               overlay_y + 2, title, Color.BRIGHT_RED)

        stats = [
            f"Final Score: {self.score}",
            f"Survival Time: {int(self.survival_time)}s",
            f"Max Combo: {self.max_combo}",
            "",
            f"Perfect: {self.beat_system.perfect_count}",
            f"Good: {self.beat_system.good_count}",
            f"Miss: {self.beat_system.miss_count}",
        ]

        for i, stat in enumerate(stats):
            self.renderer.draw_text(overlay_x + (overlay_width - len(stat)) // 2,
                                   overlay_y + 4 + i, stat, Color.WHITE)

        # Restart prompt
        if int(self.game_over_time * 2) % 2 == 0:  # Blink effect
            prompt = "Press ESC to exit"
            self.renderer.draw_text(overlay_x + (overlay_width - len(prompt)) // 2,
                                   overlay_y + overlay_height - 2, prompt, Color.CYAN)

    def run(self):
        """Main game loop."""
        self.renderer.enter_fullscreen()

        try:
            last_time = time.time()

            while True:
                # Calculate delta time
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                # Handle input
                input_event = self.input_handler.get_input(timeout=0.016)

                if input_event == InputType.QUIT or input_event == InputType.BACK:
                    break

                if input_event == InputType.SELECT and not self.game_over:
                    self.handle_drain()

                # Update game state
                self.update(dt)

                # Draw
                self.draw()

                # Frame rate limiting
                time.sleep(0.016)  # ~60 FPS

        finally:
            self.renderer.exit_fullscreen()


def run_rhythm_flux():
    """Entry point for rhythm flux control game."""
    game = RhythmFluxControl()
    game.run()


if __name__ == "__main__":
    run_rhythm_flux()
