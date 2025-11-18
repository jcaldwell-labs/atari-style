"""Galaga/Space Invaders style shooter with wave-based enemies."""

import time
import random
from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


class Bullet:
    """Represents a bullet (player or enemy)."""

    def __init__(self, x, y, vy, char='|', color=Color.BRIGHT_WHITE):
        self.x = x
        self.y = y
        self.vy = vy  # Negative = upward, positive = downward
        self.char = char
        self.color = color
        self.active = True

    def update(self, dt):
        """Update bullet position."""
        self.y += self.vy * dt

        # Deactivate if off screen
        if self.y < 0 or self.y >= 50:
            self.active = False


class Explosion:
    """Visual explosion effect."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0
        self.max_frames = 6
        self.timer = 0

    def update(self, dt):
        """Update explosion animation."""
        self.timer += dt
        if self.timer >= 0.1:
            self.timer = 0
            self.frame += 1

    def is_active(self):
        """Check if explosion is still animating."""
        return self.frame < self.max_frames

    def get_char(self):
        """Get character for current frame."""
        frames = ['*', '+', '*', '+', '·', ' ']
        return frames[min(self.frame, len(frames) - 1)]


class Enemy:
    """Enemy ship."""

    ENEMY_TYPES = {
        'grunt': {'char': '◊⋄', 'color': Color.GREEN, 'value': 10, 'fire_rate': 0.02},
        'officer': {'char': '⊕⊗', 'color': Color.CYAN, 'value': 20, 'fire_rate': 0.03},
        'commander': {'char': '◉○', 'color': Color.RED, 'value': 40, 'fire_rate': 0.04},
    }

    def __init__(self, x, y, enemy_type='grunt'):
        self.x = float(x)
        self.y = float(y)
        self.formation_x = x
        self.formation_y = y
        self.type = enemy_type
        self.info = self.ENEMY_TYPES[enemy_type]
        self.active = True
        self.in_formation = True
        self.animation_frame = 0
        self.animation_timer = 0

        # Dive attack
        self.diving = False
        self.dive_path = []
        self.dive_index = 0

    def update(self, dt, formation_offset_x, formation_offset_y):
        """Update enemy."""
        # Animation
        self.animation_timer += dt
        if self.animation_timer >= 0.3:
            self.animation_timer = 0
            self.animation_frame = 1 - self.animation_frame

        if self.diving:
            # Follow dive path
            if self.dive_index < len(self.dive_path):
                self.x, self.y = self.dive_path[self.dive_index]
                self.dive_index += 1
            else:
                # Dive complete, return to formation or loop back
                if self.y > 50:
                    # Wrap to top
                    self.y = -5
                    self.diving = False
                    self.in_formation = True
        else:
            # Stay in formation
            self.x = self.formation_x + formation_offset_x
            self.y = self.formation_y + formation_offset_y

    def start_dive(self, player_x):
        """Start dive attack toward player."""
        self.diving = True
        self.in_formation = False

        # Generate curved dive path (Bezier-like)
        start = (self.x, self.y)
        mid = (player_x, self.y + 10)
        end = (player_x, 40)

        self.dive_path = []
        steps = 30

        for i in range(steps):
            t = i / steps
            # Quadratic Bezier curve
            x = (1-t)**2 * start[0] + 2*(1-t)*t * mid[0] + t**2 * end[0]
            y = (1-t)**2 * start[1] + 2*(1-t)*t * mid[1] + t**2 * end[1]
            self.dive_path.append((x, y))

        self.dive_index = 0

    def get_char(self):
        """Get character for rendering."""
        chars = self.info['char']
        return chars[self.animation_frame]

    def get_color(self):
        """Get color for rendering."""
        return self.info['color']


class UFO:
    """Bonus UFO that crosses screen."""

    def __init__(self):
        self.x = 0
        self.y = 3
        self.vx = 15  # Speed
        self.active = False
        self.blink = False
        self.value = random.choice([100, 150, 200, 250, 300])

    def spawn(self):
        """Spawn UFO."""
        self.active = True
        self.x = 0 if random.random() < 0.5 else 80
        self.vx = 15 if self.x == 0 else -15
        self.value = random.choice([100, 150, 200, 250, 300])

    def update(self, dt, screen_width):
        """Update UFO."""
        if not self.active:
            return

        self.x += self.vx * dt
        self.blink = not self.blink

        # Deactivate if off screen
        if self.x < -5 or self.x > screen_width + 5:
            self.active = False

    def get_char(self):
        """Get character."""
        return '<<=>' if self.blink else '<=>' + ' '


class Player:
    """Player ship."""

    def __init__(self, x, y, screen_width):
        self.x = x
        self.y = y
        self.screen_width = screen_width
        self.speed = 40  # chars per second
        self.fire_cooldown = 0
        self.fire_rate = 0.3  # seconds between shots

    def update(self, dt):
        """Update player."""
        self.fire_cooldown = max(0, self.fire_cooldown - dt)

    def move(self, dx, dt):
        """Move player left/right."""
        self.x += dx * self.speed * dt
        self.x = max(2, min(self.x, self.screen_width - 3))

    def can_fire(self):
        """Check if player can fire."""
        return self.fire_cooldown == 0

    def fire(self):
        """Fire a bullet."""
        self.fire_cooldown = self.fire_rate


class Galaga:
    """Main Galaga game class."""

    # Game states
    STATE_WAVE_START = 0
    STATE_PLAYING = 1
    STATE_DEATH = 2
    STATE_VICTORY = 3
    STATE_GAME_OVER = 4

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.width = self.renderer.width
        self.height = self.renderer.height

        # Game state
        self.state = self.STATE_WAVE_START
        self.wave = 1
        self.score = 0
        self.lives = 3
        self.high_score = 0

        # Player
        self.player = Player(self.width // 2, self.height - 4, self.width)

        # Bullets
        self.player_bullets = []
        self.enemy_bullets = []
        self.max_player_bullets = 3

        # Enemies
        self.enemies = []
        self.formation_offset_x = 0
        self.formation_offset_y = 0
        self.formation_direction = 1  # 1 = right, -1 = left
        self.formation_speed = 5  # chars per second
        self.formation_descent = False

        # UFO
        self.ufo = UFO()
        self.ufo_spawn_timer = random.uniform(15, 30)

        # Explosions
        self.explosions = []

        # Dive attack
        self.dive_timer = 0
        self.dive_interval = random.uniform(3, 7)

        # Wave start delay
        self.wave_start_timer = 2.0

        # Death timer
        self.death_timer = 0

        # Stats
        self.shots_fired = 0
        self.shots_hit = 0

        # Create first wave
        self._create_wave(self.wave)

        # Frame timing
        self.last_time = time.time()

    def _create_wave(self, wave):
        """Create enemy formation for wave."""
        self.enemies = []

        # Reset formation
        self.formation_offset_x = 0
        self.formation_offset_y = 5
        self.formation_direction = 1

        # Determine formation size (increases with wave)
        cols = min(10, 6 + wave // 2)
        rows = min(5, 3 + wave // 3)

        start_x = (self.width - cols * 4) // 2
        start_y = 8

        # Create formation
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * 4
                y = start_y + row * 3

                # Determine enemy type by row
                if row == 0:
                    enemy_type = 'commander'
                elif row <= 2:
                    enemy_type = 'officer'
                else:
                    enemy_type = 'grunt'

                enemy = Enemy(x, y, enemy_type)
                self.enemies.append(enemy)

        # Increase difficulty
        self.formation_speed = 5 + wave * 0.5
        self.dive_interval = max(1, 7 - wave * 0.3)

    def update(self, dt):
        """Update game state."""
        if self.state == self.STATE_WAVE_START:
            self.wave_start_timer -= dt
            if self.wave_start_timer <= 0:
                self.state = self.STATE_PLAYING

        elif self.state == self.STATE_PLAYING:
            self._update_playing(dt)

        elif self.state == self.STATE_DEATH:
            self.death_timer += dt
            if self.death_timer >= 1.0:
                self.death_timer = 0
                self.lives -= 1

                if self.lives <= 0:
                    self.state = self.STATE_GAME_OVER
                    if self.score > self.high_score:
                        self.high_score = self.score
                else:
                    # Reset
                    self.player.x = self.width // 2
                    self.player_bullets = []
                    self.enemy_bullets = []
                    self.explosions = []
                    self.state = self.STATE_PLAYING

    def _update_playing(self, dt):
        """Update during active gameplay."""
        # Update player
        self.player.update(dt)

        # Update formation movement
        self.formation_offset_x += self.formation_direction * self.formation_speed * dt

        # Check formation bounds
        leftmost = min((e.formation_x for e in self.enemies if e.active), default=50)
        rightmost = max((e.formation_x for e in self.enemies if e.active), default=0)

        if (leftmost + self.formation_offset_x <= 2 or
            rightmost + self.formation_offset_x >= self.width - 3):
            self.formation_direction *= -1
            self.formation_offset_y += 2  # Descend

        # Update enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.update(dt, self.formation_offset_x, self.formation_offset_y)

                # Random firing
                if random.random() < enemy.info['fire_rate'] * dt:
                    self.enemy_bullets.append(
                        Bullet(enemy.x, enemy.y + 1, 30, '!', Color.RED)
                    )

        # Update dive attacks
        self.dive_timer += dt
        if self.dive_timer >= self.dive_interval:
            self.dive_timer = 0
            self.dive_interval = random.uniform(2, 5)

            # Pick random enemy to dive
            formation_enemies = [e for e in self.enemies if e.active and e.in_formation]
            if formation_enemies:
                diver = random.choice(formation_enemies)
                diver.start_dive(self.player.x)

        # Update UFO
        self.ufo_spawn_timer -= dt
        if self.ufo_spawn_timer <= 0 and not self.ufo.active:
            self.ufo.spawn()
            self.ufo_spawn_timer = random.uniform(20, 40)

        self.ufo.update(dt, self.width)

        # Update bullets
        for bullet in self.player_bullets[:]:
            bullet.update(dt)
            if not bullet.active:
                self.player_bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            bullet.update(dt)
            if not bullet.active:
                self.enemy_bullets.remove(bullet)

        # Update explosions
        for explosion in self.explosions[:]:
            explosion.update(dt)
            if not explosion.is_active():
                self.explosions.remove(explosion)

        # Check collisions
        self._check_collisions()

        # Check wave complete
        if all(not e.active for e in self.enemies):
            self.state = self.STATE_VICTORY
            self.wave += 1

    def _check_collisions(self):
        """Check all collisions."""
        # Player bullets vs enemies
        for bullet in self.player_bullets[:]:
            if not bullet.active:
                continue

            bullet_hit = False

            # Check enemy hits
            for enemy in self.enemies:
                if not enemy.active:
                    continue

                if (int(bullet.x) == int(enemy.x) and
                    int(bullet.y) == int(enemy.y)):
                    # Hit!
                    enemy.active = False
                    bullet.active = False
                    bullet_hit = True
                    self.score += enemy.info['value']
                    self.shots_hit += 1
                    self.explosions.append(Explosion(enemy.x, enemy.y))
                    break

            # Check UFO hit
            if not bullet_hit and self.ufo.active:
                if (int(bullet.x) >= int(self.ufo.x) and
                    int(bullet.x) < int(self.ufo.x) + 4 and
                    int(bullet.y) == int(self.ufo.y)):
                    self.ufo.active = False
                    bullet.active = False
                    self.score += self.ufo.value
                    self.shots_hit += 1
                    self.explosions.append(Explosion(self.ufo.x, self.ufo.y))

        # Enemy bullets vs player
        for bullet in self.enemy_bullets[:]:
            if not bullet.active:
                continue

            if (int(bullet.x) == int(self.player.x) and
                int(bullet.y) == int(self.player.y)):
                # Player hit
                bullet.active = False
                self.explosions.append(Explosion(self.player.x, self.player.y))
                self.state = self.STATE_DEATH
                return

        # Enemies vs player (collision)
        for enemy in self.enemies:
            if not enemy.active:
                continue

            if (int(enemy.x) == int(self.player.x) and
                int(enemy.y) >= self.player.y - 1):
                # Collision
                enemy.active = False
                self.explosions.append(Explosion(self.player.x, self.player.y))
                self.state = self.STATE_DEATH
                return

    def handle_input(self, dt):
        """Handle player input."""
        # Get joystick state
        jx, jy = self.input_handler.get_joystick_state()

        # Movement
        if jx != 0:
            self.player.move(jx, dt)
        else:
            # Keyboard
            with self.input_handler.term.cbreak():
                key = self.input_handler.term.inkey(timeout=0.001)

                if key:
                    if key.name == 'KEY_LEFT' or key.lower() == 'a':
                        self.player.move(-1, dt)
                    elif key.name == 'KEY_RIGHT' or key.lower() == 'd':
                        self.player.move(1, dt)

        # Firing
        buttons = self.input_handler.get_joystick_buttons()
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)

            if ((key == ' ' or key.name == 'KEY_ENTER' or buttons.get(0)) and
                self.player.can_fire() and
                len(self.player_bullets) < self.max_player_bullets):
                self.player.fire()
                self.player_bullets.append(
                    Bullet(self.player.x, self.player.y - 1, -50)
                )
                self.shots_fired += 1

    def draw(self):
        """Draw the game."""
        self.renderer.clear_buffer()

        # Draw HUD
        self._draw_hud()

        # Draw player
        self.renderer.set_pixel(int(self.player.x), int(self.player.y), '^', Color.BRIGHT_GREEN)
        # Thrusters
        if int(time.time() * 10) % 2 == 0:
            self.renderer.set_pixel(int(self.player.x), int(self.player.y) + 1, '∧', Color.YELLOW)

        # Draw enemies
        for enemy in self.enemies:
            if enemy.active:
                self.renderer.set_pixel(int(enemy.x), int(enemy.y),
                                        enemy.get_char(), enemy.get_color())

        # Draw UFO
        if self.ufo.active:
            ufo_chars = self.ufo.get_char()
            for i, char in enumerate(ufo_chars):
                self.renderer.set_pixel(int(self.ufo.x) + i, int(self.ufo.y),
                                        char, Color.BRIGHT_MAGENTA)

        # Draw bullets
        for bullet in self.player_bullets:
            if bullet.active:
                self.renderer.set_pixel(int(bullet.x), int(bullet.y),
                                        bullet.char, bullet.color)

        for bullet in self.enemy_bullets:
            if bullet.active:
                self.renderer.set_pixel(int(bullet.x), int(bullet.y),
                                        bullet.char, bullet.color)

        # Draw explosions
        for explosion in self.explosions:
            self.renderer.set_pixel(int(explosion.x), int(explosion.y),
                                    explosion.get_char(), Color.BRIGHT_YELLOW)

        # Draw state messages
        if self.state == self.STATE_WAVE_START:
            msg = f"WAVE {self.wave}"
            self.renderer.draw_text(self.width // 2 - len(msg) // 2,
                                    self.height // 2, msg, Color.BRIGHT_CYAN)

        elif self.state == self.STATE_VICTORY:
            msg = f"WAVE {self.wave - 1} COMPLETE!"
            self.renderer.draw_text(self.width // 2 - len(msg) // 2,
                                    self.height // 2, msg, Color.BRIGHT_GREEN)
            msg2 = "Get ready..."
            self.renderer.draw_text(self.width // 2 - len(msg2) // 2,
                                    self.height // 2 + 2, msg2, Color.BRIGHT_WHITE)

        elif self.state == self.STATE_GAME_OVER:
            msg = "GAME OVER"
            self.renderer.draw_text(self.width // 2 - len(msg) // 2,
                                    self.height // 2, msg, Color.BRIGHT_RED)
            score_msg = f"Final Score: {self.score}"
            self.renderer.draw_text(self.width // 2 - len(score_msg) // 2,
                                    self.height // 2 + 2, score_msg, Color.BRIGHT_WHITE)
            if self.shots_fired > 0:
                accuracy = int((self.shots_hit / self.shots_fired) * 100)
                acc_msg = f"Accuracy: {accuracy}%"
                self.renderer.draw_text(self.width // 2 - len(acc_msg) // 2,
                                        self.height // 2 + 4, acc_msg, Color.BRIGHT_YELLOW)

        self.renderer.render()

    def _draw_hud(self):
        """Draw heads-up display."""
        # Score
        score_text = f"SCORE: {self.score}"
        self.renderer.draw_text(2, 0, score_text, Color.BRIGHT_WHITE)

        # High score
        high_score_text = f"HIGH: {self.high_score}"
        self.renderer.draw_text(self.width // 2 - len(high_score_text) // 2, 0,
                                high_score_text, Color.BRIGHT_YELLOW)

        # Lives
        lives_text = f"LIVES: {'^' * self.lives}"
        self.renderer.draw_text(self.width - len(lives_text) - 2, 0,
                                lives_text, Color.BRIGHT_GREEN)

        # Wave
        wave_text = f"WAVE: {self.wave}"
        self.renderer.draw_text(2, 1, wave_text, Color.BRIGHT_CYAN)

    def run(self):
        """Main game loop."""
        self.renderer.enter_fullscreen()

        try:
            running = True

            while running:
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time

                # Cap dt
                dt = min(dt, 0.1)

                # Handle input
                input_type = self.input_handler.get_input(timeout=0.001)

                if input_type == InputType.BACK or input_type == InputType.QUIT:
                    running = False
                elif input_type == InputType.SELECT:
                    if self.state == self.STATE_GAME_OVER:
                        self.__init__()  # Restart
                    elif self.state == self.STATE_VICTORY:
                        self._create_wave(self.wave)
                        self.wave_start_timer = 2.0
                        self.state = self.STATE_WAVE_START

                # Continuous input for movement
                if self.state == self.STATE_PLAYING:
                    self.handle_input(dt)

                # Update
                self.update(dt)

                # Draw
                self.draw()

                # Frame rate (60 FPS)
                time.sleep(0.016)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_galaga():
    """Entry point for Galaga game."""
    game = Galaga()
    game.run()


if __name__ == "__main__":
    run_galaga()
