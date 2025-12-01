"""Lissajous Game - Educational video + interactive game with Lissajous curves.

Features:
- L-shaped visualization (X circle top, Y circle left)
- Enemies following Lissajous paths
- Player with free movement (Galaga-style)
- Smooth-follow camera with pan/zoom/tilt
- Multiple view modes (top-down, chase cam, cockpit)
"""

import os
import math
import time
import random
import platform
import subprocess
from typing import Tuple, List, Optional, Generator
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


# ============================================================================
# COLOR DEFINITIONS
# ============================================================================

COLOR_RGB = {
    'red': (255, 85, 85),
    'green': (80, 250, 123),
    'yellow': (241, 250, 140),
    'blue': (98, 114, 164),
    'magenta': (255, 121, 198),
    'cyan': (139, 233, 253),
    'white': (248, 248, 242),
    'bright_red': (255, 110, 110),
    'bright_green': (105, 255, 148),
    'bright_yellow': (255, 255, 165),
    'bright_blue': (189, 147, 249),
    'bright_magenta': (255, 146, 218),
    'bright_cyan': (164, 255, 255),
    'bright_white': (255, 255, 255),
    'bg': (30, 32, 44),
    'grid': (60, 60, 80),
}


# ============================================================================
# LISSAJOUS PATTERNS (Enemy Types)
# ============================================================================

@dataclass
class LissajousPattern:
    """Definition of a Lissajous pattern for enemy movement."""
    name: str
    a: float  # X frequency
    b: float  # Y frequency
    delta: float  # Phase offset (radians)
    points: int  # Score value
    color: str  # Color name


ENEMY_PATTERNS = [
    LissajousPattern("Circler", 1.0, 1.0, math.pi/2, 10, 'cyan'),
    LissajousPattern("Figure-8", 1.0, 2.0, 0, 25, 'green'),
    LissajousPattern("Trefoil", 2.0, 3.0, 0, 50, 'yellow'),
    LissajousPattern("Star", 2.0, 5.0, 0, 100, 'magenta'),
    LissajousPattern("Pentagram", 3.0, 5.0, 0, 500, 'bright_red'),
]


# ============================================================================
# CORE CLASSES
# ============================================================================

class LissajousViz:
    """L-shaped Lissajous visualization with X circle (top) and Y circle (left)."""

    def __init__(self, freq_a: float = 3.0, freq_b: float = 2.0, phase: float = 0.0):
        self.a = freq_a
        self.b = freq_b
        self.delta = phase
        self.trail: List[Tuple[float, float]] = []
        self.max_trail = 500

    def get_point(self, t: float) -> Tuple[float, float]:
        """Get normalized (-1 to 1) point on Lissajous curve at time t."""
        x = math.sin(self.a * t + self.delta)
        y = math.sin(self.b * t)
        return (x, y)

    def update(self, t: float):
        """Update trail with new point."""
        point = self.get_point(t)
        self.trail.append(point)
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

    def draw_terminal(self, renderer: Renderer, t: float,
                      x_circle_cx: int, x_circle_cy: int,
                      y_circle_cx: int, y_circle_cy: int,
                      result_cx: int, result_cy: int,
                      radius: int):
        """Draw L-shaped visualization to terminal renderer."""
        # Get current point
        x_norm, y_norm = self.get_point(t)

        # X circle (horizontal at top)
        # Draw circle outline
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            px = x_circle_cx + int(radius * math.cos(rad))
            py = x_circle_cy + int(radius * 0.5 * math.sin(rad))  # Squash for terminal
            renderer.set_pixel(px, py, '·', Color.CYAN)

        # Rotating point on X circle
        x_angle = self.a * t + self.delta
        x_px = x_circle_cx + int(radius * math.cos(x_angle))
        x_py = x_circle_cy
        renderer.set_pixel(x_px, x_py, '●', Color.BRIGHT_YELLOW)

        # Y circle (vertical at left)
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            px = y_circle_cx + int(radius * 0.5 * math.cos(rad))
            py = y_circle_cy + int(radius * math.sin(rad))
            renderer.set_pixel(px, py, '·', Color.MAGENTA)

        # Rotating point on Y circle
        y_angle = self.b * t
        y_px = y_circle_cx
        y_py = y_circle_cy + int(radius * math.sin(y_angle))
        renderer.set_pixel(y_px, y_py, '●', Color.BRIGHT_YELLOW)

        # Result point
        result_x = result_cx + int(radius * x_norm)
        result_y = result_cy + int(radius * 0.5 * y_norm)  # Squash for terminal

        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            trail_x = result_cx + int(radius * tx)
            trail_y = result_cy + int(radius * 0.5 * ty)
            brightness = i / len(self.trail)
            if brightness > 0.8:
                char, color = '●', Color.BRIGHT_GREEN
            elif brightness > 0.5:
                char, color = '○', Color.GREEN
            else:
                char, color = '·', Color.BLUE
            renderer.set_pixel(trail_x, trail_y, char, color)

        # Current point (brightest)
        renderer.set_pixel(result_x, result_y, '█', Color.BRIGHT_WHITE)

        # Connection lines (dashed)
        # X to result (horizontal)
        step = 3
        for dx in range(0, abs(result_x - x_px), step):
            lx = x_px + (1 if result_x > x_px else -1) * dx
            if dx % (step * 2) < step:
                renderer.set_pixel(lx, result_y, '─', Color.CYAN)

        # Y to result (vertical)
        for dy in range(0, abs(result_y - y_py), step):
            ly = y_py + (1 if result_y > y_py else -1) * dy
            if dy % (step * 2) < step:
                renderer.set_pixel(result_x, ly, '│', Color.MAGENTA)


class LissajousEnemy:
    """Enemy that moves along a Lissajous path."""

    def __init__(self, pattern: LissajousPattern, center_x: float, center_y: float,
                 scale: float = 50.0, speed: float = 1.0, time_offset: float = 0.0):
        self.pattern = pattern
        self.center_x = center_x
        self.center_y = center_y
        self.scale = scale
        self.speed = speed
        self.t = time_offset
        self.active = True
        self.health = 1

        # Animation
        self.anim_frame = 0
        self.anim_timer = 0.0

    def update(self, dt: float):
        """Update enemy position."""
        self.t += self.speed * dt
        self.anim_timer += dt
        if self.anim_timer >= 0.2:
            self.anim_timer = 0
            self.anim_frame = 1 - self.anim_frame

    def get_position(self) -> Tuple[float, float]:
        """Get current world position."""
        x = math.sin(self.pattern.a * self.t + self.pattern.delta)
        y = math.sin(self.pattern.b * self.t)
        return (self.center_x + x * self.scale, self.center_y + y * self.scale)

    def get_char(self) -> str:
        """Get character for rendering."""
        chars = ['◊', '⋄']
        return chars[self.anim_frame]

    def get_color(self) -> str:
        """Get color for rendering."""
        return self.pattern.color


