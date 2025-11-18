"""Breakout/Arkanoid paddle game with power-ups and physics."""

import time
import random
import math
from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


class PowerUp:
    """Represents a falling power-up."""

    TYPES = {
        'P': ('Wide Paddle', Color.BRIGHT_CYAN, 30),      # Duration in seconds
        'M': ('Multi-Ball', Color.BRIGHT_YELLOW, 0),      # Instant
        'L': ('Laser', Color.BRIGHT_RED, 20),
        'S': ('Slow Ball', Color.BRIGHT_GREEN, 20),
        'E': ('Extra Life', Color.BRIGHT_MAGENTA, 0),     # Instant
    }

    def __init__(self, x, y, ptype):
        self.x = x
        self.y = y
        self.type = ptype
        self.name, self.color, self.duration = self.TYPES[ptype]
        self.active = True

    def update(self, dt):
        """Move power-up downward."""
        self.y += 10 * dt  # Fall at 10 rows per second


class Ball:
    """Represents a ball in the game."""

    def __init__(self, x, y, vx=0, vy=-30):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)  # Velocity in chars/sec
        self.vy = float(vy)
        self.active = True
        self.on_paddle = True

    def update(self, dt, speed_multiplier=1.0):
        """Update ball position."""
        if not self.on_paddle:
            self.x += self.vx * dt * speed_multiplier
            self.y += self.vy * dt * speed_multiplier

    def launch(self, angle_degrees=None):
        """Launch the ball from paddle."""
        if angle_degrees is None:
            angle_degrees = random.uniform(-60, 60)  # Random angle

        angle = math.radians(angle_degrees)
        speed = 30
        self.vx = speed * math.sin(angle)
        self.vy = -speed * math.cos(angle)
        self.on_paddle = False


class Brick:
    """Represents a brick."""

    def __init__(self, x, y, row, brick_type='normal'):
        self.x = x
        self.y = y
        self.width = 6  # Brick width
        self.row = row
        self.type = brick_type
        self.hits_remaining = 2 if brick_type == 'strong' else 1
        self.destroyed = False
        self.indestructible = (brick_type == 'unbreakable')

    def get_color(self):
        """Get brick color based on row and state."""
        if self.indestructible:
            return Color.WHITE

        if self.type == 'strong' and self.hits_remaining == 1:
            return Color.YELLOW  # Damaged strong brick

        # Color gradient by row
        colors = [
            Color.BRIGHT_RED,      # Row 0 (top)
            Color.BRIGHT_MAGENTA,
            Color.BRIGHT_YELLOW,
            Color.BRIGHT_GREEN,
            Color.BRIGHT_CYAN,
            Color.BRIGHT_BLUE,
            Color.RED,
            Color.MAGENTA,
        ]
        return colors[self.row % len(colors)]

    def get_value(self):
        """Get point value."""
        if self.indestructible:
            return 0
        if self.type == 'strong':
            return 100
        # Higher rows worth more
        return 10 + (7 - self.row) * 10


