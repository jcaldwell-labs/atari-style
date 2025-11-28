"""Flux Showcase - Visually stunning fluid dynamics demo."""

import time
import math
from ..core.renderer import Renderer, Color
from .flux_control_zen import FluidLattice


# Rainbow color cycle
RAINBOW = [
    Color.RED, Color.BRIGHT_RED,
    Color.YELLOW, Color.BRIGHT_YELLOW,
    Color.GREEN, Color.BRIGHT_GREEN,
    Color.CYAN, Color.BRIGHT_CYAN,
    Color.BLUE, Color.BRIGHT_BLUE,
    Color.MAGENTA, Color.BRIGHT_MAGENTA,
]

# Heat map (low to high energy)
HEAT_MAP = [
    Color.BLUE, Color.CYAN, Color.GREEN,
    Color.YELLOW, Color.RED, Color.BRIGHT_RED,
    Color.BRIGHT_MAGENTA, Color.BRIGHT_WHITE,
]

# Ocean theme - smooth deep sea vibes
OCEAN = [
    Color.BLUE, Color.BLUE, Color.BLUE,
    Color.CYAN, Color.CYAN, Color.BRIGHT_CYAN,
    Color.BRIGHT_CYAN, Color.BRIGHT_WHITE,
]

# Fire theme
FIRE = [
    Color.RED, Color.BRIGHT_RED, Color.YELLOW,
    Color.BRIGHT_YELLOW, Color.BRIGHT_WHITE,
]

# Desert theme - warm sandy dunes
DESERT = [
    Color.RED, Color.YELLOW, Color.YELLOW,
    Color.BRIGHT_YELLOW, Color.BRIGHT_YELLOW,
    Color.WHITE, Color.BRIGHT_WHITE,
]

# Sunset theme - golden hour vibes
SUNSET = [
    Color.RED, Color.RED, Color.BRIGHT_RED,
    Color.YELLOW, Color.BRIGHT_YELLOW,
    Color.MAGENTA, Color.BRIGHT_MAGENTA,
]

# Characters for different intensities
CHARS_DENSE = ' ·∘○◎●◉█'
CHARS_WAVE = ' ~≈≋∿⌇░▒▓█'
CHARS_DOTS = ' ·••●●◉◉█'


