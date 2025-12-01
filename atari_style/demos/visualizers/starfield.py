"""Enhanced starfield demo with parallax, nebulae, warp tunnel, and asteroids."""

import random
import time
import math
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType


class Star:
    """Represents a star in 3D space."""

    def __init__(self, width: int, height: int, layer=0):
        self.x = random.uniform(-width, width)
        self.y = random.uniform(-height, height)
        self.z = random.uniform(1, width)
        self.layer = layer  # 0=far, 1=mid, 2=near

    def update(self, speed: float, width: int, height: int, lateral_drift=0):
        """Update star position."""
        # Layer-based speed multiplier for parallax
        layer_speed = [0.3, 0.7, 1.0][self.layer]

        self.z -= speed * layer_speed
        self.x += lateral_drift * layer_speed

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


class Nebula:
    """Represents a nebula cloud."""

    def __init__(self, width, height):
        self.x = random.uniform(-width * 2, width * 2)
        self.y = random.uniform(-height * 2, height * 2)
        self.z = random.uniform(width * 0.5, width * 2)
        self.size = random.uniform(30, 80)
        self.color = random.choice([
            Color.RED, Color.MAGENTA, Color.BLUE,
            Color.CYAN, Color.GREEN
        ])
        self.density_char = random.choice(['░', '▒'])

    def update(self, speed, width, height):
        """Update nebula position."""
        self.z -= speed * 0.2  # Slower than stars (background)

        if self.z <= 0:
            self.x = random.uniform(-width * 2, width * 2)
            self.y = random.uniform(-height * 2, height * 2)
            self.z = width * 2

    def render(self, renderer, width, height):
        """Render nebula cloud."""
        # Project center
        k = 128 / self.z if self.z > 0 else 0
        cx = int(self.x * k + width / 2)
        cy = int(self.y * k * 0.5 + height / 2)
        size = int(self.size * k)

        # Draw cloud using Perlin-noise-like distribution
        for dy in range(-size, size):
            for dx in range(-size, size):
                dist = math.sqrt(dx**2 + dy**2)
                if dist < size:
                    # Density falloff from center
                    if random.random() < (1 - dist / size) * 0.3:
                        px, py = cx + dx, cy + dy
                        if 0 <= px < width and 0 <= py < height:
                            renderer.set_pixel(px, py, self.density_char, self.color)


class Asteroid:
    """Represents an asteroid."""

    SHAPES = ['◊', '◇', '◆', '⬖', '⬗']

    def __init__(self, width, height):
        self.x = random.uniform(-width, width)
        self.y = random.uniform(-height, height)
        self.z = random.uniform(1, width)
        self.shape_idx = random.randint(0, len(self.SHAPES) - 1)
        self.rotation = 0

    def update(self, speed, width, height):
        """Update asteroid position."""
        self.z -= speed
        self.rotation += 0.1

        if self.z <= 0:
            self.x = random.uniform(-width, width)
            self.y = random.uniform(-height, height)
            self.z = width

    def project(self, width, height):
        """Project 3D position to 2D."""
        k = 128 / self.z
        x = int(self.x * k + width / 2)
        y = int(self.y * k * 0.5 + height / 2)
        return x, y, k

    def get_char(self):
        """Get character based on rotation."""
        idx = int(self.rotation) % len(self.SHAPES)
        return self.SHAPES[idx]


