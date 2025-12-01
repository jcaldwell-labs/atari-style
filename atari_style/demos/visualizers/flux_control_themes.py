"""Reactor Core themed UI overlay for Flux Control game.

Usage Example with Flux Control Game:
-------------------------------------

from atari_style.demos.flux_control_themes import ReactorTheme

class FluxControl:
    def __init__(self):
        self.renderer = Renderer()
        self.theme = ReactorTheme()  # Optional theme
        self.energy = 50.0
        self.threshold = 75.0
        self.cooldown = 0.0
        self.score = 0
        self.game_over = False
        self.meltdown_frame = 0

    def draw(self):
        self.renderer.clear_buffer()

        if self.game_over:
            # Draw meltdown animation
            continue_animation = self.theme.draw_meltdown(
                self.renderer, self.meltdown_frame
            )
            if continue_animation:
                self.meltdown_frame += 1
        else:
            # Draw game HUD with reactor theme
            self.theme.draw_hud(
                self.renderer,
                self.energy,
                self.threshold,
                self.cooldown,
                self.score
            )

            # Draw warning overlay for high energy
            self.theme.draw_warning(self.renderer, self.energy)

            # Draw your game elements here
            # ... player, enemies, etc ...

        self.renderer.render()

    def game_over_sequence(self):
        self.game_over = True
        self.meltdown_frame = 0
"""

import math
import time
from typing import Optional
from ...core.renderer import Renderer, Color