class Player:
    """Player ship with free movement."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.speed = 40.0
        self.fire_cooldown = 0.0
        self.fire_rate = 0.3
        self.lives = 3

    def update(self, dt: float):
        """Update player state."""
        self.fire_cooldown = max(0, self.fire_cooldown - dt)

    def move(self, dx: float, dy: float, dt: float, bounds: Tuple[float, float, float, float]):
        """Move player within bounds (min_x, min_y, max_x, max_y)."""
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        min_x, min_y, max_x, max_y = bounds
        self.x = max(min_x, min(self.x, max_x))
        self.y = max(min_y, min(self.y, max_y))

    def can_fire(self) -> bool:
        return self.fire_cooldown <= 0

    def fire(self):
        self.fire_cooldown = self.fire_rate


class Bullet:
    """Projectile from player or enemy."""

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 char: str = '|', color: str = Color.BRIGHT_WHITE):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.char = char
        self.color = color
        self.active = True

    def update(self, dt: float, bounds: Tuple[float, float, float, float]):
        """Update bullet position."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        min_x, min_y, max_x, max_y = bounds
        if not (min_x <= self.x <= max_x and min_y <= self.y <= max_y):
            self.active = False


class Missile:
    """Missile that spawns from viewport edge and travels toward target."""

    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float,
                 speed: float = 30.0):
        self.x = start_x
        self.y = start_y
        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.sqrt(dx*dx + dy*dy) or 1
        self.vx = dx / dist * speed
        self.vy = dy / dist * speed
        self.active = True

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt

    @staticmethod
    def spawn_from_edge(width: float, height: float, target_x: float, target_y: float,
                       speed: float = 30.0) -> 'Missile':
        """Spawn missile from random viewport edge."""
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            return Missile(random.uniform(0, width), 0, target_x, target_y, speed)
        elif edge == 'bottom':
            return Missile(random.uniform(0, width), height, target_x, target_y, speed)
        elif edge == 'left':
            return Missile(0, random.uniform(0, height), target_x, target_y, speed)
        else:
            return Missile(width, random.uniform(0, height), target_x, target_y, speed)