class StarfieldDemo:
    """Enhanced interactive starfield demo."""

    # Modes
    MODE_STARS = 0
    MODE_ASTEROIDS = 1

    # Hyperspace states
    HS_NONE = 0
    HS_PAUSE = 1
    HS_FLASH = 2
    HS_BURST = 3
    HS_RESUME = 4

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True

        # Animation parameters
        self.base_speed = 2.0
        self.warp_speed = 1.0
        self.lateral_drift = 0.0  # X-axis drift
        self.color_mode = 0  # 0: white, 1: rainbow, 2: speed-based

        # Mode
        self.mode = self.MODE_STARS

        # Parallax layers
        self.stars = []
        self._init_stars()

        # Nebulae
        self.nebulae = []
        self.nebulae_visible = True
        for _ in range(5):
            self.nebulae.append(Nebula(self.renderer.width, self.renderer.height))

        # Asteroids
        self.asteroids = []
        for _ in range(100):
            self.asteroids.append(Asteroid(self.renderer.width, self.renderer.height))

        # Warp tunnel
        self.warp_tunnel_active = False

        # Hyperspace jump
        self.hyperspace_state = self.HS_NONE
        self.hyperspace_timer = 0

        # Frame timing
        self.last_time = time.time()

    def _init_stars(self):
        """Initialize stars with parallax layers."""
        self.stars = []

        # Far layer (30% of stars, dim, slow)
        for _ in range(60):
            star = Star(self.renderer.width, self.renderer.height, layer=0)
            self.stars.append(star)

        # Mid layer (40% of stars, medium)
        for _ in range(80):
            star = Star(self.renderer.width, self.renderer.height, layer=1)
            self.stars.append(star)

        # Near layer (30% of stars, bright, fast)
        for _ in range(60):
            star = Star(self.renderer.width, self.renderer.height, layer=2)
            self.stars.append(star)

    def get_star_color(self, star: Star, depth: float) -> str:
        """Determine star color based on mode and layer."""
        # Layer-based dimming
        layer_colors = {
            0: [Color.BLUE, Color.CYAN, Color.WHITE],  # Far = dim
            1: [Color.CYAN, Color.WHITE, Color.BRIGHT_WHITE],  # Mid
            2: [Color.WHITE, Color.BRIGHT_WHITE, Color.BRIGHT_CYAN],  # Near = bright
        }

        if self.color_mode == 0:
            # Monochrome with layer-based brightness
            colors = layer_colors.get(star.layer, [Color.WHITE])
            if depth > 2:
                return colors[2] if len(colors) > 2 else colors[-1]
            elif depth > 1:
                return colors[1] if len(colors) > 1 else colors[0]
            else:
                return colors[0]

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

    def get_star_char(self, depth: float, layer: int) -> str:
        """Get character to draw based on star depth and layer."""
        # Layer affects brightness
        if layer == 0:  # Far
            return '.' if depth > 1 else '·'
        elif layer == 1:  # Mid
            return '●' if depth > 2 else '·'
        else:  # Near
            if depth > 3:
                return '█'
            elif depth > 2:
                return '●'
            else:
                return '·'

    def draw(self):
        """Render the starfield."""
        self.renderer.clear_buffer()

        # Hyperspace flash
        if self.hyperspace_state == self.HS_FLASH:
            # White screen flash
            for y in range(self.renderer.height):
                for x in range(self.renderer.width):
                    self.renderer.set_pixel(x, y, '█', Color.BRIGHT_WHITE)
            self.renderer.render()
            return

        # Draw nebulae (background layer)
        if self.nebulae_visible and self.mode == self.MODE_STARS:
            for nebula in self.nebulae:
                nebula.render(self.renderer, self.renderer.width, self.renderer.height)

        # Draw stars or asteroids
        if self.mode == self.MODE_STARS:
            self._draw_stars()
        else:
            self._draw_asteroids()

        # Draw HUD
        self._draw_hud()

        self.renderer.render()

    def _draw_stars(self):
        """Draw starfield with parallax and effects."""
        # Warp tunnel effect at high speed
        if self.warp_speed > 3.0 and not self.warp_tunnel_active:
            self.warp_tunnel_active = True
        elif self.warp_speed <= 3.0 and self.warp_tunnel_active:
            self.warp_tunnel_active = False

        for star in self.stars:
            x, y, depth = star.project(self.renderer.width, self.renderer.height)

            # Warp tunnel: arrange stars into tunnel walls
            if self.warp_tunnel_active:
                # Radial arrangement
                cx, cy = self.renderer.width / 2, self.renderer.height / 2
                dx, dy = x - cx, y - cy
                dist = math.sqrt(dx**2 + dy**2)

                if dist > 0:
                    # Push stars outward to tunnel walls
                    tunnel_radius = 20 + depth * 5
                    x = int(cx + (dx / dist) * tunnel_radius)
                    y = int(cy + (dy / dist) * tunnel_radius * 0.5)  # Aspect correction

            if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                char = self.get_star_char(depth, star.layer)
                color = self.get_star_color(star, depth)

                # Draw motion trails at high speed (streaking effect)
                if self.warp_speed > 2.5:
                    trail_length = int(self.warp_speed * (1 + star.layer * 0.5))

                    if self.warp_tunnel_active:
                        # Radial streaks in tunnel mode
                        cx, cy = self.renderer.width / 2, self.renderer.height / 2
                        for i in range(1, trail_length):
                            tx = int(x + (cx - x) * i / trail_length)
                            ty = int(y + (cy - y) * i / trail_length)
                            if 0 <= tx < self.renderer.width and 0 <= ty < self.renderer.height:
                                self.renderer.set_pixel(tx, ty, '-', color)
                    else:
                        # Horizontal trails in normal mode
                        for i in range(trail_length):
                            trail_x = x - i
                            if 0 <= trail_x < self.renderer.width:
                                self.renderer.set_pixel(trail_x, y, '-', color)

                self.renderer.set_pixel(x, y, char, color)

        # Hyperspace burst effect
        if self.hyperspace_state == self.HS_BURST:
            self._draw_hyperspace_burst()

    def _draw_asteroids(self):
        """Draw asteroid field."""
        for asteroid in self.asteroids:
            x, y, depth = asteroid.project(self.renderer.width, self.renderer.height)

            if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                char = asteroid.get_char()

                # Size varies with depth
                if depth > 2:
                    color = Color.BRIGHT_WHITE
                elif depth > 1:
                    color = Color.WHITE
                else:
                    color = Color.CYAN

                # Draw 3x3 cluster for larger asteroids
                if depth > 2.5:
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            px, py = x + dx, y + dy
                            if 0 <= px < self.renderer.width and 0 <= py < self.renderer.height:
                                self.renderer.set_pixel(px, py, char, color)
                else:
                    self.renderer.set_pixel(x, y, char, color)

    def _draw_hyperspace_burst(self):
        """Draw hyperspace burst animation."""
        # Stars burst outward from center
        cx, cy = self.renderer.width / 2, self.renderer.height / 2

        for star in self.stars:
            # Project normally
            x, y, depth = star.project(self.renderer.width, self.renderer.height)

            # Then push radially outward
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx**2 + dy**2)

            if dist > 0:
                burst_factor = 3
                x = int(cx + (dx / dist) * dist * burst_factor)
                y = int(cy + (dy / dist) * dist * burst_factor)

                if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                    self.renderer.set_pixel(x, y, '*', Color.BRIGHT_CYAN)

    def _draw_hud(self):
        """Draw heads-up display."""
        hud_y = 1

        # Speed
        self.renderer.draw_text(2, hud_y, f"Speed: {self.warp_speed:.1f}x", Color.YELLOW)

        # Mode
        mode_name = "Stars" if self.mode == self.MODE_STARS else "Asteroids"
        self.renderer.draw_text(2, hud_y + 1, f"Mode: {mode_name}", Color.YELLOW)

        # Color mode
        color_mode_names = ["Monochrome", "Rainbow", "Speed-based"]
        self.renderer.draw_text(2, hud_y + 2, f"Color: {color_mode_names[self.color_mode]}", Color.YELLOW)

        # Effects
        effects = []
        if self.warp_tunnel_active:
            effects.append("WARP TUNNEL")
        if not self.nebulae_visible and self.mode == self.MODE_STARS:
            effects.append("Nebula: OFF")

        if effects:
            self.renderer.draw_text(2, hud_y + 3, " | ".join(effects), Color.BRIGHT_CYAN)

        # Controls
        controls = [
            "Controls:",
            "Y-axis: Speed",
            "X-axis: Drift",
            "Btn 2: Toggle Mode",
            "Btn 3: Nebula",
            "Btn 4: Hyperspace",
            "Space: Color",
            "ESC: Exit"
        ]
        for i, text in enumerate(controls):
            self.renderer.draw_text(self.renderer.width - 20, hud_y + i, text, Color.CYAN)

    def update(self, dt):
        """Update starfield animation."""
        # Update hyperspace sequence
        if self.hyperspace_state != self.HS_NONE:
            self._update_hyperspace(dt)
            return

        # Update stars/asteroids
        if self.mode == self.MODE_STARS:
            for star in self.stars:
                star.update(self.base_speed * self.warp_speed,
                            self.renderer.width, self.renderer.height,
                            self.lateral_drift)

            # Update nebulae
            if self.nebulae_visible:
                for nebula in self.nebulae:
                    nebula.update(self.base_speed * self.warp_speed,
                                  self.renderer.width, self.renderer.height)
        else:
            for asteroid in self.asteroids:
                asteroid.update(self.base_speed * self.warp_speed,
                                self.renderer.width, self.renderer.height)

    def _update_hyperspace(self, dt):
        """Update hyperspace jump sequence."""
        self.hyperspace_timer += dt

        if self.hyperspace_state == self.HS_PAUSE:
            if self.hyperspace_timer >= 0.5:
                self.hyperspace_state = self.HS_FLASH
                self.hyperspace_timer = 0

        elif self.hyperspace_state == self.HS_FLASH:
            if self.hyperspace_timer >= 0.2:
                self.hyperspace_state = self.HS_BURST
                self.hyperspace_timer = 0

        elif self.hyperspace_state == self.HS_BURST:
            if self.hyperspace_timer >= 0.5:
                self.hyperspace_state = self.HS_RESUME
                self.hyperspace_timer = 0

                # Randomize nebulae (new region)
                self.nebulae = []
                for _ in range(5):
                    self.nebulae.append(Nebula(self.renderer.width, self.renderer.height))

        elif self.hyperspace_state == self.HS_RESUME:
            self.hyperspace_state = self.HS_NONE
            self.hyperspace_timer = 0

    def handle_input(self, dt):
        """Handle user input to control parameters."""
        input_type = self.input_handler.get_input(timeout=0.001)

        # Toggle color mode
        if input_type == InputType.SELECT:
            self.color_mode = (self.color_mode + 1) % 3
            time.sleep(0.2)  # Debounce

        # Exit
        if input_type == InputType.QUIT or input_type == InputType.BACK:
            self.running = False

        # Check joystick for analog control
        jx, jy = self.input_handler.get_joystick_state()

        if abs(jy) > 0.1:
            # Vertical axis controls speed
            self.warp_speed = max(0.1, min(5.0, self.warp_speed - jy * 0.1))

        if abs(jx) > 0.1:
            # Horizontal axis controls lateral drift
            self.lateral_drift = jx * 10

        # Check buttons
        buttons = self.input_handler.get_joystick_buttons()

        # Button 2: Toggle asteroid mode
        if buttons.get(1):
            time.sleep(0.2)
            self.mode = self.MODE_ASTEROIDS if self.mode == self.MODE_STARS else self.MODE_STARS

        # Button 3: Toggle nebula
        if buttons.get(2):
            time.sleep(0.2)
            self.nebulae_visible = not self.nebulae_visible

        # Button 4: Hyperspace jump
        if buttons.get(3):
            if self.hyperspace_state == self.HS_NONE:
                self.hyperspace_state = self.HS_PAUSE
                self.hyperspace_timer = 0
            time.sleep(0.2)

        # Keyboard controls
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)

            if key:
                if key.name == 'KEY_UP' or key.lower() == 'w':
                    self.warp_speed = min(5.0, self.warp_speed + 0.1)
                elif key.name == 'KEY_DOWN' or key.lower() == 's':
                    self.warp_speed = max(0.1, self.warp_speed - 0.1)
                elif key.name == 'KEY_LEFT' or key.lower() == 'a':
                    self.lateral_drift = -10
                elif key.name == 'KEY_RIGHT' or key.lower() == 'd':
                    self.lateral_drift = 10
                elif key.lower() == 'm':
                    self.mode = self.MODE_ASTEROIDS if self.mode == self.MODE_STARS else self.MODE_STARS
                elif key.lower() == 'n':
                    self.nebulae_visible = not self.nebulae_visible
                elif key.lower() == 'h':
                    if self.hyperspace_state == self.HS_NONE:
                        self.hyperspace_state = self.HS_PAUSE
                        self.hyperspace_timer = 0

        # Decay drift
        self.lateral_drift *= 0.9

    def run(self):
        """Run the starfield demo."""
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            while self.running:
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time

                # Cap dt
                dt = min(dt, 0.1)

                self.draw()
                self.update(dt)
                self.handle_input(dt)

                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_starfield():
    """Entry point for starfield demo."""
    demo = StarfieldDemo()
    demo.run()