class ReactorTheme:
    """Reactor Core theme with temperature gauges, warnings, and meltdown animations."""

    def __init__(self):
        """Initialize the reactor theme."""
        self.last_warning_flash = 0
        self.meltdown_start_time = None
        self.radiation_chars = ['☢', '⚠']
        self.temp_bars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

    def get_energy_color(self, energy_percent: float) -> str:
        """Return color based on energy level percentage.

        Args:
            energy_percent: Energy level as percentage (0-100)

        Returns:
            Color constant from renderer.Color
        """
        if energy_percent < 40:
            return Color.CYAN  # Normal - cool
        elif energy_percent < 60:
            return Color.BRIGHT_CYAN  # Warming up
        elif energy_percent < 75:
            return Color.YELLOW  # Warning - hot
        elif energy_percent < 90:
            return Color.BRIGHT_YELLOW  # High temperature
        elif energy_percent < 95:
            return Color.RED  # Critical
        else:
            return Color.BRIGHT_RED  # Meltdown imminent

    def _draw_temperature_gauge(self, renderer: Renderer, x: int, y: int,
                                energy_percent: float, width: int = 30):
        """Draw a horizontal temperature gauge with gradient bars.

        Args:
            renderer: Renderer instance
            x: X position
            y: Y position
            energy_percent: Energy level as percentage (0-100)
            width: Width of the gauge in characters
        """
        # Calculate filled length
        filled = int((energy_percent / 100) * width)

        # Draw gauge border
        renderer.set_pixel(x - 1, y, '[', Color.CYAN)
        renderer.set_pixel(x + width, y, ']', Color.CYAN)

        # Draw filled portion with gradient
        for i in range(width):
            if i < filled:
                # Use temperature bars for filled section
                bar_char = self.temp_bars[-1]  # Full block for filled
                color = self.get_energy_color((i / width) * 100)
                renderer.set_pixel(x + i, y, bar_char, color)
            else:
                # Empty section
                renderer.set_pixel(x + i, y, '░', Color.BLUE)

    def _draw_temperature_value(self, renderer: Renderer, x: int, y: int,
                                energy_percent: float):
        """Draw temperature in degrees Celsius.

        Temperature scales from 20°C (0%) to 3000°C (100%)

        Args:
            renderer: Renderer instance
            x: X position
            y: Y position
            energy_percent: Energy level as percentage (0-100)
        """
        temp_c = int(20 + (energy_percent / 100) * 2980)  # 20-3000°C range
        temp_text = f"CORE TEMP: {temp_c:4d}°C"
        color = self.get_energy_color(energy_percent)
        renderer.draw_text(x, y, temp_text, color)

    def _draw_containment_status(self, renderer: Renderer, x: int, y: int,
                                 energy_percent: float):
        """Draw containment field status indicator.

        Args:
            renderer: Renderer instance
            x: X position
            y: Y position
            energy_percent: Energy level as percentage (0-100)
        """
        if energy_percent < 75:
            status = "STABLE  "
            color = Color.BRIGHT_GREEN
            indicator = "●"
        elif energy_percent < 90:
            status = "WARNING "
            color = Color.BRIGHT_YELLOW
            indicator = "◐"
        else:
            status = "CRITICAL"
            color = Color.BRIGHT_RED
            indicator = "○"

        renderer.draw_text(x, y, "CONTAINMENT: ", Color.CYAN)
        renderer.draw_text(x + 13, y, status, color)
        renderer.draw_text(x + 22, y, indicator, color)

    def _draw_control_rod_status(self, renderer: Renderer, x: int, y: int,
                                 cooldown: float):
        """Draw control rod status (READY/COOLING DOWN).

        Args:
            renderer: Renderer instance
            x: X position
            y: Y position
            cooldown: Cooldown timer in seconds
        """
        renderer.draw_text(x, y, "CONTROL RODS: ", Color.CYAN)

        if cooldown > 0:
            status = f"COOLING [{cooldown:.1f}s]"
            color = Color.YELLOW
        else:
            status = "READY         "
            color = Color.BRIGHT_GREEN

        renderer.draw_text(x + 14, y, status, color)

    def _draw_radiation_warnings(self, renderer: Renderer, energy_percent: float):
        """Draw radiation warning symbols when energy is high.

        Args:
            renderer: Renderer instance
            energy_percent: Energy level as percentage (0-100)
        """
        if energy_percent < 75:
            return  # No warnings below 75%

        # Flash radiation symbols
        current_time = time.time()
        flash_on = int(current_time * 3) % 2 == 0  # Flash at 3Hz

        if not flash_on and energy_percent < 90:
            return  # Only flash for warning level

        # Position warnings at corners
        width = renderer.width
        height = renderer.height

        positions = [
            (2, 2),           # Top left
            (width - 4, 2),   # Top right
            (2, height - 3),  # Bottom left
            (width - 4, height - 3)  # Bottom right
        ]

        color = Color.BRIGHT_YELLOW if energy_percent < 90 else Color.BRIGHT_RED
        symbol = self.radiation_chars[0]  # ☢

        for px, py in positions:
            renderer.draw_text(px, py, symbol, color)
            if energy_percent >= 90:
                # Add extra warning symbols
                renderer.draw_text(px + 2, py, self.radiation_chars[1], color)  # ⚠

    def draw_hud(self, renderer: Renderer, energy: float, threshold: float,
                 cooldown: float, score: int):
        """Draw the reactor-themed HUD.

        Args:
            renderer: Renderer instance
            energy: Current energy level (0-100)
            threshold: Energy threshold value (not used in display)
            cooldown: Cooldown timer in seconds
            score: Current score
        """
        width = renderer.width
        height = renderer.height

        # Header
        header = "═══ REACTOR CORE STATUS ═══"
        header_x = (width - len(header)) // 2
        renderer.draw_text(header_x, 0, header, Color.BRIGHT_CYAN)

        # Temperature gauge (centered)
        gauge_y = 2
        gauge_width = 40
        gauge_x = (width - gauge_width) // 2
        self._draw_temperature_gauge(renderer, gauge_x, gauge_y, energy, gauge_width)

        # Temperature value
        temp_y = 4
        temp_text_width = 22  # "CORE TEMP: XXXX°C"
        temp_x = (width - temp_text_width) // 2
        self._draw_temperature_value(renderer, temp_x, temp_y, energy)

        # Containment status
        containment_y = 6
        containment_width = 24
        containment_x = (width - containment_width) // 2
        self._draw_containment_status(renderer, containment_x, containment_y, energy)

        # Control rod status
        rod_y = 8
        rod_width = 30
        rod_x = (width - rod_width) // 2
        self._draw_control_rod_status(renderer, rod_x, rod_y, cooldown)

        # Score
        score_y = height - 2
        score_text = f"REACTOR OUTPUT: {score:08d} MW"
        score_x = (width - len(score_text)) // 2
        renderer.draw_text(score_x, score_y, score_text, Color.BRIGHT_WHITE)

        # Radiation warnings for high energy
        self._draw_radiation_warnings(renderer, energy)

    def draw_warning(self, renderer: Renderer, energy_percent: float):
        """Draw warning effects when energy is in danger zone.

        Args:
            renderer: Renderer instance
            energy_percent: Energy level as percentage (0-100)
        """
        if energy_percent < 75:
            return  # No warnings below 75%

        width = renderer.width
        height = renderer.height
        current_time = time.time()

        # Flash screen border
        flash_on = int(current_time * 4) % 2 == 0  # 4Hz flash for warnings

        if energy_percent >= 90:
            flash_on = int(current_time * 8) % 2 == 0  # 8Hz flash for critical

        if not flash_on:
            return

        # Determine warning level and color
        if energy_percent >= 90:
            color = Color.BRIGHT_RED
            char = '█'
            message = "!!! CRITICAL TEMPERATURE !!!"
        else:
            color = Color.BRIGHT_YELLOW
            char = '▓'
            message = "!! WARNING - HIGH TEMPERATURE !!"

        # Draw flashing border
        for x in range(width):
            renderer.set_pixel(x, 0, char, color)
            renderer.set_pixel(x, height - 1, char, color)

        for y in range(height):
            renderer.set_pixel(0, y, char, color)
            renderer.set_pixel(width - 1, y, char, color)

        # Draw warning message
        msg_x = (width - len(message)) // 2
        msg_y = height // 2
        renderer.draw_text(msg_x, msg_y, message, color)

    def draw_meltdown(self, renderer: Renderer, frame: int) -> bool:
        """Draw meltdown animation sequence.

        The animation has 4 phases over ~2 seconds (15 frames total at 30 FPS):
        - Frames 0-2: Pause and warning text (0.1s per frame)
        - Frames 3-5: Screen flash (0.1s per frame)
        - Frames 6-13: Radial burst from center (0.1s per frame)
        - Frame 14+: Final explosion state

        Args:
            renderer: Renderer instance
            frame: Animation frame number (0-based)

        Returns:
            True if animation should continue, False if complete
        """
        width = renderer.width
        height = renderer.height
        center_x = width // 2
        center_y = height // 2

        # Phase 1: Pause with warning (frames 0-2)
        if frame < 3:
            message = "!!! MELTDOWN !!!"
            msg_x = (width - len(message)) // 2
            msg_y = center_y

            # Alternate colors for flash effect
            color = Color.BRIGHT_RED if frame % 2 == 0 else Color.BRIGHT_WHITE
            renderer.draw_text(msg_x, msg_y, message, color)

            # Draw radiation symbols
            for i in range(4):
                angle = (i / 4) * 2 * math.pi
                offset = 15
                x = int(center_x + math.cos(angle) * offset)
                y = int(center_y + math.sin(angle) * offset * 0.5)  # Aspect ratio
                renderer.draw_text(x, y, self.radiation_chars[0], color)

            return True

        # Phase 2: Screen flash (frames 3-5)
        elif frame < 6:
            flash_char = '█' if frame % 2 == 0 else '▓'
            color = Color.BRIGHT_WHITE if frame % 2 == 0 else Color.BRIGHT_RED

            for y in range(height):
                for x in range(width):
                    if (x + y) % 2 == 0:
                        renderer.set_pixel(x, y, flash_char, color)

            # Meltdown text
            message = "MELTDOWN"
            msg_x = (width - len(message)) // 2
            renderer.draw_text(msg_x, center_y, message, Color.BRIGHT_YELLOW)

            return True

        # Phase 3: Radial burst (frames 6-13)
        elif frame < 14:
            burst_frame = frame - 6
            max_radius = max(width, height * 2)  # Account for aspect ratio
            current_radius = (burst_frame / 8) * max_radius

            # Draw expanding burst
            chars = ['░', '▒', '▓', '█']
            for y in range(height):
                for x in range(width):
                    # Calculate distance from center (with aspect ratio correction)
                    dx = x - center_x
                    dy = (y - center_y) * 2  # Aspect ratio correction
                    distance = math.sqrt(dx * dx + dy * dy)

                    # Draw if within burst radius
                    if distance < current_radius:
                        # Create wave effect
                        wave_offset = distance / 5
                        intensity = (current_radius - distance) / current_radius

                        # Select character based on intensity
                        char_idx = int(intensity * (len(chars) - 1))
                        char = chars[min(char_idx, len(chars) - 1)]

                        # Color based on distance
                        if distance < current_radius * 0.3:
                            color = Color.BRIGHT_WHITE
                        elif distance < current_radius * 0.6:
                            color = Color.BRIGHT_YELLOW
                        elif distance < current_radius * 0.8:
                            color = Color.BRIGHT_RED
                        else:
                            color = Color.RED

                        renderer.set_pixel(x, y, char, color)

            # Flashing meltdown text
            if burst_frame % 2 == 0:
                message = "!!! CORE BREACH !!!"
                msg_x = (width - len(message)) // 2
                renderer.draw_text(msg_x, center_y, message, Color.BRIGHT_WHITE)

            return True

        # Phase 4: Final explosion state (frame 14+)
        else:
            # Static final state - scattered radiation
            chars = ['☢', '⚠', '▓', '░', '*', '×', '+']

            # Use frame as seed for pseudo-random pattern
            for y in range(height):
                for x in range(width):
                    # Pseudo-random based on position
                    seed = (x * 7 + y * 13 + frame) % 100

                    if seed < 30:  # 30% coverage
                        char_idx = (x + y + frame) % len(chars)
                        char = chars[char_idx]

                        # Color based on position
                        if seed < 10:
                            color = Color.BRIGHT_RED
                        elif seed < 20:
                            color = Color.BRIGHT_YELLOW
                        else:
                            color = Color.RED

                        renderer.set_pixel(x, y, char, color)

            # Final message
            messages = [
                "REACTOR DESTROYED",
                "",
                "Radiation Level: FATAL",
                "Containment: FAILED"
            ]

            for i, msg in enumerate(messages):
                if msg:
                    msg_x = (width - len(msg)) // 2
                    msg_y = center_y - 2 + i
                    color = Color.BRIGHT_RED if i == 0 else Color.BRIGHT_YELLOW
                    renderer.draw_text(msg_x, msg_y, msg, color)

            # Animation complete after frame 20
            return frame < 20


