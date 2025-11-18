"""Spaceship Flying - 3D space navigation and obstacle course.

Pilot a spaceship through space with full 6DOF control.
"""

import time
import random
import math
from ...engine.renderer import Renderer, Color
from ...engine.input_handler import InputHandler, InputType


class Obstacle:
    """Space obstacle (asteroid, gate, etc.)."""

    def __init__(self, x, y, z, obstacle_type='asteroid'):
        self.x = x
        self.y = y
        self.z = z
        self.type = obstacle_type
        self.size = random.uniform(2, 5) if obstacle_type == 'asteroid' else 8
        self.rotation = random.uniform(0, 6.28)
        self.color = Color.DARK_GRAY if obstacle_type == 'asteroid' else Color.BRIGHT_CYAN

    def update(self, speed):
        """Move obstacle toward viewer."""
        self.z -= speed
        self.rotation += 0.1


class Star:
    """Background star."""

    def __init__(self, x, y, z, layer=0):
        self.x = x
        self.y = y
        self.z = z
        self.layer = layer  # 0=far, 1=mid, 2=near

    def update(self, speed):
        """Move star toward viewer."""
        layer_speeds = [0.3, 0.7, 1.0]
        self.z -= speed * layer_speeds[self.layer]


class Spaceship:
    """Player spaceship with 6DOF control."""

    def __init__(self):
        """Initialize spaceship."""
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Position and velocity
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.speed = 1.0  # Forward speed
        self.max_speed = 5.0
        self.min_speed = 0.5

        # Rotation (roll)
        self.roll = 0.0

        # Fuel and health
        self.fuel = 100.0
        self.health = 100.0
        self.score = 0

        # Mode
        self.parameter_mode = False
        self.selected_param = 0
        self.show_help = False

        # Stars (3 layers)
        self.stars = []
        for _ in range(150):
            layer = random.choice([0, 1, 2])
            self.stars.append(Star(
                random.uniform(-50, 50),
                random.uniform(-30, 30),
                random.uniform(1, 100),
                layer
            ))

        # Obstacles
        self.obstacles = []
        self.spawn_distance = 100

        # Parameters
        self.parameters = [
            {'name': 'Speed', 'value': self.speed, 'type': 'float', 'min': 0.5, 'max': 5.0, 'step': 0.5},
            {'name': 'Sensitivity', 'value': 0.5, 'type': 'float', 'min': 0.1, 'max': 1.0, 'step': 0.1},
            {'name': 'Stars', 'value': len(self.stars), 'type': 'int', 'min': 50, 'max': 300, 'step': 50},
        ]

        self.running = True
        self.sensitivity = 0.5

    def spawn_obstacle(self):
        """Spawn a new obstacle."""
        if len(self.obstacles) < 20 and random.random() < 0.02:
            obstacle_type = random.choice(['asteroid', 'asteroid', 'asteroid', 'gate'])
            x = random.uniform(-40, 40)
            y = random.uniform(-25, 25)
            z = self.spawn_distance

            self.obstacles.append(Obstacle(x, y, z, obstacle_type))

    def update(self, dt):
        """Update game state."""
        # Update position from velocity
        self.x += self.vel_x * dt * 10
        self.y += self.vel_y * dt * 10

        # Consume fuel
        self.fuel -= self.speed * dt * 0.5
        if self.fuel <= 0:
            self.fuel = 0
            self.speed = self.min_speed

        # Update stars
        for star in self.stars:
            star.update(self.speed)
            if star.z < 1:
                star.z = 100
                star.x = random.uniform(-50, 50)
                star.y = random.uniform(-30, 30)

        # Update obstacles
        for obs in self.obstacles[:]:
            obs.update(self.speed)

            # Check collision
            screen_x, screen_y = self.project_3d(obs.x - self.x, obs.y - self.y, obs.z)
            center_x = self.renderer.width // 2
            center_y = self.renderer.height // 2

            if obs.z < 5 and abs(screen_x - center_x) < 3 and abs(screen_y - center_y) < 2:
                if obs.type == 'asteroid':
                    self.health -= 10
                    self.obstacles.remove(obs)
                elif obs.type == 'gate':
                    self.score += 100
                    self.obstacles.remove(obs)

            # Remove if behind viewer
            if obs.z < 0:
                self.obstacles.remove(obs)

        # Spawn new obstacles
        self.spawn_obstacle()

    def project_3d(self, x, y, z):
        """Project 3D point to 2D screen coordinates."""
        if z <= 0:
            return (-1, -1)

        fov = 200
        scale = fov / z

        screen_x = int(self.renderer.width / 2 + x * scale)
        screen_y = int(self.renderer.height / 2 + y * scale * 0.5)  # Aspect ratio

        return (screen_x, screen_y)

    def draw_stars(self):
        """Draw starfield."""
        layer_colors = [
            (Color.BLUE, '·'),
            (Color.CYAN, '·'),
            (Color.BRIGHT_CYAN, '*'),
        ]

        for star in self.stars:
            screen_x, screen_y = self.project_3d(star.x - self.x, star.y - self.y, star.z)

            if 0 <= screen_x < self.renderer.width and 0 <= screen_y < self.renderer.height:
                color, char = layer_colors[star.layer]
                self.renderer.set_pixel(screen_x, screen_y, char, color)

    def draw_obstacles(self):
        """Draw obstacles."""
        for obs in self.obstacles:
            screen_x, screen_y = self.project_3d(obs.x - self.x, obs.y - self.y, obs.z)

            if 0 <= screen_x < self.renderer.width and 0 <= screen_y < self.renderer.height:
                size = max(1, int(obs.size * 200 / obs.z))

                if obs.type == 'asteroid':
                    # Draw rotating asteroid
                    chars = '◊◇◆⬖⬗'
                    char = chars[int(obs.rotation * 5) % len(chars)]
                    self.renderer.set_pixel(screen_x, screen_y, char, Color.YELLOW)

                    # Larger asteroids
                    if size > 2:
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                if 0 <= screen_x + dx < self.renderer.width and 0 <= screen_y + dy < self.renderer.height:
                                    self.renderer.set_pixel(screen_x + dx, screen_y + dy, char, Color.YELLOW)

                elif obs.type == 'gate':
                    # Draw gate (you want to fly through it)
                    gate_width = max(4, size)
                    gate_height = max(3, size // 2)

                    # Draw gate frame
                    for dx in range(-gate_width, gate_width + 1):
                        y_top = screen_y - gate_height
                        y_bot = screen_y + gate_height
                        if 0 <= y_top < self.renderer.height:
                            self.renderer.set_pixel(screen_x + dx, y_top, '═', Color.BRIGHT_GREEN)
                        if 0 <= y_bot < self.renderer.height:
                            self.renderer.set_pixel(screen_x + dx, y_bot, '═', Color.BRIGHT_GREEN)

                    for dy in range(-gate_height, gate_height + 1):
                        x_left = screen_x - gate_width
                        x_right = screen_x + gate_width
                        if 0 <= x_left < self.renderer.width:
                            self.renderer.set_pixel(x_left, screen_y + dy, '║', Color.BRIGHT_GREEN)
                        if 0 <= x_right < self.renderer.width:
                            self.renderer.set_pixel(x_right, screen_y + dy, '║', Color.BRIGHT_GREEN)

    def draw_cockpit(self):
        """Draw spaceship cockpit overlay."""
        # Crosshair
        center_x = self.renderer.width // 2
        center_y = self.renderer.height // 2

        self.renderer.draw_text(center_x - 1, center_y, "┼", Color.BRIGHT_RED)

        # HUD
        hud_lines = [
            f"SPEED: {self.speed:.1f}",
            f"FUEL:  {self.fuel:.0f}%",
            f"HEALTH:{self.health:.0f}%",
            f"SCORE: {self.score}",
        ]

        for i, line in enumerate(hud_lines):
            self.renderer.draw_text(2, 2 + i, line, Color.BRIGHT_WHITE)

        # Speedometer bar
        speed_bar_width = 20
        speed_fill = int((self.speed / self.max_speed) * speed_bar_width)
        speed_x = 2
        speed_y = 7

        self.renderer.draw_text(speed_x, speed_y, "[" + "█" * speed_fill + "·" * (speed_bar_width - speed_fill) + "]", Color.GREEN)

    def _sync_parameters(self):
        """Sync parameters."""
        self.parameters[0]['value'] = self.speed
        self.parameters[1]['value'] = self.sensitivity
        self.parameters[2]['value'] = len(self.stars)

    def draw_ui(self):
        """Draw UI with parameter panel."""
        self._sync_parameters()

        # Build parameter text
        param_lines = ["SPACESHIP PARAMETERS", ""]
        mode_text = "MODE: ADJUST" if self.parameter_mode else "MODE: FLIGHT"
        param_lines.append(mode_text)
        param_lines.append("")

        for i, param in enumerate(self.parameters):
            prefix = "► " if (self.parameter_mode and i == self.selected_param) else "  "

            if param['type'] == 'float':
                value_str = f"{param['value']:.2f}"
            elif param['type'] == 'int':
                value_str = str(param['value'])
            else:
                value_str = str(param['value'])

            param_lines.append(f"{prefix}{param['name']}: {value_str}")

        # Create box
        import subprocess
        param_text = "\n".join(param_lines)
        try:
            result = subprocess.run(
                ['boxes', '-d', 'ansi-double', '-p', 'a1'],
                input=param_text,
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                box_lines = result.stdout.strip().split('\n')
            else:
                max_width = max(len(line) for line in param_lines)
                box_lines = ["╔" + "═" * (max_width + 2) + "╗"]
                for line in param_lines:
                    box_lines.append(f"║ {line:<{max_width}} ║")
                box_lines.append("╚" + "═" * (max_width + 2) + "╝")
        except Exception:
            max_width = max(len(line) for line in param_lines)
            box_lines = ["╔" + "═" * (max_width + 2) + "╗"]
            for line in param_lines:
                box_lines.append(f"║ {line:<{max_width}} ║")
            box_lines.append("╚" + "═" * (max_width + 2) + "╝")

        # Draw box
        box_width = max(len(line) for line in box_lines)
        box_x = self.renderer.width - box_width - 2
        box_y = self.renderer.height - len(box_lines) - 2

        for i, line in enumerate(box_lines):
            if self.parameter_mode and "MODE: ADJUST" in line:
                color = Color.BRIGHT_GREEN
            elif "MODE: FLIGHT" in line:
                color = Color.BRIGHT_CYAN
            elif line.strip().startswith("►"):
                color = Color.BRIGHT_YELLOW
            else:
                color = Color.WHITE

            self.renderer.draw_text(box_x, box_y + i, line, color)

        # Mode hint
        if self.parameter_mode:
            hint = "[SPACE] Flight Mode | JOYSTICK: ↕ Select, ← → Adjust"
            color = Color.BRIGHT_GREEN
        else:
            hint = "[SPACE] Adjust Mode | JOYSTICK: Fly Ship | +/- Speed | ESC=Exit"
            color = Color.BRIGHT_CYAN

        hint_x = (self.renderer.width - len(hint)) // 2
        self.renderer.draw_text(hint_x, self.renderer.height - 1, hint, color)

    def _adjust_parameter(self, direction):
        """Adjust parameter."""
        param = self.parameters[self.selected_param]

        if param['type'] == 'float':
            step = param.get('step', 0.1)
            new_val = param['value'] + (direction * step)
            param['value'] = max(param['min'], min(param['max'], new_val))

            if param['name'] == 'Speed':
                self.speed = param['value']
            elif param['name'] == 'Sensitivity':
                self.sensitivity = param['value']

        elif param['type'] == 'int':
            step = param.get('step', 1)
            new_val = param['value'] + (direction * step)
            param['value'] = max(param['min'], min(param['max'], new_val))

            if param['name'] == 'Stars':
                # Adjust star count
                current = len(self.stars)
                target = param['value']
                if target > current:
                    for _ in range(target - current):
                        layer = random.choice([0, 1, 2])
                        self.stars.append(Star(
                            random.uniform(-50, 50),
                            random.uniform(-30, 30),
                            random.uniform(1, 100),
                            layer
                        ))
                elif target < current:
                    self.stars = self.stars[:target]

    def handle_input(self, input_type, raw_key):
        """Handle input."""
        # Special keys
        if raw_key:
            if raw_key == ' ':
                self.parameter_mode = not self.parameter_mode
                return
            if raw_key.name == 'KEY_ESCAPE':
                self.running = False
                return

        if input_type == InputType.QUIT:
            self.running = False
            return

        # Parameter mode
        if self.parameter_mode:
            if input_type == InputType.UP:
                self.selected_param = (self.selected_param - 1) % len(self.parameters)
            elif input_type == InputType.DOWN:
                self.selected_param = (self.selected_param + 1) % len(self.parameters)
            elif input_type == InputType.LEFT:
                self._adjust_parameter(-1)
            elif input_type == InputType.RIGHT:
                self._adjust_parameter(1)

        # Flight mode
        else:
            # Lateral movement
            if input_type == InputType.LEFT:
                self.vel_x = -self.sensitivity * 2
            elif input_type == InputType.RIGHT:
                self.vel_x = self.sensitivity * 2
            else:
                self.vel_x *= 0.9  # Damping

            if input_type == InputType.UP:
                self.vel_y = -self.sensitivity * 2
            elif input_type == InputType.DOWN:
                self.vel_y = self.sensitivity * 2
            else:
                self.vel_y *= 0.9  # Damping

            # Acceleration
            if input_type == InputType.SELECT:
                self.speed = min(self.max_speed, self.speed + 0.2)

        # Keyboard shortcuts
        if raw_key:
            key_lower = raw_key.lower()

            if key_lower == 'h':
                self.show_help = not self.show_help
            elif key_lower == '+' or key_lower == '=':
                self.speed = min(self.max_speed, self.speed + 0.5)
            elif key_lower == '-':
                self.speed = max(self.min_speed, self.speed - 0.5)

    def run(self):
        """Main game loop."""
        try:
            self.renderer.enter_fullscreen()
            last_time = time.time()

            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                # Update
                self.update(dt)

                # Draw
                self.renderer.clear_buffer()
                self.draw_stars()
                self.draw_obstacles()
                self.draw_cockpit()
                self.draw_ui()
                self.renderer.render()

                # Input
                input_type = self.input_handler.get_input(timeout=0.05)
                raw_key = None
                with self.input_handler.term.cbreak():
                    raw_key = self.input_handler.term.inkey(timeout=0)

                self.handle_input(input_type, raw_key)

                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_spaceship():
    """Entry point for Spaceship Flying."""
    ship = Spaceship()
    ship.run()


if __name__ == '__main__':
    run_spaceship()