class Explosion:
    """Visual explosion effect."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.frame = 0
        self.max_frames = 6
        self.timer = 0.0

    def update(self, dt: float):
        self.timer += dt
        if self.timer >= 0.1:
            self.timer = 0
            self.frame += 1

    def is_active(self) -> bool:
        return self.frame < self.max_frames

    def get_char(self) -> str:
        frames = ['*', '+', '*', '+', '·', ' ']
        return frames[min(self.frame, len(frames) - 1)]


class GameCamera:
    """Camera with smooth follow, zoom, and tilt."""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        self.tilt = 0.0  # Rotation in radians
        self.follow_speed = 5.0

    def follow(self, target_x: float, target_y: float, dt: float):
        """Smooth follow target position."""
        self.x += (target_x - self.x) * self.follow_speed * dt
        self.y += (target_y - self.y) * self.follow_speed * dt

    def world_to_screen(self, wx: float, wy: float, screen_cx: int, screen_cy: int) -> Tuple[int, int]:
        """Transform world coordinates to screen coordinates."""
        # Translate to camera space
        x = wx - self.x
        y = wy - self.y

        # Apply tilt (rotation)
        if self.tilt != 0:
            cos_t = math.cos(self.tilt)
            sin_t = math.sin(self.tilt)
            x, y = x * cos_t - y * sin_t, x * sin_t + y * cos_t

        # Apply zoom
        x *= self.zoom
        y *= self.zoom

        # Offset to screen center
        return int(x + screen_cx), int(y + screen_cy)


# ============================================================================
# MAIN GAME CLASS
# ============================================================================

class LissajousGame:
    """Main game class combining all elements."""

    # View modes
    VIEW_TOPDOWN = 0
    VIEW_CHASE = 1
    VIEW_COCKPIT = 2

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.width = self.renderer.width
        self.height = self.renderer.height

        # Game state
        self.running = True
        self.paused = False
        self.score = 0
        self.wave = 1
        self.view_mode = self.VIEW_TOPDOWN

        # L-shaped visualization
        self.viz = LissajousViz(3.0, 2.0, 0)

        # Camera
        self.camera = GameCamera()

        # Player
        self.player = Player(self.width // 2, self.height - 10)

        # Game objects
        self.enemies: List[LissajousEnemy] = []
        self.bullets: List[Bullet] = []
        self.missiles: List[Missile] = []
        self.explosions: List[Explosion] = []

        # Spawn timers
        self.enemy_spawn_timer = 0.0
        self.missile_spawn_timer = 0.0

        # Time tracking
        self.t = 0.0

    def spawn_wave(self):
        """Spawn enemies for current wave."""
        self.enemies.clear()

        # Select patterns based on wave
        patterns_available = ENEMY_PATTERNS[:min(self.wave, len(ENEMY_PATTERNS))]

        # Number of enemies increases with wave
        num_enemies = 3 + self.wave * 2

        for i in range(num_enemies):
            pattern = random.choice(patterns_available)
            center_x = self.width // 2
            center_y = self.height // 2
            scale = 15 + random.uniform(-5, 5)
            speed = 0.5 + self.wave * 0.1
            offset = i * (math.pi * 2 / num_enemies)

            enemy = LissajousEnemy(pattern, center_x, center_y, scale, speed, offset)
            self.enemies.append(enemy)

    def check_collisions(self):
        """Check and handle collisions."""
        # Bullet-enemy collisions
        for bullet in self.bullets:
            if not bullet.active:
                continue
            for enemy in self.enemies:
                if not enemy.active:
                    continue
                ex, ey = enemy.get_position()
                dx = bullet.x - ex
                dy = bullet.y - ey
                if dx*dx + dy*dy < 4:  # Hit radius
                    bullet.active = False
                    enemy.health -= 1
                    if enemy.health <= 0:
                        enemy.active = False
                        self.score += enemy.pattern.points
                        self.explosions.append(Explosion(ex, ey))
                    break

        # Player-enemy collisions
        for enemy in self.enemies:
            if not enemy.active:
                continue
            ex, ey = enemy.get_position()
            dx = self.player.x - ex
            dy = self.player.y - ey
            if dx*dx + dy*dy < 9:
                enemy.active = False
                self.player.lives -= 1
                self.explosions.append(Explosion(self.player.x, self.player.y))
                if self.player.lives <= 0:
                    self.running = False

        # Player-missile collisions
        for missile in self.missiles:
            if not missile.active:
                continue
            dx = self.player.x - missile.x
            dy = self.player.y - missile.y
            if dx*dx + dy*dy < 4:
                missile.active = False
                self.player.lives -= 1
                self.explosions.append(Explosion(self.player.x, self.player.y))
                if self.player.lives <= 0:
                    self.running = False

    def update(self, dt: float):
        """Update game state."""
        if self.paused:
            return

        self.t += dt

        # Update visualization
        self.viz.update(self.t)

        # Update player
        self.player.update(dt)

        # Update camera
        if self.view_mode == self.VIEW_CHASE:
            self.camera.follow(self.player.x, self.player.y - 10, dt)
        elif self.view_mode == self.VIEW_COCKPIT:
            self.camera.x = self.player.x
            self.camera.y = self.player.y
        else:
            self.camera.x = self.width // 2
            self.camera.y = self.height // 2

        # Update enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.update(dt)

        # Update bullets
        bounds = (0, 0, self.width, self.height)
        for bullet in self.bullets:
            if bullet.active:
                bullet.update(dt, bounds)

        # Update missiles
        for missile in self.missiles:
            if missile.active:
                missile.update(dt)
                # Deactivate if off screen
                if not (0 <= missile.x <= self.width and 0 <= missile.y <= self.height):
                    missile.active = False

        # Update explosions
        for exp in self.explosions:
            exp.update(dt)

        # Clean up inactive objects
        self.enemies = [e for e in self.enemies if e.active]
        self.bullets = [b for b in self.bullets if b.active]
        self.missiles = [m for m in self.missiles if m.active]
        self.explosions = [e for e in self.explosions if e.is_active()]

        # Check collisions
        self.check_collisions()

        # Spawn missiles (wave 7+)
        if self.wave >= 7:
            self.missile_spawn_timer += dt
            if self.missile_spawn_timer >= 3.0:
                self.missile_spawn_timer = 0
                self.missiles.append(Missile.spawn_from_edge(
                    self.width, self.height, self.player.x, self.player.y))

        # Check for wave complete
        if len(self.enemies) == 0:
            self.wave += 1
            self.spawn_wave()

    def handle_input(self, dt: float):
        """Handle player input."""
        inp = self.input_handler.get_input(timeout=0.01)

        if inp == InputType.QUIT:
            self.running = False
            return

        # Movement
        dx, dy = 0, 0
        joy = self.input_handler.get_joystick_state()
        if joy:
            dx = joy.get('x', 0)
            dy = joy.get('y', 0)

        if inp == InputType.UP:
            dy = -1
        elif inp == InputType.DOWN:
            dy = 1
        elif inp == InputType.LEFT:
            dx = -1
        elif inp == InputType.RIGHT:
            dx = 1

        bounds = (2, 2, self.width - 3, self.height - 3)
        self.player.move(dx, dy, dt, bounds)

        # Fire
        if inp == InputType.SELECT and self.player.can_fire():
            self.player.fire()
            self.bullets.append(Bullet(self.player.x, self.player.y - 1, 0, -60))

        # View switching (Tab or Button 2)
        if inp == InputType.BACK:
            self.view_mode = (self.view_mode + 1) % 3

    def draw(self):
        """Draw game state."""
        self.renderer.clear_buffer()

        # Draw L-shaped visualization (minimap style in top-left)
        viz_radius = 8
        self.viz.draw_terminal(
            self.renderer, self.t,
            x_circle_cx=20, x_circle_cy=5,
            y_circle_cx=5, y_circle_cy=15,
            result_cx=20, result_cy=15,
            radius=viz_radius
        )

        # Draw enemies
        screen_cx, screen_cy = self.width // 2, self.height // 2
        for enemy in self.enemies:
            ex, ey = enemy.get_position()
            sx, sy = self.camera.world_to_screen(ex, ey, screen_cx, screen_cy)
            if 0 <= sx < self.width and 0 <= sy < self.height:
                self.renderer.set_pixel(sx, sy, enemy.get_char(), enemy.get_color())

        # Draw bullets
        for bullet in self.bullets:
            sx, sy = self.camera.world_to_screen(bullet.x, bullet.y, screen_cx, screen_cy)
            if 0 <= sx < self.width and 0 <= sy < self.height:
                self.renderer.set_pixel(sx, sy, bullet.char, bullet.color)

        # Draw missiles
        for missile in self.missiles:
            sx, sy = self.camera.world_to_screen(missile.x, missile.y, screen_cx, screen_cy)
            if 0 <= sx < self.width and 0 <= sy < self.height:
                self.renderer.set_pixel(sx, sy, '!', Color.BRIGHT_RED)

        # Draw explosions
        for exp in self.explosions:
            sx, sy = self.camera.world_to_screen(exp.x, exp.y, screen_cx, screen_cy)
            if 0 <= sx < self.width and 0 <= sy < self.height:
                self.renderer.set_pixel(sx, sy, exp.get_char(), Color.BRIGHT_YELLOW)

        # Draw player
        px, py = self.camera.world_to_screen(self.player.x, self.player.y, screen_cx, screen_cy)
        if 0 <= px < self.width and 0 <= py < self.height:
            self.renderer.set_pixel(px, py, 'A', Color.BRIGHT_WHITE)
            self.renderer.set_pixel(px - 1, py + 1, '/', Color.WHITE)
            self.renderer.set_pixel(px + 1, py + 1, '\\', Color.WHITE)

        # Draw HUD
        self.renderer.draw_text(self.width - 20, 1, f"SCORE: {self.score}", Color.WHITE)
        self.renderer.draw_text(self.width - 20, 2, f"WAVE: {self.wave}", Color.CYAN)
        self.renderer.draw_text(self.width - 20, 3, f"LIVES: {'♥' * self.player.lives}", Color.RED)

        view_names = ["TOP-DOWN", "CHASE CAM", "COCKPIT"]
        self.renderer.draw_text(2, self.height - 2, f"[TAB] View: {view_names[self.view_mode]}", Color.WHITE)

        self.renderer.render()

    def run(self):
        """Main game loop."""
        self.renderer.enter_fullscreen()
        self.spawn_wave()

        last_time = time.time()

        try:
            while self.running:
                current_time = time.time()
                dt = min(current_time - last_time, 0.1)
                last_time = current_time

                self.handle_input(dt)
                self.update(dt)
                self.draw()

                time.sleep(0.016)  # ~60 FPS
        finally:
            self.renderer.exit_fullscreen()

        print(f"\nGame Over! Final Score: {self.score}")
        print(f"Waves Completed: {self.wave - 1}")


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_viz():
    """Test the L-shaped visualization."""
    renderer = Renderer()
    viz = LissajousViz(3.0, 2.0, 0)

    renderer.enter_fullscreen()
    t = 0.0

    try:
        for _ in range(300):  # 10 seconds at 30fps
            renderer.clear_buffer()

            viz.update(t)
            viz.draw_terminal(
                renderer, t,
                x_circle_cx=40, x_circle_cy=8,
                y_circle_cx=10, y_circle_cy=22,
                result_cx=50, result_cy=22,
                radius=15
            )

            # Labels
            renderer.draw_text(35, 2, "X Circle (horizontal)", Color.CYAN)
            renderer.draw_text(2, 12, "Y Circle", Color.MAGENTA)
            renderer.draw_text(2, 13, "(vertical)", Color.MAGENTA)
            renderer.draw_text(45, 35, "Result: Lissajous Curve", Color.GREEN)
            renderer.draw_text(45, 36, f"Ratio: {viz.a:.0f}:{viz.b:.0f}", Color.YELLOW)

            renderer.draw_text(2, renderer.height - 2, "[ESC] Exit", Color.WHITE)

            renderer.render()

            t += 0.033
            time.sleep(0.033)
    finally:
        renderer.exit_fullscreen()


def test_game():
    """Test the game."""
    game = LissajousGame()
    game.run()


# ============================================================================
# VIDEO RENDERER
# ============================================================================

def find_monospace_font(size: int):
    """Find a suitable monospace font."""
    paths = []
    if platform.system() == 'Windows':
        paths = [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        ]

    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()


class VideoRenderer:
    """Renders Lissajous educational video frames."""

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.bg_color = COLOR_RGB['bg']

        # Scale fonts based on resolution
        scale = min(width / 1920, height / 1080)
        self.font_large = find_monospace_font(int(48 * scale))
        self.font_medium = find_monospace_font(int(32 * scale))
        self.font_small = find_monospace_font(int(24 * scale))

    def new_frame(self) -> Tuple[Image.Image, ImageDraw.Draw]:
        """Create a new blank frame."""
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        return img, ImageDraw.Draw(img)

    def draw_circle(self, draw: ImageDraw.Draw, cx: int, cy: int, radius: int,
                   color: Tuple[int, int, int], width: int = 2):
        """Draw a circle outline."""
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                    outline=color, width=width)

    def draw_point(self, draw: ImageDraw.Draw, x: int, y: int, radius: int,
                  color: Tuple[int, int, int]):
        """Draw a filled circle point."""
        draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], fill=color)

    def draw_l_shaped_viz(self, draw: ImageDraw.Draw, t: float, viz: LissajousViz,
                         x_cx: int, x_cy: int, y_cx: int, y_cy: int,
                         result_cx: int, result_cy: int, radius: int):
        """Draw complete L-shaped Lissajous visualization."""
        # Get current normalized point
        x_norm, y_norm = viz.get_point(t)

        # Draw axes (light gray)
        # X circle axes
        draw.line([(x_cx - radius - 20, x_cy), (x_cx + radius + 20, x_cy)],
                 fill=COLOR_RGB['grid'], width=1)
        # Y circle axes
        draw.line([(y_cx, y_cy - radius - 20), (y_cx, y_cy + radius + 20)],
                 fill=COLOR_RGB['grid'], width=1)
        # Result axes
        draw.line([(result_cx - radius - 20, result_cy), (result_cx + radius + 20, result_cy)],
                 fill=COLOR_RGB['grid'], width=1)
        draw.line([(result_cx, result_cy - radius - 20), (result_cx, result_cy + radius + 20)],
                 fill=COLOR_RGB['grid'], width=1)

        # X circle (horizontal at top) - cyan
        self.draw_circle(draw, x_cx, x_cy, radius, COLOR_RGB['cyan'], 3)
        # Rotating point on X circle
        x_angle = viz.a * t + viz.delta
        x_px = x_cx + int(radius * math.cos(x_angle))
        x_py = x_cy
        self.draw_point(draw, x_px, x_py, 12, COLOR_RGB['bright_yellow'])

        # Y circle (vertical at left) - magenta
        self.draw_circle(draw, y_cx, y_cy, radius, COLOR_RGB['magenta'], 3)
        # Rotating point on Y circle
        y_angle = viz.b * t
        y_px = y_cx
        y_py = y_cy - int(radius * math.sin(y_angle))
        self.draw_point(draw, y_px, y_py, 12, COLOR_RGB['bright_yellow'])

        # Result point position
        result_x = result_cx + int(radius * x_norm)
        result_y = result_cy - int(radius * y_norm)

        # Connection lines (dashed effect via segments)
        # Horizontal from X point to result Y level
        for i in range(0, abs(result_x - x_px), 20):
            x1 = x_px + (1 if result_x > x_px else -1) * i
            x2 = x_px + (1 if result_x > x_px else -1) * min(i + 10, abs(result_x - x_px))
            draw.line([(x1, result_y), (x2, result_y)], fill=COLOR_RGB['cyan'], width=2)

        # Vertical from Y point to result X level
        for i in range(0, abs(result_y - y_py), 20):
            y1 = y_py + (1 if result_y > y_py else -1) * i
            y2 = y_py + (1 if result_y > y_py else -1) * min(i + 10, abs(result_y - y_py))
            draw.line([(result_x, y1), (result_x, y2)], fill=COLOR_RGB['magenta'], width=2)

        # Draw trail
        for i, (tx, ty) in enumerate(viz.trail):
            trail_x = result_cx + int(radius * tx)
            trail_y = result_cy - int(radius * ty)
            brightness = i / max(len(viz.trail), 1)
            if brightness > 0.8:
                color = COLOR_RGB['bright_green']
                r = 6
            elif brightness > 0.5:
                color = COLOR_RGB['green']
                r = 4
            else:
                color = (50, 100, 60)  # Dim green
                r = 3
            self.draw_point(draw, trail_x, trail_y, r, color)

        # Current result point (brightest)
        self.draw_point(draw, result_x, result_y, 10, COLOR_RGB['bright_white'])


def generate_educational_frames(renderer: VideoRenderer, duration: float, fps: int,
                               viz: LissajousViz) -> Generator[Image.Image, None, None]:
    """Generate educational video frames showing L-shaped visualization."""
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        img, draw = renderer.new_frame()

        # Update visualization trail
        viz.update(t)

        # Layout positions (scaled for resolution)
        scale = renderer.width / 1920
        x_cx = int(500 * scale)
        x_cy = int(200 * scale)
        y_cx = int(200 * scale)
        y_cy = int(550 * scale)
        result_cx = int(1200 * scale)
        result_cy = int(550 * scale)
        radius = int(150 * scale)

        # Draw L-shaped visualization
        renderer.draw_l_shaped_viz(draw, t, viz, x_cx, x_cy, y_cx, y_cy,
                                   result_cx, result_cy, radius)

        # Labels
        draw.text((x_cx - 100, x_cy - radius - 60), "X Circle", font=renderer.font_medium,
                 fill=COLOR_RGB['cyan'])
        draw.text((x_cx - 100, x_cy - radius - 30), f"x = sin({viz.a:.0f}t)",
                 font=renderer.font_small, fill=COLOR_RGB['cyan'])

        draw.text((y_cx - 80, y_cy + radius + 20), "Y Circle", font=renderer.font_medium,
                 fill=COLOR_RGB['magenta'])
        draw.text((y_cx - 80, y_cy + radius + 50), f"y = sin({viz.b:.0f}t)",
                 font=renderer.font_small, fill=COLOR_RGB['magenta'])

        draw.text((result_cx - 100, result_cy + radius + 30), "Lissajous Curve",
                 font=renderer.font_medium, fill=COLOR_RGB['green'])
        draw.text((result_cx - 100, result_cy + radius + 70),
                 f"Ratio: {viz.a:.0f}:{viz.b:.0f}", font=renderer.font_small,
                 fill=COLOR_RGB['yellow'])

        # Title
        draw.text((50, 30), "LISSAJOUS CURVES", font=renderer.font_large,
                 fill=COLOR_RGB['white'])
        draw.text((50, 90), "How X and Y combine to create patterns",
                 font=renderer.font_small, fill=COLOR_RGB['bright_cyan'])

        # Time indicator
        draw.text((renderer.width - 200, renderer.height - 50),
                 f"t = {t:.2f}s", font=renderer.font_small, fill=COLOR_RGB['yellow'])

        yield img


def generate_pattern_gallery_frames(renderer: VideoRenderer, duration: float, fps: int
                                   ) -> Generator[Image.Image, None, None]:
    """Generate frames showing multiple Lissajous patterns."""
    total_frames = int(duration * fps)

    # Patterns to showcase
    patterns = [
        (1, 1, math.pi/2, "Circle"),
        (1, 2, 0, "Figure-8"),
        (2, 3, 0, "Trefoil"),
        (3, 4, 0, "Quatrefoil"),
        (2, 5, 0, "Star-5"),
        (3, 5, 0, "Pentagram"),
    ]

    # Create visualizations
    vizs = [LissajousViz(a, b, d) for a, b, d, _ in patterns]

    for frame in range(total_frames):
        t = frame / fps
        img, draw = renderer.new_frame()

        # Grid layout: 2 rows x 3 columns
        cols, rows = 3, 2
        cell_w = renderer.width // cols
        cell_h = renderer.height // rows

        for i, (viz, (a, b, d, name)) in enumerate(zip(vizs, patterns)):
            viz.update(t)

            col = i % cols
            row = i // cols
            cx = col * cell_w + cell_w // 2
            cy = row * cell_h + cell_h // 2
            radius = min(cell_w, cell_h) // 3

            # Draw curve
            for j, (tx, ty) in enumerate(viz.trail):
                px = cx + int(radius * tx)
                py = cy - int(radius * ty)
                brightness = j / max(len(viz.trail), 1)
                colors = [COLOR_RGB['red'], COLOR_RGB['yellow'], COLOR_RGB['green'],
                         COLOR_RGB['cyan'], COLOR_RGB['blue'], COLOR_RGB['magenta']]
                color = colors[i % len(colors)]
                if brightness > 0.5:
                    r = 4
                else:
                    r = 2
                    color = tuple(c // 2 for c in color)
                renderer.draw_point(draw, px, py, r, color)

            # Current point
            x, y = viz.get_point(t)
            px = cx + int(radius * x)
            py = cy - int(radius * y)
            renderer.draw_point(draw, px, py, 8, COLOR_RGB['bright_white'])

            # Label
            draw.text((cx - 60, cy + radius + 10), name, font=renderer.font_small,
                     fill=COLOR_RGB['white'])
            draw.text((cx - 40, cy + radius + 40), f"{a}:{b}", font=renderer.font_small,
                     fill=COLOR_RGB['yellow'])

        # Title
        draw.text((50, 30), "PATTERN GALLERY", font=renderer.font_large,
                 fill=COLOR_RGB['white'])

        yield img


# ============================================================================
# PART II: INDIVIDUAL PATTERN SHOWCASES WITH CAMERA EFFECTS
# ============================================================================

@dataclass
class PatternShowcase:
    """Configuration for a single pattern showcase."""
    name: str
    a: float
    b: float
    delta: float
    color: Tuple[int, int, int]
    enemy_name: str
    enemy_behavior: str
    points: int
    camera_effect: str  # 'zoom_in', 'zoom_out', 'rotate', 'pan', 'pulse'


PATTERN_SHOWCASES = [
    PatternShowcase("Circle", 1, 1, math.pi/2, COLOR_RGB['cyan'],
                   "Circler", "Steady orbit - predictable but relentless", 10, 'rotate'),
    PatternShowcase("Figure-8", 1, 2, 0, COLOR_RGB['green'],
                   "Figure-8", "Crosses center frequently - dangerous!", 25, 'zoom_in'),
    PatternShowcase("Trefoil", 2, 3, 0, COLOR_RGB['yellow'],
                   "Trefoil", "Complex weave - hard to predict", 50, 'pan'),
    PatternShowcase("Quatrefoil", 3, 4, 0, COLOR_RGB['magenta'],
                   "Quatrefoil", "Four-leaf pattern - watch all directions", 75, 'pulse'),
    PatternShowcase("Star-5", 2, 5, 0, COLOR_RGB['bright_cyan'],
                   "Star", "Fast and erratic - elite enemy", 100, 'zoom_out'),
    PatternShowcase("Pentagram", 3, 5, 0, COLOR_RGB['bright_red'],
                   "Pentagram", "BOSS - Complex star pattern", 500, 'rotate'),
]


def ease_in_out(t: float) -> float:
    """Smooth easing function (cubic)."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def generate_pattern_showcase_frames(renderer: VideoRenderer, showcase: PatternShowcase,
                                     duration: float, fps: int
                                     ) -> Generator[Image.Image, None, None]:
    """Generate frames for a single pattern showcase with camera effects."""
    total_frames = int(duration * fps)
    viz = LissajousViz(showcase.a, showcase.b, showcase.delta)

    # Pre-warm the trail
    for pre_t in range(100):
        viz.update(pre_t * 0.05)

    for frame in range(total_frames):
        t = frame / fps
        progress = frame / total_frames  # 0 to 1

        img, draw = renderer.new_frame()
        viz.update(t)

        # Base center and radius
        base_cx = renderer.width // 2
        base_cy = renderer.height // 2
        base_radius = min(renderer.width, renderer.height) // 3

        # Apply camera effects
        if showcase.camera_effect == 'zoom_in':
            # Start wide, zoom in
            zoom = 0.6 + 0.6 * ease_in_out(progress)
            rotation = 0
            offset_x, offset_y = 0, 0
        elif showcase.camera_effect == 'zoom_out':
            # Start close, zoom out
            zoom = 1.2 - 0.4 * ease_in_out(progress)
            rotation = 0
            offset_x, offset_y = 0, 0
        elif showcase.camera_effect == 'rotate':
            # Rotate around the pattern
            zoom = 1.0
            rotation = progress * math.pi * 2  # Full rotation
            offset_x, offset_y = 0, 0
        elif showcase.camera_effect == 'pan':
            # Pan across the pattern
            zoom = 1.0
            rotation = 0
            pan_amount = 150 * math.sin(progress * math.pi * 2)
            offset_x = int(pan_amount)
            offset_y = int(pan_amount * 0.3)
        elif showcase.camera_effect == 'pulse':
            # Pulsing zoom effect
            zoom = 1.0 + 0.2 * math.sin(progress * math.pi * 6)
            rotation = progress * math.pi * 0.5  # Slow rotation
            offset_x, offset_y = 0, 0
        else:
            zoom = 1.0
            rotation = 0
            offset_x, offset_y = 0, 0

        # Apply zoom to radius
        radius = int(base_radius * zoom)
        cx = base_cx + offset_x
        cy = base_cy + offset_y

        # Draw pattern trail with rotation
        cos_r = math.cos(rotation)
        sin_r = math.sin(rotation)

        for i, (tx, ty) in enumerate(viz.trail):
            # Apply rotation
            rx = tx * cos_r - ty * sin_r
            ry = tx * sin_r + ty * cos_r

            px = cx + int(radius * rx)
            py = cy - int(radius * ry)

            brightness = i / max(len(viz.trail), 1)

            # Gradient color from dim to bright
            if brightness > 0.8:
                color = showcase.color
                r = int(8 * zoom)
            elif brightness > 0.5:
                color = tuple(int(c * 0.7) for c in showcase.color)
                r = int(5 * zoom)
            elif brightness > 0.2:
                color = tuple(int(c * 0.4) for c in showcase.color)
                r = int(3 * zoom)
            else:
                color = tuple(int(c * 0.2) for c in showcase.color)
                r = int(2 * zoom)

            if 0 <= px < renderer.width and 0 <= py < renderer.height:
                renderer.draw_point(draw, px, py, max(1, r), color)

        # Current point (brightest)
        x_norm, y_norm = viz.get_point(t)
        rx = x_norm * cos_r - y_norm * sin_r
        ry = x_norm * sin_r + y_norm * cos_r
        px = cx + int(radius * rx)
        py = cy - int(radius * ry)

        # Glowing effect for current point
        for glow_r in [20, 15, 10, 6]:
            glow_alpha = 1.0 - (glow_r / 20)
            glow_color = tuple(int(c * glow_alpha) for c in showcase.color)
            if 0 <= px < renderer.width and 0 <= py < renderer.height:
                renderer.draw_point(draw, px, py, int(glow_r * zoom), glow_color)

        renderer.draw_point(draw, px, py, int(8 * zoom), COLOR_RGB['bright_white'])

        # Draw enemy ship indicator following the pattern
        ship_chars = ['◊', '⋄', '◆', '★', '✦']
        # (We can't draw actual characters in PIL easily, so we'll draw a triangle shape)
        ship_size = int(15 * zoom)
        # Draw a simple triangle pointing in movement direction
        if len(viz.trail) > 2:
            prev_x, prev_y = viz.trail[-2]
            prx = prev_x * cos_r - prev_y * sin_r
            pry = prev_x * sin_r + prev_y * cos_r
            dx = rx - prx
            dy = ry - pry
            angle = math.atan2(-dy, dx)

            # Triangle points
            tip_x = px + int(ship_size * math.cos(angle))
            tip_y = py - int(ship_size * math.sin(angle))
            left_x = px + int(ship_size * 0.6 * math.cos(angle + 2.5))
            left_y = py - int(ship_size * 0.6 * math.sin(angle + 2.5))
            right_x = px + int(ship_size * 0.6 * math.cos(angle - 2.5))
            right_y = py - int(ship_size * 0.6 * math.sin(angle - 2.5))

            draw.polygon([(tip_x, tip_y), (left_x, left_y), (right_x, right_y)],
                        fill=showcase.color, outline=COLOR_RGB['bright_white'])

        # Title and info (top)
        draw.text((50, 30), showcase.name.upper(), font=renderer.font_large,
                 fill=showcase.color)
        draw.text((50, 90), f"Ratio: {showcase.a:.0f}:{showcase.b:.0f}",
                 font=renderer.font_medium, fill=COLOR_RGB['yellow'])

        # Enemy info panel (bottom left)
        panel_y = renderer.height - 180
        draw.rectangle([(30, panel_y), (500, renderer.height - 30)],
                      fill=(40, 42, 54), outline=showcase.color, width=2)
        draw.text((50, panel_y + 20), f"ENEMY: {showcase.enemy_name}",
                 font=renderer.font_medium, fill=showcase.color)
        draw.text((50, panel_y + 60), showcase.enemy_behavior,
                 font=renderer.font_small, fill=COLOR_RGB['white'])
        draw.text((50, panel_y + 100), f"POINTS: {showcase.points}",
                 font=renderer.font_medium, fill=COLOR_RGB['bright_yellow'])

        # Camera effect indicator (top right)
        effect_names = {
            'zoom_in': 'ZOOM IN',
            'zoom_out': 'ZOOM OUT',
            'rotate': 'ROTATE',
            'pan': 'PAN',
            'pulse': 'PULSE'
        }
        draw.text((renderer.width - 200, 30), effect_names.get(showcase.camera_effect, ''),
                 font=renderer.font_small, fill=COLOR_RGB['cyan'])

        yield img