def run_theme_demo():
    """Demo the reactor theme independently."""
    renderer = Renderer()
    theme = ReactorTheme()

    try:
        renderer.enter_fullscreen()

        # Demo sequence
        print("Reactor Theme Demo - Phase 1: Normal operation")

        # Normal operation (energy at 30%)
        for i in range(30):
            renderer.clear_buffer()
            energy = 30 + (i % 10)  # Slight fluctuation
            theme.draw_hud(renderer, energy, 50, 0, 1000 * i)
            renderer.render()
            time.sleep(0.1)

        print("\nPhase 2: Rising temperature")

        # Rising energy to warning level
        for i in range(50):
            renderer.clear_buffer()
            energy = 30 + (i * 0.8)  # Rise from 30% to 70%
            cooldown = max(0, 5 - i * 0.1)
            theme.draw_hud(renderer, energy, 50, cooldown, 3000 + i * 100)
            theme.draw_warning(renderer, energy)
            renderer.render()
            time.sleep(0.1)

        print("\nPhase 3: Critical temperature")

        # Critical level
        for i in range(30):
            renderer.clear_buffer()
            energy = 85 + (i % 5)  # Fluctuate around 87%
            theme.draw_hud(renderer, energy, 50, 0, 8000 + i * 50)
            theme.draw_warning(renderer, energy)
            renderer.render()
            time.sleep(0.1)

        print("\nPhase 4: MELTDOWN!")

        # Meltdown animation
        frame = 0
        while frame < 25:
            renderer.clear_buffer()
            theme.draw_meltdown(renderer, frame)
            renderer.render()
            time.sleep(0.1)
            frame += 1

        # Hold final state
        time.sleep(2)

    finally:
        renderer.exit_fullscreen()
        print("\nReactor Theme Demo Complete")


if __name__ == '__main__':
    run_theme_demo()