class FluxShowcase:
    """Showcase fluid dynamics with stunning visuals."""

    def __init__(self):
        self.renderer = Renderer()
        self.width = self.renderer.width
        self.height = self.renderer.height - 2  # Leave room for status
        self.fluid = FluidLattice(self.width, self.height)

        # Proven stable parameters from capture session
        self.wave_speed = 0.45
        self.damping = 0.77
        self.rain_rate = 1.0  # Moderate rate - we control rain ourselves

        # Visual settings
        self.color_mode = 'rainbow'  # rainbow, heat, ocean, fire, wave
        self.char_set = CHARS_DENSE
        self.time_offset = 0.0
        self.color_speed = 0.5  # Color cycle speed
        self.wave_frequency = 0.1  # For wave mode

        # Drain timer to prevent saturation
        self.last_drain_time = 0.0
        self.drain_interval = 3.0  # Drain every 3 seconds

        # Apply parameters
        self.fluid.wave_speed = self.wave_speed
        self.fluid.damping = self.damping
        self.fluid.rain_rate = 0.5  # Use built-in rain at low rate

    def get_color_rainbow(self, x, y, energy, t):
        """Rainbow colors cycling over time with position offset."""
        # Combine time and position for flowing rainbow effect
        phase = (t * self.color_speed + x * 0.02 + y * 0.015) % 1.0
        idx = int(phase * len(RAINBOW)) % len(RAINBOW)
        return RAINBOW[idx]

    def get_color_heat(self, energy):
        """Heat map based on energy level."""
        idx = min(int(energy * len(HEAT_MAP) * 2), len(HEAT_MAP) - 1)
        return HEAT_MAP[idx]

    def get_color_ocean(self, x, y, energy, t):
        """Ocean waves with depth."""
        # Wave pattern based on position and time
        wave = math.sin(x * 0.1 + t * 2) * math.cos(y * 0.08 + t * 1.5)
        combined = (energy + wave * 0.3 + 0.3) / 1.6
        idx = min(int(combined * len(OCEAN)), len(OCEAN) - 1)
        return OCEAN[max(0, idx)]

    def get_color_fire(self, x, y, energy, t):
        """Fire effect rising from bottom."""
        # Energy rises and flickers
        flicker = math.sin(x * 0.3 + t * 8) * 0.1
        rise = (self.height - y) / self.height * 0.2
        combined = min(1.0, energy + flicker + rise)
        idx = min(int(combined * len(FIRE) * 1.5), len(FIRE) - 1)
        return FIRE[max(0, idx)]

    def get_color_wave(self, x, y, energy, t):
        """Concentric wave colors from center."""
        cx, cy = self.width // 2, self.height // 2
        dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        phase = (dist * self.wave_frequency - t * 2) % 1.0
        idx = int(phase * len(RAINBOW)) % len(RAINBOW)
        return RAINBOW[idx]

    def get_color_desert(self, x, y, energy, t):
        """Desert dunes - warm sandy waves."""
        # Slow rolling dune effect
        dune = math.sin(x * 0.05 + t * 0.5) * math.sin(y * 0.03 + t * 0.3)
        combined = (energy + dune * 0.2 + 0.3) / 1.5
        idx = min(int(combined * len(DESERT)), len(DESERT) - 1)
        return DESERT[max(0, idx)]

    def get_color_sunset(self, x, y, energy, t):
        """Sunset - golden hour glow."""
        # Gradient from top to bottom with shimmer
        gradient = y / self.height
        shimmer = math.sin(x * 0.1 + t * 3) * 0.1
        combined = (energy * 0.7 + gradient * 0.3 + shimmer)
        idx = min(int(combined * len(SUNSET) * 1.2), len(SUNSET) - 1)
        return SUNSET[max(0, idx)]

    def get_char_and_color(self, x, y, energy, t):
        """Get character and color for a cell."""
        if energy < 0.02:
            return ' ', Color.WHITE

        # Character based on energy
        char_idx = min(int(energy * len(self.char_set) * 1.5), len(self.char_set) - 1)
        char = self.char_set[max(0, char_idx)]

        # Color based on mode
        if self.color_mode == 'rainbow':
            color = self.get_color_rainbow(x, y, energy, t)
        elif self.color_mode == 'heat':
            color = self.get_color_heat(energy)
        elif self.color_mode == 'ocean':
            color = self.get_color_ocean(x, y, energy, t)
        elif self.color_mode == 'fire':
            color = self.get_color_fire(x, y, energy, t)
        elif self.color_mode == 'wave':
            color = self.get_color_wave(x, y, energy, t)
        elif self.color_mode == 'desert':
            color = self.get_color_desert(x, y, energy, t)
        elif self.color_mode == 'sunset':
            color = self.get_color_sunset(x, y, energy, t)
        else:
            color = Color.CYAN

        return char, color

    def update(self, dt):
        """Update simulation."""
        self.time_offset += dt

        # Auto-drain to prevent saturation (only when above sweet spot)
        coverage = self.fluid.get_coverage_percent()
        if coverage > 70:
            # Drain when getting too full
            self.fluid.drain_global(0.2)
        elif coverage > 55 and self.time_offset - self.last_drain_time > self.drain_interval:
            # Periodic gentle drain to keep it interesting
            self.fluid.drain_global(0.1)
            self.last_drain_time = self.time_offset

        # Update simulation (built-in rain handles drops)
        self.fluid.update(dt)

    def draw(self, show_ui=True):
        """Render the fluid."""
        self.renderer.clear_buffer()
        t = self.time_offset

        # Draw fluid
        for y in range(self.height):
            for x in range(self.width):
                # Access fluid grid directly - normalize to 0-1 range
                raw_value = abs(self.fluid.current[y][x])
                energy = min(1.0, raw_value / 10.0)  # Normalize (max ~10)
                char, color = self.get_char_and_color(x, y, energy, t)
                if char != ' ':
                    self.renderer.set_pixel(x, y, char, color)

        # Minimal status bar
        if show_ui:
            coverage = self.fluid.get_coverage_percent()
            mode_display = self.color_mode.upper()
            status = f" {mode_display} | Coverage: {coverage:.0f}% "
            self.renderer.draw_text(2, self.height, status, Color.BRIGHT_WHITE)

        self.renderer.render()


def run_flux_showcase(duration: int = 75):
    """Run the showcase demo with automatic mode cycling.

    Args:
        duration: Total duration in seconds (default 75s to avoid VHS issues)
    """
    showcase = FluxShowcase()
    showcase.renderer.enter_fullscreen()

    # Mode sequence - ocean & desert themed, smoother transitions
    modes = [
        ('ocean', CHARS_WAVE, 0.3),       # Deep ocean waves
        ('desert', CHARS_DENSE, 0.2),     # Sandy dunes
        ('sunset', CHARS_DOTS, 0.4),      # Golden hour glow
        ('rainbow', CHARS_WAVE, 0.6),     # Rainbow finale
        ('ocean', CHARS_DENSE, 0.5),      # Return to calm ocean
    ]
    mode_duration = duration / len(modes)

    try:
        start_time = time.time()
        last_time = start_time
        mode_idx = 0
        last_mode_change = start_time

        while time.time() - start_time < duration:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            elapsed = current_time - start_time

            # Change mode based on time
            new_mode_idx = min(int(elapsed / mode_duration), len(modes) - 1)
            if new_mode_idx != mode_idx:
                mode_idx = new_mode_idx
                mode, chars, speed = modes[mode_idx]
                showcase.color_mode = mode
                showcase.char_set = chars
                showcase.color_speed = speed
                last_mode_change = current_time

            showcase.update(dt)
            showcase.draw()
            time.sleep(0.05)  # 20 FPS - reduced for VHS compatibility

    finally:
        showcase.renderer.exit_fullscreen()


def run_flux_showcase_single(mode: str = 'rainbow', duration: int = 60):
    """Run showcase with a single color mode.

    Args:
        mode: One of 'rainbow', 'heat', 'ocean', 'fire', 'wave'
        duration: Duration in seconds
    """
    showcase = FluxShowcase()
    showcase.color_mode = mode
    showcase.renderer.enter_fullscreen()

    try:
        start_time = time.time()
        last_time = start_time

        while time.time() - start_time < duration:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            showcase.update(dt)
            showcase.draw()
            time.sleep(0.016)

    finally:
        showcase.renderer.exit_fullscreen()


if __name__ == "__main__":
    run_flux_showcase(180)
