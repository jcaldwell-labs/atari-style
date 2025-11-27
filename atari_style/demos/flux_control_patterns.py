"""Flux Control: Pattern Matching Variant.

Players must maintain specific energy levels in different screen zones
by managing wave propagation with directional drain controls.
"""

import math
import time
import random
from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


class Zone:
    """Represents a screen quadrant with energy tracking."""

    def __init__(self, x: int, y: int, width: int, height: int, name: str):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name
        self.energy = 0.0
        self.target_level = 'MEDIUM'  # LOW, MEDIUM, HIGH

    def contains(self, x: int, y: int) -> bool:
        """Check if a point is within this zone."""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def get_energy_percentage(self) -> float:
        """Get energy as percentage (0-100)."""
        # Calculate energy based on number of cells and their intensity
        total_cells = self.width * self.height
        if total_cells == 0:
            return 0.0
        return min(100.0, (self.energy / total_cells) * 10.0)

    def is_matching_target(self) -> bool:
        """Check if current energy matches target level."""
        energy_pct = self.get_energy_percentage()
        if self.target_level == 'LOW':
            return energy_pct < 30
        elif self.target_level == 'MEDIUM':
            return 30 <= energy_pct <= 70
        elif self.target_level == 'HIGH':
            return energy_pct > 70
        return False

    def get_target_emoji(self) -> str:
        """Get emoji indicator for target level."""
        if self.target_level == 'LOW':
            return 'o'  # Blue circle
        elif self.target_level == 'MEDIUM':
            return 'o'  # Yellow circle
        elif self.target_level == 'HIGH':
            return 'O'  # Red circle (capital for emphasis)
        return '?'

    def get_target_color(self) -> str:
        """Get color for target indicator."""
        if self.target_level == 'LOW':
            return Color.BLUE
        elif self.target_level == 'MEDIUM':
            return Color.YELLOW
        elif self.target_level == 'HIGH':
            return Color.BRIGHT_RED
        return Color.WHITE