class Laser:
    """Laser shot from paddle."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True

    def update(self, dt):
        """Move laser upward."""
        self.y -= 50 * dt  # Fast upward movement


class Breakout:
    """Main Breakout game class."""

    # Game states
    STATE_MENU = 0
    STATE_SERVING = 1
    STATE_PLAYING = 2
    STATE_VICTORY = 3
    STATE_DEATH = 4
    STATE_GAME_OVER = 5

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.width = self.renderer.width
        self.height = self.renderer.height

        # Game state
        self.state = self.STATE_SERVING
        self.level = 1
        self.score = 0
        self.lives = 3
        self.combo = 0

        # Paddle
        self.paddle_width = 12
        self.paddle_x = self.width // 2 - self.paddle_width // 2
        self.paddle_y = self.height - 3
        self.paddle_speed = 50  # chars per second

        # Balls
        self.balls = [Ball(self.width // 2, self.paddle_y - 1)]

        # Bricks
        self.bricks = []
        self._create_level(1)

        # Power-ups
        self.powerups = []
        self.active_powerups = {}  # {type: expiry_time}

        # Lasers (if laser power-up active)
        self.lasers = []
        self.laser_cooldown = 0

        # Auto-launch timer
        self.auto_launch_timer = 0

        # Death timer
        self.death_timer = 0

        # Frame timing
        self.last_time = time.time()

    def _create_level(self, level):
        """Create brick layout for level."""
        self.bricks = []

        # Determine layout pattern
        patterns = ['full', 'checkerboard', 'pyramid', 'diamonds', 'waves']
        pattern = patterns[(level - 1) % len(patterns)]

        brick_width = 6
        brick_spacing = 1
        start_x = 5
        start_y = 5
        rows = min(8, 5 + level // 3)  # More rows at higher levels
        cols = (self.width - 2 * start_x) // (brick_width + brick_spacing)

        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (brick_width + brick_spacing)
                y = start_y + row * 2

                # Apply pattern
                create_brick = False
                brick_type = 'normal'

                if pattern == 'full':
                    create_brick = True
                elif pattern == 'checkerboard':
                    create_brick = (row + col) % 2 == 0
                elif pattern == 'pyramid':
                    center_col = cols // 2
                    create_brick = abs(col - center_col) <= row
                elif pattern == 'diamonds':
                    create_brick = (row + col) % 3 != 0
                elif pattern == 'waves':
                    create_brick = (col + row * 2) % 4 != 3

                # Add strong bricks at higher levels
                if create_brick and level > 2 and random.random() < 0.1:
                    brick_type = 'strong'

                # Add unbreakable bricks at higher levels
                if create_brick and level > 4 and random.random() < 0.05:
                    brick_type = 'unbreakable'

                if create_brick:
                    self.bricks.append(Brick(x, y, row, brick_type))

    def _reset_paddle(self):
        """Reset paddle to normal state."""
        self.paddle_width = 12

    def update(self, dt):
        """Update game state."""
        if self.state == self.STATE_SERVING:
            # Auto-launch after 3 seconds
            self.auto_launch_timer += dt
            if self.auto_launch_timer >= 3.0:
                for ball in self.balls:
                    if ball.on_paddle:
                        ball.launch()
                self.state = self.STATE_PLAYING

        elif self.state == self.STATE_PLAYING:
            self._update_playing(dt)

        elif self.state == self.STATE_DEATH:
            # Wait a moment before respawning or game over
            self.death_timer += dt
            if self.death_timer >= 1.0:
                self.death_timer = 0
                self.lives -= 1

                if self.lives <= 0:
                    self.state = self.STATE_GAME_OVER
                else:
                    # Reset for next ball
                    self.balls = [Ball(self.width // 2, self.paddle_y - 1)]
                    self.powerups = []
                    self.lasers = []
                    self._reset_paddle()
                    self.active_powerups = {}
                    self.auto_launch_timer = 0
                    self.state = self.STATE_SERVING

        elif self.state == self.STATE_VICTORY:
            # Wait for input to advance to next level
            pass

    def _update_playing(self, dt):
        """Update during active gameplay."""
        current_time = time.time()

        # Update active power-up timers
        expired = []
        for ptype, expiry_time in self.active_powerups.items():
            if current_time >= expiry_time:
                expired.append(ptype)
                if ptype == 'P':  # Wide paddle expired
                    self._reset_paddle()

        for ptype in expired:
            del self.active_powerups[ptype]

        # Determine ball speed multiplier
        speed_mult = 0.5 if 'S' in self.active_powerups else 1.0

        # Update balls
        for ball in self.balls[:]:
            if not ball.active:
                continue

            if ball.on_paddle:
                # Ball follows paddle
                ball.x = self.paddle_x + self.paddle_width // 2
                ball.y = self.paddle_y - 1
            else:
                ball.update(dt, speed_mult)
                self._handle_ball_collisions(ball)

        # Remove inactive balls
        self.balls = [b for b in self.balls if b.active]

        # Check if all balls lost
        if not self.balls:
            self.state = self.STATE_DEATH
            return

        # Update power-ups
        for powerup in self.powerups[:]:
            if not powerup.active:
                continue

            powerup.update(dt)

            # Check collision with paddle
            if (int(powerup.y) == self.paddle_y and
                self.paddle_x <= powerup.x < self.paddle_x + self.paddle_width):
                self._activate_powerup(powerup)
                powerup.active = False

            # Remove if off screen
            if powerup.y >= self.height:
                powerup.active = False

        self.powerups = [p for p in self.powerups if p.active]

        # Update lasers
        if 'L' in self.active_powerups:
            self.laser_cooldown = max(0, self.laser_cooldown - dt)

            for laser in self.lasers[:]:
                laser.update(dt)

                # Check laser-brick collision
                for brick in self.bricks:
                    if brick.destroyed or brick.indestructible:
                        continue

                    if (brick.x <= laser.x < brick.x + brick.width and
                        brick.y <= laser.y < brick.y + 2):
                        self._destroy_brick(brick, laser.x, laser.y)
                        laser.active = False
                        break

                # Remove if off screen
                if laser.y < 0:
                    laser.active = False

            self.lasers = [l for l in self.lasers if l.active]

        # Check victory
        destroyable_bricks = [b for b in self.bricks if not b.destroyed and not b.indestructible]
        if not destroyable_bricks:
            self.state = self.STATE_VICTORY

    def _handle_ball_collisions(self, ball):
        """Handle all collisions for a ball."""
        # Wall collisions
        if ball.x <= 0 or ball.x >= self.width - 1:
            ball.vx = -ball.vx
            ball.x = max(0, min(ball.x, self.width - 1))

        if ball.y <= 0:
            ball.vy = -ball.vy
            ball.y = 0

        # Bottom - ball lost
        if ball.y >= self.height:
            ball.active = False
            self.combo = 0  # Reset combo on miss
            return

        # Paddle collision
        ball_int_y = int(ball.y)
        ball_int_x = int(ball.x)

        if (ball_int_y == self.paddle_y and
            self.paddle_x <= ball_int_x < self.paddle_x + self.paddle_width and
            ball.vy > 0):  # Ball moving downward

            # Reflect based on hit position
            hit_pos = (ball_int_x - self.paddle_x) / self.paddle_width  # 0.0 to 1.0
            angle_degrees = -90 + (hit_pos - 0.5) * 120  # -90 to +30 degrees
            angle = math.radians(angle_degrees)

            speed = math.sqrt(ball.vx**2 + ball.vy**2)
            ball.vx = speed * math.sin(angle)
            ball.vy = speed * math.cos(angle)

            # Ensure upward movement
            if ball.vy > 0:
                ball.vy = -ball.vy

        # Brick collision
        for brick in self.bricks:
            if brick.destroyed:
                continue

            # Simple AABB collision
            if (brick.x <= ball_int_x < brick.x + brick.width and
                brick.y <= ball_int_y < brick.y + 2):

                if not brick.indestructible:
                    self._destroy_brick(brick, ball.x, ball.y)

                # Determine bounce direction
                # Simple approach: reverse vertical direction
                ball.vy = -ball.vy

                # Slight speed increase (max cap)
                speed = math.sqrt(ball.vx**2 + ball.vy**2)
                if speed < 40:
                    ball.vx *= 1.02
                    ball.vy *= 1.02

                break

    def _destroy_brick(self, brick, hit_x, hit_y):
        """Destroy or damage a brick."""
        brick.hits_remaining -= 1

        if brick.hits_remaining <= 0:
            brick.destroyed = True
            self.score += brick.get_value()
            self.combo += 1

            # Extra points for combo
            if self.combo > 1:
                self.score += self.combo * 5

            # Chance to drop power-up (20%)
            if random.random() < 0.2:
                ptype = random.choice(list(PowerUp.TYPES.keys()))
                self.powerups.append(PowerUp(hit_x, hit_y, ptype))

            # Extra life every 10,000 points
            if self.score // 10000 > (self.score - brick.get_value()) // 10000:
                self.lives += 1

    def _activate_powerup(self, powerup):
        """Activate a collected power-up."""
        current_time = time.time()
        ptype = powerup.type

        if ptype == 'P':  # Wide paddle
            self.paddle_width = 20
            self.active_powerups['P'] = current_time + powerup.duration

        elif ptype == 'M':  # Multi-ball
            # Split each existing ball into 3
            new_balls = []
            for ball in self.balls:
                if not ball.on_paddle:
                    # Create two additional balls at angles
                    for angle_offset in [-30, 30]:
                        angle = math.atan2(ball.vx, -ball.vy)
                        angle_deg = math.degrees(angle) + angle_offset
                        new_ball = Ball(ball.x, ball.y)
                        new_ball.launch(angle_deg)
                        new_balls.append(new_ball)
            self.balls.extend(new_balls)

        elif ptype == 'L':  # Laser
            self.active_powerups['L'] = current_time + powerup.duration

        elif ptype == 'S':  # Slow ball
            self.active_powerups['S'] = current_time + powerup.duration

        elif ptype == 'E':  # Extra life
            self.lives += 1

    def handle_input(self, input_type):
        """Handle user input."""
        if self.state == self.STATE_GAME_OVER or self.state == self.STATE_VICTORY:
            if input_type == InputType.SELECT:
                # Restart or next level
                if self.state == self.STATE_VICTORY:
                    self.level += 1
                    self._create_level(self.level)
                    self.balls = [Ball(self.width // 2, self.paddle_y - 1)]
                    self.powerups = []
                    self.lasers = []
                    self._reset_paddle()
                    self.active_powerups = {}
                    self.auto_launch_timer = 0
                    self.state = self.STATE_SERVING
                else:
                    # Restart game
                    self.__init__()

            elif input_type == InputType.BACK:
                return False  # Exit to menu

        return True

    def update_paddle(self, dt):
        """Update paddle position based on input."""
        # Get joystick state for analog control
        jx, jy = self.input_handler.get_joystick_state()

        if abs(jx) > 0:
            # Analog joystick control
            self.paddle_x += jx * self.paddle_speed * dt
        else:
            # Digital keyboard control
            with self.input_handler.term.cbreak():
                key = self.input_handler.term.inkey(timeout=0.001)

                if key:
                    if key.name == 'KEY_LEFT' or key.lower() == 'a':
                        self.paddle_x -= self.paddle_speed * dt
                    elif key.name == 'KEY_RIGHT' or key.lower() == 'd':
                        self.paddle_x += self.paddle_speed * dt

        # Clamp paddle to screen
        self.paddle_x = max(0, min(self.paddle_x, self.width - self.paddle_width))

        # Check for action buttons
        buttons = self.input_handler.get_joystick_buttons()
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)

            # Launch ball
            if (key == ' ' or key.name == 'KEY_ENTER' or
                (buttons.get(0) and self.state == self.STATE_SERVING)):
                if self.state == self.STATE_SERVING:
                    for ball in self.balls:
                        if ball.on_paddle:
                            ball.launch()
                    self.state = self.STATE_PLAYING
                elif 'L' in self.active_powerups and self.laser_cooldown == 0:
                    # Fire laser
                    self.lasers.append(Laser(self.paddle_x + self.paddle_width // 2, self.paddle_y - 1))
                    self.laser_cooldown = 0.3

    def draw(self):
        """Draw the game."""
        self.renderer.clear_buffer()

        # Draw HUD
        self._draw_hud()

        # Draw bricks
        for brick in self.bricks:
            if not brick.destroyed:
                color = brick.get_color()
                char = '█' if not brick.indestructible else '▓'
                for dy in range(2):
                    for dx in range(brick.width):
                        self.renderer.set_pixel(brick.x + dx, brick.y + dy, char, color)

        # Draw paddle
        paddle_char = '═'
        paddle_color = Color.BRIGHT_CYAN if 'P' in self.active_powerups else Color.CYAN
        for i in range(self.paddle_width):
            self.renderer.set_pixel(int(self.paddle_x) + i, self.paddle_y, paddle_char, paddle_color)

        # Draw balls
        for ball in self.balls:
            if ball.active:
                self.renderer.set_pixel(int(ball.x), int(ball.y), '●', Color.BRIGHT_WHITE)

        # Draw power-ups
        for powerup in self.powerups:
            if powerup.active:
                self.renderer.set_pixel(int(powerup.x), int(powerup.y), powerup.type, powerup.color)

        # Draw lasers
        for laser in self.lasers:
            if laser.active:
                self.renderer.set_pixel(int(laser.x), int(laser.y), '|', Color.BRIGHT_RED)

        # Draw game state messages
        if self.state == self.STATE_SERVING:
            msg = "PRESS SPACE TO LAUNCH"
            self.renderer.draw_text(self.width // 2 - len(msg) // 2, self.height // 2, msg, Color.BRIGHT_YELLOW)

        elif self.state == self.STATE_VICTORY:
            msg = f"LEVEL {self.level} COMPLETE!"
            self.renderer.draw_text(self.width // 2 - len(msg) // 2, self.height // 2 - 1, msg, Color.BRIGHT_GREEN)
            msg2 = "PRESS SPACE FOR NEXT LEVEL"
            self.renderer.draw_text(self.width // 2 - len(msg2) // 2, self.height // 2 + 1, msg2, Color.BRIGHT_YELLOW)

        elif self.state == self.STATE_GAME_OVER:
            msg = "GAME OVER"
            self.renderer.draw_text(self.width // 2 - len(msg) // 2, self.height // 2 - 1, msg, Color.BRIGHT_RED)
            msg2 = f"Final Score: {self.score}"
            self.renderer.draw_text(self.width // 2 - len(msg2) // 2, self.height // 2 + 1, msg2, Color.BRIGHT_WHITE)
            msg3 = "PRESS SPACE TO RESTART"
            self.renderer.draw_text(self.width // 2 - len(msg3) // 2, self.height // 2 + 3, msg3, Color.BRIGHT_YELLOW)

        self.renderer.render()

    def _draw_hud(self):
        """Draw heads-up display."""
        # Score
        score_text = f"SCORE: {self.score}"
        self.renderer.draw_text(2, 0, score_text, Color.BRIGHT_WHITE)

        # Lives
        lives_text = f"LIVES: {self.lives}"
        self.renderer.draw_text(2, 1, lives_text, Color.BRIGHT_GREEN)

        # Level
        level_text = f"LEVEL: {self.level}"
        self.renderer.draw_text(self.width - len(level_text) - 2, 0, level_text, Color.BRIGHT_YELLOW)

        # Combo
        if self.combo > 1:
            combo_text = f"COMBO x{self.combo}"
            self.renderer.draw_text(self.width - len(combo_text) - 2, 1, combo_text, Color.BRIGHT_MAGENTA)

        # Active power-ups
        y_offset = 2
        current_time = time.time()
        for ptype, expiry_time in self.active_powerups.items():
            remaining = int(expiry_time - current_time)
            if remaining > 0:
                name, color, _ = PowerUp.TYPES[ptype]
                text = f"{name}: {remaining}s"
                self.renderer.draw_text(self.width - len(text) - 2, y_offset, text, color)
                y_offset += 1

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
                input_type = self.input_handler.get_input(timeout=0.001)

                if input_type == InputType.BACK or input_type == InputType.QUIT:
                    running = False
                else:
                    if not self.handle_input(input_type):
                        running = False

                # Update paddle (needs continuous input)
                if self.state in [self.STATE_SERVING, self.STATE_PLAYING]:
                    self.update_paddle(dt)

                # Update game
                self.update(dt)

                # Draw
                self.draw()

                # Frame rate limiting (60 FPS)
                time.sleep(0.016)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_breakout():
    """Entry point for Breakout game."""
    game = Breakout()
    game.run()


if __name__ == "__main__":
    run_breakout()
