"""Target Shooter - First-person shooting gallery.

Aim and shoot moving targets for points and combos!
"""

import time
import random
from ...engine.renderer import Renderer, Color
from ...engine.input_handler import InputHandler, InputType


class Target:
    """Shooting gallery target."""

    def __init__(self, x, y, speed, target_type='normal'):
        self.x = x
        self.y = y
        self.speed = speed
        self.type = target_type
        self.alive = True
        self.animation_frame = 0

        # Type properties
        if target_type == 'normal':
            self.points = 10
            self.size = 3
            self.char = '◎'
            self.color = Color.YELLOW
        elif target_type == 'fast':
            self.points = 25
            self.size = 2
            self.char = '◉'
            self.color = Color.BRIGHT_RED
            self.speed *= 1.5
        elif target_type == 'bonus':
            self.points = 50
            self.size = 4
            self.char = '★'
            self.color = Color.BRIGHT_YELLOW
        elif target_type == 'large':
            self.points = 15
            self.size = 5
            self.char = '●'
            self.color = Color.CYAN

    def update(self, dt):
        """Update target position."""
        self.x += self.speed * dt * 10
        self.animation_frame += 1

    def is_hit(self, aim_x, aim_y):
        """Check if target is hit by aim point."""
        dx = abs(aim_x - self.x)
        dy = abs(aim_y - self.y)
        return dx <= self.size and dy <= self.size // 2