class ZoneManager:
    """Manages zones and target patterns."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Create 4 quadrants
        mid_x = screen_width // 2
        mid_y = screen_height // 2

        self.zones = [
            Zone(0, 0, mid_x, mid_y, "Top-Left"),
            Zone(mid_x, 0, screen_width - mid_x, mid_y, "Top-Right"),
            Zone(0, mid_y, mid_x, screen_height - mid_y, "Bottom-Left"),
            Zone(mid_x, mid_y, screen_width - mid_x, screen_height - mid_y, "Bottom-Right"),
        ]

        self.pattern_timer = 0.0
        self.pattern_duration = 20.0  # Change pattern every 20 seconds
        self.generate_new_pattern()

    def generate_new_pattern(self):
        """Generate a new random target pattern."""
        levels = ['LOW', 'MEDIUM', 'HIGH']
        for zone in self.zones:
            zone.target_level = random.choice(levels)
        self.pattern_timer = 0.0

    def update(self, dt: float):
        """Update zone manager state."""
        self.pattern_timer += dt
        if self.pattern_timer >= self.pattern_duration:
            self.generate_new_pattern()

    def calculate_zone_energies(self, lattice_current: list):
        """Calculate energy in each zone from lattice data."""
        # Reset energies
        for zone in self.zones:
            zone.energy = 0.0

        # Sum up energy in each zone
        height = len(lattice_current)
        width = len(lattice_current[0]) if height > 0 else 0

        for y in range(height):
            for x in range(width):
                # Map lattice coordinates to screen coordinates (lattice is half width)
                screen_x = x * 2
                screen_y = y

                # Find which zone this cell belongs to
                for zone in self.zones:
                    if zone.contains(screen_x, screen_y):
                        zone.energy += abs(lattice_current[y][x])
                        break

    def get_matching_zones_count(self) -> int:
        """Count how many zones are currently matching their targets."""
        return sum(1 for zone in self.zones if zone.is_matching_target())

    def get_zone_at_position(self, x: int, y: int) -> int:
        """Get zone index at screen position. Returns -1 if none found."""
        for i, zone in enumerate(self.zones):
            if zone.contains(x, y):
                return i
        return -1


class PatternFluxControl:
    """Pattern Matching variant of Flux Control game."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True

        # Lattice setup (based on FluidLattice from screensaver)
        self.lattice_width = self.renderer.width // 2
        self.lattice_height = self.renderer.height
        self.current = [[0.0 for _ in range(self.lattice_width)] for _ in range(self.lattice_height)]
        self.previous = [[0.0 for _ in range(self.lattice_width)] for _ in range(self.lattice_height)]

        # Wave parameters
        self.rain_rate = 0.4
        self.wave_speed = 0.3
        self.drop_strength = 8.0
        self.damping = 0.97

        # Zone management
        self.zone_manager = ZoneManager(self.renderer.width, self.renderer.height)

        # Player controls
        self.selected_zone = 0  # Which zone to drain (0-3)
        self.drain_reduction = 0.5  # Drain is 50% effective

        # Scoring
        self.score = 0
        self.combo_multiplier = 1.0
        self.combo_timer = 0.0
        self.max_combo = 1.0
        self.pattern_match_bonus = 0
        self.last_match_state = False

        # Visual feedback
        self.pattern_match_flash = 0.0
        self.flash_duration = 0.5

    def update_lattice(self, dt: float):
        """Update the wave lattice simulation."""
        # Add random rain drops
        if random.random() < self.rain_rate * dt:
            x = random.randint(1, self.lattice_width - 2)
            y = random.randint(1, self.lattice_height - 2)
            self.current[y][x] += self.drop_strength

        # Wave equation simulation
        for y in range(1, self.lattice_height - 1):
            for x in range(1, self.lattice_width - 1):
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

    def apply_drain_to_zone(self, zone_index: int):
        """Apply drain effect to selected zone only."""
        zone = self.zone_manager.zones[zone_index]

        # Drain only affects lattice cells in this zone
        for y in range(self.lattice_height):
            for x in range(self.lattice_width):
                # Map lattice coords to screen coords
                screen_x = x * 2
                screen_y = y

                if zone.contains(screen_x, screen_y):
                    # Reduce energy by drain amount
                    self.current[y][x] *= self.drain_reduction
                    self.previous[y][x] *= self.drain_reduction

    def update_scoring(self, dt: float):
        """Update score based on pattern matching."""
        matching_count = self.zone_manager.get_matching_zones_count()
        all_matching = matching_count == 4

        # Award points continuously while zones match
        if matching_count > 0:
            # Base points per matching zone
            base_points = matching_count * 10
            self.score += int(base_points * self.combo_multiplier * dt)

            # Build combo
            self.combo_timer += dt
            if self.combo_timer >= 1.0:  # Every second of sustained match
                self.combo_multiplier = min(5.0, self.combo_multiplier + 0.1)
                self.max_combo = max(self.max_combo, self.combo_multiplier)
                self.combo_timer = 0.0
        else:
            # Reset combo
            self.combo_multiplier = 1.0
            self.combo_timer = 0.0

        # Bonus flash when all zones match
        if all_matching and not self.last_match_state:
            self.pattern_match_flash = self.flash_duration
            self.pattern_match_bonus += 1000
            self.score += 1000

        self.last_match_state = all_matching

        # Decay flash
        if self.pattern_match_flash > 0:
            self.pattern_match_flash -= dt

    def draw_lattice(self):
        """Draw the wave lattice."""
        for y in range(self.lattice_height):
            for x in range(self.lattice_width):
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

    def draw_zone_dividers(self):
        """Draw dotted lines dividing zones."""
        mid_x = self.renderer.width // 2
        mid_y = self.renderer.height // 2

        # Vertical divider (every other character for dotted effect)
        for y in range(self.renderer.height):
            if y % 2 == 0:
                self.renderer.set_pixel(mid_x, y, '┆', Color.WHITE)

        # Horizontal divider
        for x in range(self.renderer.width):
            if x % 3 == 0:
                self.renderer.set_pixel(x, mid_y, '·', Color.WHITE)

    def draw_zone_indicators(self):
        """Draw target indicators and energy bars in zone corners."""
        for i, zone in enumerate(self.zone_manager.zones):
            # Position for corner indicator
            if i == 0:  # Top-Left
                corner_x, corner_y = zone.x + 2, zone.y + 1
            elif i == 1:  # Top-Right
                corner_x, corner_y = zone.x + zone.width - 12, zone.y + 1
            elif i == 2:  # Bottom-Left
                corner_x, corner_y = zone.x + 2, zone.y + zone.height - 3
            else:  # Bottom-Right
                corner_x, corner_y = zone.x + zone.width - 12, zone.y + zone.height - 3

            # Draw target indicator
            target_emoji = zone.get_target_emoji()
            target_color = zone.get_target_color()
            self.renderer.draw_text(corner_x, corner_y,
                                  f"[{target_emoji}] {zone.target_level}",
                                  target_color)

            # Draw energy bar
            energy_pct = zone.get_energy_percentage()
            bar_width = 8
            filled = int((energy_pct / 100.0) * bar_width)
            bar = '[' + '█' * filled + '·' * (bar_width - filled) + ']'

            # Color based on match status
            bar_color = Color.BRIGHT_GREEN if zone.is_matching_target() else Color.RED
            self.renderer.draw_text(corner_x, corner_y + 1, bar, bar_color)

            # Highlight selected zone
            if i == self.selected_zone:
                self.renderer.draw_text(corner_x - 2, corner_y, '>>', Color.BRIGHT_YELLOW)

    def draw_hud(self):
        """Draw game HUD."""
        # Score
        self.renderer.draw_text(2, self.renderer.height - 5,
                              f"Score: {self.score}",
                              Color.BRIGHT_YELLOW)

        # Combo
        if self.combo_multiplier > 1.0:
            self.renderer.draw_text(2, self.renderer.height - 4,
                                  f"Combo: x{self.combo_multiplier:.1f}",
                                  Color.BRIGHT_CYAN)

        # Pattern timer
        time_remaining = self.zone_manager.pattern_duration - self.zone_manager.pattern_timer
        self.renderer.draw_text(2, self.renderer.height - 3,
                              f"Next Pattern: {time_remaining:.1f}s",
                              Color.CYAN)

        # Controls
        self.renderer.draw_text(2, self.renderer.height - 2,
                              "Arrows: Select Zone | Space: Drain | ESC: Exit",
                              Color.WHITE)

        # Pattern match flash
        if self.pattern_match_flash > 0:
            flash_text = "*** PATTERN MATCH! ***"
            flash_x = (self.renderer.width - len(flash_text)) // 2
            flash_y = self.renderer.height // 2
            self.renderer.draw_text(flash_x, flash_y, flash_text, Color.BRIGHT_YELLOW)

        # Matching zones count
        matching = self.zone_manager.get_matching_zones_count()
        self.renderer.draw_text(self.renderer.width - 20, self.renderer.height - 5,
                              f"Matching: {matching}/4",
                              Color.BRIGHT_GREEN if matching == 4 else Color.YELLOW)

    def draw(self):
        """Draw entire game state."""
        self.renderer.clear_buffer()

        # Draw lattice
        self.draw_lattice()

        # Draw zone dividers
        self.draw_zone_dividers()

        # Draw zone indicators
        self.draw_zone_indicators()

        # Draw HUD
        self.draw_hud()

        self.renderer.render()

    def handle_input(self):
        """Handle player input."""
        # Check for arrow keys to select zone
        input_type = self.input_handler.get_input(timeout=0.01)

        if input_type == InputType.QUIT:
            self.running = False
        elif input_type == InputType.UP:
            # Select top zones (0 or 1)
            if self.selected_zone >= 2:
                self.selected_zone -= 2
        elif input_type == InputType.DOWN:
            # Select bottom zones (2 or 3)
            if self.selected_zone < 2:
                self.selected_zone += 2
        elif input_type == InputType.LEFT:
            # Select left zones (0 or 2)
            if self.selected_zone % 2 == 1:
                self.selected_zone -= 1
        elif input_type == InputType.RIGHT:
            # Select right zones (1 or 3)
            if self.selected_zone % 2 == 0:
                self.selected_zone += 1
        elif input_type == InputType.SELECT:
            # Drain selected zone
            self.apply_drain_to_zone(self.selected_zone)

        # Check for spacebar drain (in addition to SELECT button)
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)
            if key and key.code == self.input_handler.term.KEY_ENTER or (key and key == ' '):
                self.apply_drain_to_zone(self.selected_zone)

    def update(self, dt: float):
        """Update game state."""
        # Update lattice waves
        self.update_lattice(dt)

        # Update zone manager
        self.zone_manager.update(dt)

        # Calculate zone energies
        self.zone_manager.calculate_zone_energies(self.current)

        # Update scoring
        self.update_scoring(dt)

    def run(self):
        """Main game loop."""
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            last_time = time.time()
            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                self.draw()
                self.update(dt)
                self.handle_input()

                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()


def run_pattern_flux():
    """Entry point for Pattern Matching Flux Control game."""
    game = PatternFluxControl()
    game.run()


if __name__ == '__main__':
    run_pattern_flux()