def generate_part2_frames(renderer: VideoRenderer, duration_per_pattern: float, fps: int
                         ) -> Generator[Image.Image, None, None]:
    """Generate Part II: Individual pattern showcases with camera effects."""

    # Title card for Part II
    title_duration = 3.0
    title_frames = int(title_duration * fps)

    for frame in range(title_frames):
        t = frame / fps
        img, draw = renderer.new_frame()

        # Animated title
        alpha = min(1.0, t / 1.0)  # Fade in over 1 second
        if t > title_duration - 1.0:
            alpha = (title_duration - t)  # Fade out

        # Title text
        draw.text((renderer.width // 2 - 300, renderer.height // 2 - 100),
                 "PART II", font=renderer.font_large, fill=COLOR_RGB['cyan'])
        draw.text((renderer.width // 2 - 350, renderer.height // 2),
                 "ENEMY PATTERNS", font=renderer.font_large, fill=COLOR_RGB['white'])
        draw.text((renderer.width // 2 - 250, renderer.height // 2 + 80),
                 "Know your enemies...", font=renderer.font_medium,
                 fill=COLOR_RGB['yellow'])

        yield img

    # Each pattern showcase
    for showcase in PATTERN_SHOWCASES:
        print(f"  Rendering: {showcase.name} ({showcase.camera_effect})...")
        yield from generate_pattern_showcase_frames(renderer, showcase, duration_per_pattern, fps)

        # Brief transition (fade to black)
        transition_frames = int(0.5 * fps)
        for frame in range(transition_frames):
            img, draw = renderer.new_frame()
            # Just black frame with pattern name fading
            alpha = 1.0 - (frame / transition_frames)
            if alpha > 0.5:
                draw.text((renderer.width // 2 - 100, renderer.height // 2),
                         showcase.name, font=renderer.font_medium,
                         fill=tuple(int(c * alpha) for c in showcase.color))
            yield img


def generate_game_teaser_frames(renderer: VideoRenderer, duration: float, fps: int
                               ) -> Generator[Image.Image, None, None]:
    """Generate game teaser frames showing multiple enemies and player."""
    total_frames = int(duration * fps)

    # Create multiple enemies with different patterns
    enemies = []
    for i, showcase in enumerate(PATTERN_SHOWCASES[:4]):  # Use first 4 patterns
        viz = LissajousViz(showcase.a, showcase.b, showcase.delta)
        # Pre-warm
        for pre_t in range(50):
            viz.update(pre_t * 0.1 + i * 0.5)
        enemies.append((viz, showcase))

    # Player position (moves around)
    player_x = renderer.width // 2
    player_y = renderer.height * 0.75

    for frame in range(total_frames):
        t = frame / fps
        img, draw = renderer.new_frame()

        # Update player movement (circle pattern for demo)
        player_x = renderer.width // 2 + int(200 * math.sin(t * 0.5))
        player_y = renderer.height * 0.7 + int(50 * math.cos(t * 0.3))

        # Draw all enemy patterns
        for i, (viz, showcase) in enumerate(enemies):
            viz.update(t)

            # Position each enemy pattern in different area
            offset_x = (i % 2) * 400 - 200
            offset_y = (i // 2) * 200 - 100
            cx = renderer.width // 2 + offset_x
            cy = renderer.height // 2 + offset_y - 100
            radius = 80

            # Draw trail
            for j, (tx, ty) in enumerate(viz.trail[-100:]):  # Shorter trails
                px = cx + int(radius * tx)
                py = cy - int(radius * ty)
                brightness = j / 100
                if brightness > 0.5:
                    color = showcase.color
                    r = 3
                else:
                    color = tuple(int(c * 0.5) for c in showcase.color)
                    r = 2
                renderer.draw_point(draw, px, py, r, color)

            # Enemy ship
            x_norm, y_norm = viz.get_point(t)
            ex = cx + int(radius * x_norm)
            ey = cy - int(radius * y_norm)
            renderer.draw_point(draw, ex, ey, 10, showcase.color)
            renderer.draw_point(draw, ex, ey, 6, COLOR_RGB['bright_white'])

        # Draw player ship
        draw.polygon([
            (player_x, player_y - 15),
            (player_x - 10, player_y + 10),
            (player_x + 10, player_y + 10)
        ], fill=COLOR_RGB['bright_white'], outline=COLOR_RGB['cyan'])

        # Draw some bullets from player
        for bullet_i in range(3):
            bullet_y = player_y - 30 - (frame * 10 + bullet_i * 40) % 200
            if bullet_y > 0:
                draw.line([(player_x, bullet_y), (player_x, bullet_y - 15)],
                         fill=COLOR_RGB['bright_yellow'], width=3)

        # HUD
        draw.text((50, 30), "LISSAJOUS DEFENDER", font=renderer.font_large,
                 fill=COLOR_RGB['white'])
        draw.text((50, 90), "Survive the mathematical onslaught!",
                 font=renderer.font_small, fill=COLOR_RGB['cyan'])

        # Score display
        score = int(t * 100)
        draw.text((renderer.width - 250, 30), f"SCORE: {score:06d}",
                 font=renderer.font_medium, fill=COLOR_RGB['bright_yellow'])

        # Lives
        for life in range(3):
            lx = renderer.width - 250 + life * 30
            draw.polygon([
                (lx, 80),
                (lx - 8, 95),
                (lx + 8, 95)
            ], fill=COLOR_RGB['bright_green'])

        yield img


def render_to_video(output_path: str, width: int, height: int, fps: int,
                   frame_generator, total_frames: int) -> bool:
    """Render frames to video using temp files."""
    import tempfile
    import shutil

    # Find ffmpeg
    ffmpeg_cmd = 'ffmpeg'
    if platform.system() == 'Windows':
        scoop_ffmpeg = os.path.expanduser('~/scoop/apps/ffmpeg/current/bin/ffmpeg.exe')
        if os.path.exists(scoop_ffmpeg):
            ffmpeg_cmd = scoop_ffmpeg

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='lissajous_')

    print(f"Rendering: {width}x{height} @ {fps}fps")
    print(f"Total frames: {total_frames}")
    print(f"Temp dir: {temp_dir}")
    print(f"Output: {output_path}")
    print()

    try:
        # Render frames to files
        for i, frame in enumerate(frame_generator):
            frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
            frame.save(frame_path, optimize=False)

            if (i + 1) % 50 == 0:
                pct = (i + 1) / total_frames * 100
                print(f"  Frame {i + 1}/{total_frames} ({pct:.1f}%)")

        print(f"\nFrames complete. Encoding with ffmpeg...")

        # Encode with ffmpeg
        frame_pattern = os.path.join(temp_dir, 'frame_%05d.png')
        cmd = [
            ffmpeg_cmd, '-y',
            '-framerate', str(fps),
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '20',
            '-preset', 'fast',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            size = os.path.getsize(output_path) / 1024 / 1024
            print(f"\nSuccess! {output_path}")
            print(f"Size: {size:.1f} MB")
            return True
        else:
            print(f"ffmpeg error: {result.stderr}")
            return False

    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Please install ffmpeg.")
        print("  Windows: scoop install ffmpeg")
        return False
    finally:
        # Cleanup temp files
        print(f"Cleaning up temp files...")
        shutil.rmtree(temp_dir, ignore_errors=True)


def render_educational_video(output_path: str = None, preview: bool = False,
                            include_part2: bool = False):
    """Render complete educational video.

    Args:
        output_path: Output file path
        preview: If True, render at 720p/15fps for faster preview
        include_part2: If True, include Part II (individual pattern showcases)
    """
    if output_path is None:
        suffix = "-full" if include_part2 else "-educational"
        output_path = os.path.join(os.path.dirname(__file__), '..', '..',
                                   f'lissajous{suffix}.mp4')
        output_path = os.path.abspath(output_path)

    # Resolution settings
    if preview:
        width, height, fps = 1280, 720, 15
        edu_duration = 15  # Shorter for preview
        gallery_duration = 10
        pattern_duration = 5  # Per pattern in Part II
        teaser_duration = 8
    else:
        width, height, fps = 1920, 1080, 30
        edu_duration = 30
        gallery_duration = 20
        pattern_duration = 8  # Per pattern in Part II
        teaser_duration = 15

    renderer = VideoRenderer(width, height)

    # Create visualization
    viz = LissajousViz(3.0, 2.0, 0)

    def combined_generator():
        # Part I: Educational content
        print("\n=== PART I: EDUCATIONAL ===")

        # Section 1: L-shaped visualization (3:2 ratio)
        print("Rendering: L-shaped visualization (3:2)...")
        yield from generate_educational_frames(renderer, edu_duration, fps, viz)

        # Section 2: Pattern gallery
        print("Rendering: Pattern gallery...")
        yield from generate_pattern_gallery_frames(renderer, gallery_duration, fps)

        if include_part2:
            # Part II: Individual pattern showcases with camera effects
            print("\n=== PART II: ENEMY PATTERNS ===")
            yield from generate_part2_frames(renderer, pattern_duration, fps)

            # Section 3: Game teaser
            print("\n=== GAME TEASER ===")
            print("Rendering: Game teaser...")
            yield from generate_game_teaser_frames(renderer, teaser_duration, fps)

    # Calculate total frames
    total_frames = int((edu_duration + gallery_duration) * fps)
    if include_part2:
        # Part II: title(3s) + 6 patterns * (duration + 0.5s transition) + teaser
        part2_frames = int((3 + len(PATTERN_SHOWCASES) * (pattern_duration + 0.5) + teaser_duration) * fps)
        total_frames += part2_frames

    return render_to_video(output_path, width, height, fps, combined_generator(), total_frames)


# ============================================================================
# ENTRY POINTS
# ============================================================================

def run_lissajous_game():
    """Run the interactive Lissajous game."""
    game = LissajousGame()
    game.run()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--viz':
            test_viz()
        elif sys.argv[1] == '--game':
            test_game()
        elif sys.argv[1] == '--video':
            output = sys.argv[2] if len(sys.argv) > 2 else None
            render_educational_video(output, preview=False, include_part2=False)
        elif sys.argv[1] == '--preview':
            output = sys.argv[2] if len(sys.argv) > 2 else None
            render_educational_video(output, preview=True, include_part2=False)
        elif sys.argv[1] == '--full':
            # Full video with Part II (camera effects, game teaser)
            output = sys.argv[2] if len(sys.argv) > 2 else None
            render_educational_video(output, preview=False, include_part2=True)
        elif sys.argv[1] == '--full-preview':
            # Preview of full video
            output = sys.argv[2] if len(sys.argv) > 2 else None
            render_educational_video(output, preview=True, include_part2=True)
        else:
            print("Usage: python -m atari_style.demos.lissajous_game [options]")
            print("")
            print("Interactive:")
            print("  --viz           Test L-shaped visualization")
            print("  --game          Run interactive game")
            print("")
            print("Video Export (Part I only):")
            print("  --video         Render educational video (1080p)")
            print("  --preview       Render preview (720p, shorter)")
            print("")
            print("Full Video (Part I + Part II with camera effects):")
            print("  --full          Render complete video with enemy showcases (1080p)")
            print("  --full-preview  Render preview of complete video (720p)")
    else:
        # Default: run game
        run_lissajous_game()