class TargetShooter:
    """First-person target shooting game."""

    def __init__(self):
        """Initialize shooter."""
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Aim position (controlled by joystick/keyboard)
        self.aim_x = self.renderer.width // 2
        self.aim_y = self.renderer.height // 2

        # Game state
        self.score = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self.combo = 0
        self.max_combo = 0
        self.ammo = 50
        self.reload_time = 0

        # Targets
        self.targets = []
        self.spawn_timer = 0
        self.wave = 1
        self.targets_destroyed = 0

        # Mode
        self.parameter_mode = False
        self.selected_param = 0
        self.show_help = False

        # Settings
        self.difficulty = 1.0
        self.target_speed = 1.0
        self.spawn_rate = 2.0

        # Parameters
        self.parameters = [
            {'name': 'Difficulty', 'value': self.difficulty, 'type': 'float', 'min': 0.5, 'max': 3.0, 'step': 0.5},
            {'name': 'Target Speed', 'value': self.target_speed, 'type': 'float', 'min': 0.5, 'max': 3.0, 'step': 0.5},
            {'name': 'Spawn Rate', 'value': self.spawn_rate, 'type': 'float', 'min': 0.5, 'max': 5.0, 'step': 0.5},
        ]

        self.running = True

    def spawn_target(self):
        """Spawn a new target."""
        if len(self.targets) < 10:
            # Determine type based on difficulty
            rand = random.random()
            if rand < 0.5:
                target_type = 'normal'
            elif rand < 0.7:
                target_type = 'fast'
            elif rand < 0.85:
                target_type = 'large'
            else:
                target_type = 'bonus'

            # Spawn from sides
            if random.random() < 0.5:
                x = 0 if random.random() < 0.5 else self.renderer.width - 1
                y = random.randint(5, self.renderer.height - 5)
                speed = self.target_speed * (1 if x == 0 else -1)
            else:
                x = random.randint(5, self.renderer.width - 5)
                y = 0 if random.random() < 0.5 else self.renderer.height - 1
                speed = 0
                # Stationary targets

            target = Target(x, y, speed, target_type)
            self.targets.append(target)

    def shoot(self):
        """Fire at current aim position."""
        if self.ammo <= 0 or self.reload_time > 0:
            return

        self.shots_fired += 1
        self.ammo -= 1
        self.reload_time = 0.2  # 0.2 second reload

        # Check if any target is hit
        hit_target = None
        for target in self.targets:
            if target.alive and target.is_hit(self.aim_x, self.aim_y):
                hit_target = target
                break

        if hit_target:
            self.shots_hit += 1
            hit_target.alive = False
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
            combo_bonus = self.combo * 5
            self.score += hit_target.points + combo_bonus
            self.targets_destroyed += 1
        else:
            self.combo = 0  # Missed shot breaks combo

    def update(self, dt):
        """Update game state."""
        # Reload timer
        if self.reload_time > 0:
            self.reload_time -= dt

        # Spawn timer
        self.spawn_timer += dt
        if self.spawn_timer >= (1.0 / self.spawn_rate):
            self.spawn_target()
            self.spawn_timer = 0

        # Update targets
        for target in self.targets[:]:
            if not target.alive:
                self.targets.remove(target)
                continue

            target.update(dt)

            # Remove if off screen
            if (target.x < -10 or target.x > self.renderer.width + 10 or
                target.y < -10 or target.y > self.renderer.height + 10):
                self.targets.remove(target)

        # Reload ammo periodically
        if self.ammo < 50:
            self.ammo = min(50, self.ammo + dt * 2)

    def draw_targets(self):
        """Draw all targets."""
        for target in self.targets:
            if not target.alive:
                continue

            x = int(target.x)
            y = int(target.y)

            # Draw target based on size
            for dx in range(-target.size, target.size + 1):
                for dy in range(-target.size // 2, target.size // 2 + 1):
                    dist = math.sqrt(dx * dx + (dy * 2) * (dy * 2))
                    if dist <= target.size:
                        px = x + dx
                        py = y + dy
                        if 0 <= px < self.renderer.width and 0 <= py < self.renderer.height:
                            if dist < target.size * 0.5:
                                self.renderer.set_pixel(px, py, target.char, target.color)
                            else:
                                self.renderer.set_pixel(px, py, '○', target.color)

    def draw_crosshair(self):
        """Draw aiming crosshair."""
        x = int(self.aim_x)
        y = int(self.aim_y)

        # Crosshair lines
        crosshair_size = 3
        for i in range(1, crosshair_size + 1):
            # Horizontal
            if x - i >= 0:
                self.renderer.set_pixel(x - i, y, '─', Color.BRIGHT_RED)
            if x + i < self.renderer.width:
                self.renderer.set_pixel(x + i, y, '─', Color.BRIGHT_RED)

            # Vertical
            if y - i >= 0:
                self.renderer.set_pixel(x, y - i, '│', Color.BRIGHT_RED)
            if y + i < self.renderer.height:
                self.renderer.set_pixel(x, y + i, '│', Color.BRIGHT_RED)

        # Center dot
        self.renderer.set_pixel(x, y, '┼', Color.BRIGHT_WHITE)

    def draw_hud(self):
        """Draw HUD."""
        hud_lines = [
            f"SCORE: {self.score}",
            f"COMBO: {self.combo}x (Best: {self.max_combo}x)",
            f"AMMO:  {int(self.ammo)}/50",
            f"WAVE:  {self.wave}",
            "",
            f"Accuracy: {int((self.shots_hit / max(1, self.shots_fired)) * 100)}%",
            f"Destroyed: {self.targets_destroyed}",
        ]

        for i, line in enumerate(hud_lines):
            color = Color.BRIGHT_GREEN if "COMBO" in line and self.combo > 0 else Color.WHITE
            self.renderer.draw_text(2, 2 + i, line, color)

        # Ammo bar
        ammo_width = 20
        ammo_fill = int((self.ammo / 50) * ammo_width)
        ammo_color = Color.BRIGHT_GREEN if self.ammo > 25 else (Color.YELLOW if self.ammo > 10 else Color.BRIGHT_RED)
        self.renderer.draw_text(2, 10, "[" + "█" * ammo_fill + "·" * (ammo_width - ammo_fill) + "]", ammo_color)

    def _sync_parameters(self):
        """Sync parameters."""
        self.parameters[0]['value'] = self.difficulty
        self.parameters[1]['value'] = self.target_speed
        self.parameters[2]['value'] = self.spawn_rate

    def draw_ui(self):
        """Draw UI."""
        self._sync_parameters()

        param_lines = ["TARGET SHOOTER PARAMETERS", ""]
        mode_text = "MODE: ADJUST" if self.parameter_mode else "MODE: SHOOT"
        param_lines.append(mode_text)
        param_lines.append("")

        for i, param in enumerate(self.parameters):
            prefix = "► " if (self.parameter_mode and i == self.selected_param) else "  "
            value_str = f"{param['value']:.2f}" if param['type'] == 'float' else str(param['value'])
            param_lines.append(f"{prefix}{param['name']}: {value_str}")

        # Create box
        import subprocess
        param_text = "\n".join(param_lines)
        try:
            result = subprocess.run(['boxes', '-d', 'ansi-double', '-p', 'a1'],
                                  input=param_text, capture_output=True, text=True, timeout=2)
            box_lines = result.stdout.strip().split('\n') if result.returncode == 0 else None
        except:
            box_lines = None

        if not box_lines:
            max_width = max(len(line) for line in param_lines)
            box_lines = ["╔" + "═" * (max_width + 2) + "╗"]
            for line in param_lines:
                box_lines.append(f"║ {line:<{max_width}} ║")
            box_lines.append("╚" + "═" * (max_width + 2) + "╝")

        # Draw box bottom-right
        box_width = max(len(line) for line in box_lines)
        box_x = self.renderer.width - box_width - 2
        box_y = self.renderer.height - len(box_lines) - 2

        for i, line in enumerate(box_lines):
            color = (Color.BRIGHT_GREEN if self.parameter_mode and "ADJUST" in line
                    else Color.BRIGHT_CYAN if "SHOOT" in line
                    else Color.BRIGHT_YELLOW if line.strip().startswith("►")
                    else Color.WHITE)
            self.renderer.draw_text(box_x, box_y + i, line, color)

        # Hint
        hint = ("[SPACE] Shoot Mode | JOYSTICK: ↕ Select, ← → Adjust" if self.parameter_mode
                else "[SPACE] Adjust | JOYSTICK=Aim BUTTON0=Fire | ESC=Exit")
        color = Color.BRIGHT_GREEN if self.parameter_mode else Color.BRIGHT_CYAN
        hint_x = (self.renderer.width - len(hint)) // 2
        self.renderer.draw_text(hint_x, self.renderer.height - 1, hint, color)

    def _adjust_parameter(self, direction):
        """Adjust parameter."""
        param = self.parameters[self.selected_param]
        step = param.get('step', 0.1)
        new_val = param['value'] + (direction * step)
        param['value'] = max(param['min'], min(param['max'], new_val))

        if param['name'] == 'Difficulty':
            self.difficulty = param['value']
        elif param['name'] == 'Target Speed':
            self.target_speed = param['value']
        elif param['name'] == 'Spawn Rate':
            self.spawn_rate = param['value']

    def handle_input(self, input_type, raw_key):
        """Handle input."""
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

        # Shooting mode
        else:
            # Aim with joystick
            joy_x, joy_y = self.input_handler.get_joystick_state()
            if abs(joy_x) > 0.1 or abs(joy_y) > 0.1:
                self.aim_x += joy_x * 15
                self.aim_y += joy_y * 10

                # Clamp to screen
                self.aim_x = max(0, min(self.renderer.width - 1, self.aim_x))
                self.aim_y = max(0, min(self.renderer.height - 1, self.aim_y))

            # Keyboard aim
            if input_type == InputType.UP:
                self.aim_y = max(0, self.aim_y - 5)
            elif input_type == InputType.DOWN:
                self.aim_y = min(self.renderer.height - 1, self.aim_y + 5)
            elif input_type == InputType.LEFT:
                self.aim_x = max(0, self.aim_x - 5)
            elif input_type == InputType.RIGHT:
                self.aim_x = min(self.renderer.width - 1, self.aim_x + 5)

            # Shoot
            elif input_type == InputType.SELECT:
                self.shoot()

        # Keyboard shortcuts
        if raw_key:
            if raw_key.lower() == 'h':
                self.show_help = not self.show_help

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
                self.draw_targets()
                self.draw_crosshair()
                self.draw_hud()
                self.draw_ui()
                self.renderer.render()

                # Input
                input_type = self.input_handler.get_input(timeout=0.05)
                raw_key = None
                with self.input_handler.term.cbreak():
                    raw_key = self.input_handler.term.inkey(timeout=0)

                self.handle_input(input_type, raw_key)

                time.sleep(0.033)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_targetshooter():
    """Entry point."""
    shooter = TargetShooter()
    shooter.run()


if __name__ == '__main__':
    run_targetshooter()
