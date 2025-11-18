"""Pac-Man style maze chase game with ghost AI."""

import time
import random
from collections import deque
from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


class Maze:
    """Represents the game maze."""

    # Maze tiles
    WALL = '#'
    PATH = ' '
    PELLET = '.'
    POWER_PELLET = 'O'
    GHOST_GATE = '='

    # Classic-inspired maze (simplified for terminal)
    MAZE_DATA = [
        "############################",
        "#............##............#",
        "#.####.#####.##.#####.####.#",
        "#O####.#####.##.#####.####O#",
        "#.####.#####.##.#####.####.#",
        "#..........................#",
        "#.####.##.########.##.####.#",
        "#.####.##.########.##.####.#",
        "#......##....##....##......#",
        "######.##### ## #####.######",
        "######.##### ## #####.######",
        "######.##          ##.######",
        "######.## ###==### ##.######",
        "      .   #      #   .      ",
        "######.## ######## ##.######",
        "######.## ######## ##.######",
        "######.##    ##    ##.######",
        "#............##............#",
        "#.####.#####.##.#####.####.#",
        "#O..##.......  .......##..O#",
        "###.##.##.########.##.##.###",
        "###.##.##.########.##.##.###",
        "#......##....##....##......#",
        "#.##########.##.##########.#",
        "#.##########.##.##########.#",
        "#..........................#",
        "############################",
    ]

    def __init__(self):
        self.width = len(self.MAZE_DATA[0])
        self.height = len(self.MAZE_DATA)
        self.tiles = [list(row) for row in self.MAZE_DATA]
        self.pellet_count = self._count_pellets()

    def _count_pellets(self):
        """Count total pellets (excluding power pellets)."""
        count = 0
        for row in self.tiles:
            count += row.count(self.PELLET)
        return count

    def get_tile(self, x, y):
        """Get tile at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return self.WALL

    def set_tile(self, x, y, tile):
        """Set tile at position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile

    def is_walkable(self, x, y):
        """Check if position is walkable."""
        tile = self.get_tile(x, y)
        return tile != self.WALL

    def is_ghost_walkable(self, x, y):
        """Check if position is walkable for ghosts (includes gates)."""
        tile = self.get_tile(x, y)
        return tile != self.WALL or tile == self.GHOST_GATE


class Entity:
    """Base class for player and ghosts."""

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.direction = (0, 0)  # (dx, dy)
        self.speed = 8  # tiles per second

    def get_tile_pos(self):
        """Get tile position (integer coordinates)."""
        return (int(self.x), int(self.y))

    def update(self, dt):
        """Update position based on direction."""
        dx, dy = self.direction
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt


class Player(Entity):
    """Pac-Man player character."""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.mouth_open = True
        self.animation_timer = 0

    def update(self, dt):
        """Update player."""
        super().update(dt)

        # Animate mouth
        self.animation_timer += dt
        if self.animation_timer >= 0.15:
            self.mouth_open = not self.mouth_open
            self.animation_timer = 0

    def get_char(self):
        """Get character representation."""
        if self.mouth_open:
            return 'C'
        else:
            return 'O'


class Ghost(Entity):
    """Ghost enemy with AI."""

    # Ghost modes
    MODE_CHASE = 'chase'
    MODE_SCATTER = 'scatter'
    MODE_FRIGHTENED = 'frightened'
    MODE_DEAD = 'dead'

    def __init__(self, x, y, name, color, scatter_target):
        super().__init__(x, y)
        self.name = name
        self.color = color
        self.base_color = color
        self.scatter_target = scatter_target  # Target corner in scatter mode
        self.mode = self.MODE_SCATTER
        self.spawn_pos = (x, y)
        self.path = []
        self.path_update_timer = 0

    def update(self, dt, maze, player_pos, other_ghosts):
        """Update ghost AI."""
        super().update(dt)

        # Update path periodically
        self.path_update_timer += dt
        if self.path_update_timer >= 0.5:  # Recalculate path every 0.5s
            self.path_update_timer = 0
            target = self._get_target(player_pos, other_ghosts)
            self.path = self._find_path(maze, target)

        # Follow path
        if self.path:
            next_tile = self.path[0]
            tx, ty = next_tile
            gx, gy = self.get_tile_pos()

            # Check if reached next waypoint
            if (gx, gy) == (tx, ty):
                self.path.pop(0)
                if self.path:
                    next_tile = self.path[0]
                    tx, ty = next_tile

            # Move toward next waypoint
            if gx < tx:
                self.direction = (1, 0)
            elif gx > tx:
                self.direction = (-1, 0)
            elif gy < ty:
                self.direction = (0, 1)
            elif gy > ty:
                self.direction = (0, -1)

    def _get_target(self, player_pos, other_ghosts):
        """Get target tile based on ghost personality."""
        px, py = player_pos

        if self.mode == self.MODE_SCATTER:
            return self.scatter_target
        elif self.mode == self.MODE_FRIGHTENED:
            # Random target
            return (random.randint(1, 26), random.randint(1, 25))
        elif self.mode == self.MODE_DEAD:
            return self.spawn_pos
        else:  # CHASE mode
            if self.name == 'Blinky':
                # Direct chase
                return player_pos
            elif self.name == 'Pinky':
                # Ambush: 4 tiles ahead
                return (px + 4 * player_pos[2] if len(player_pos) > 2 else px, py + 4 * player_pos[3] if len(player_pos) > 3 else py)
            elif self.name == 'Inky':
                # Flanking: use Blinky's position
                blinky_pos = None
                for ghost in other_ghosts:
                    if ghost.name == 'Blinky':
                        blinky_pos = ghost.get_tile_pos()
                        break
                if blinky_pos:
                    # Target is reflection of player from Blinky
                    target_x = px + (px - blinky_pos[0])
                    target_y = py + (py - blinky_pos[1])
                    return (target_x, target_y)
                return player_pos
            elif self.name == 'Clyde':
                # Shy: chase when far, run when close
                gx, gy = self.get_tile_pos()
                distance = abs(px - gx) + abs(py - gy)
                if distance > 8:
                    return player_pos
                else:
                    return self.scatter_target

        return player_pos

    def _find_path(self, maze, target):
        """Find path to target using BFS (simpler than A*)."""
        start = self.get_tile_pos()
        target = (int(target[0]), int(target[1]))

        # BFS
        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            (x, y), path = queue.popleft()

            if (x, y) == target:
                return path[1:]  # Exclude current position

            # Try all directions
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy

                if (nx, ny) not in visited and maze.is_ghost_walkable(nx, ny):
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))

            # Limit search depth
            if len(visited) > 200:
                break

        return []

    def set_frightened(self):
        """Enter frightened mode."""
        self.mode = self.MODE_FRIGHTENED
        self.color = Color.BLUE
        self.speed = 4  # Slower when frightened

    def set_chase(self):
        """Enter chase mode."""
        self.mode = self.MODE_CHASE
        self.color = self.base_color
        self.speed = 8

    def set_scatter(self):
        """Enter scatter mode."""
        self.mode = self.MODE_SCATTER
        self.color = self.base_color
        self.speed = 8

    def die(self):
        """Ghost dies (returns to spawn)."""
        self.mode = self.MODE_DEAD
        self.color = Color.WHITE
        self.speed = 12  # Fast return to spawn

    def respawn(self):
        """Respawn at spawn position."""
        self.x, self.y = self.spawn_pos
        self.set_scatter()

    def get_char(self):
        """Get character representation."""
        if self.mode == self.MODE_DEAD:
            return 'x'
        elif self.mode == self.MODE_FRIGHTENED:
            return '~'
        return 'ᗣ'


class PacMan:
    """Main Pac-Man game class."""

    # Game states
    STATE_READY = 0
    STATE_PLAYING = 1
    STATE_POWER_UP = 2
    STATE_DEATH = 3
    STATE_VICTORY = 4
    STATE_GAME_OVER = 5

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Game state
        self.state = self.STATE_READY
        self.level = 1
        self.score = 0
        self.lives = 3

        # Maze
        self.maze = Maze()

        # Calculate offsets to center maze
        self.offset_x = (self.renderer.width - self.maze.width) // 2
        self.offset_y = (self.renderer.height - self.maze.height) // 2

        # Player
        self.player = Player(14, 20)
        self.next_direction = (0, 0)

        # Ghosts
        self.ghosts = [
            Ghost(12, 11, 'Blinky', Color.RED, (25, 1)),
            Ghost(14, 11, 'Pinky', Color.MAGENTA, (2, 1)),
            Ghost(13, 14, 'Inky', Color.CYAN, (25, 25)),
            Ghost(15, 14, 'Clyde', Color.YELLOW, (2, 25)),
        ]

        # Power-up
        self.power_up_timer = 0
        self.power_up_duration = 8.0  # seconds
        self.ghost_value = 200

        # Mode timer
        self.mode_timer = 0
        self.mode_durations = [7, 20, 7, 20, 5, 20, 5]  # Scatter/Chase alternation
        self.mode_index = 0

        # Ready timer
        self.ready_timer = 2.0

        # Frame timing
        self.last_time = time.time()

    def update(self, dt):
        """Update game state."""
        if self.state == self.STATE_READY:
            self.ready_timer -= dt
            if self.ready_timer <= 0:
                self.state = self.STATE_PLAYING

        elif self.state == self.STATE_PLAYING or self.state == self.STATE_POWER_UP:
            self._update_playing(dt)

        elif self.state == self.STATE_DEATH:
            time.sleep(1)
            self.lives -= 1

            if self.lives <= 0:
                self.state = self.STATE_GAME_OVER
            else:
                self._reset_positions()
                self.state = self.STATE_READY
                self.ready_timer = 2.0

    def _update_playing(self, dt):
        """Update during active gameplay."""
        # Update mode timer (scatter/chase alternation)
        self.mode_timer += dt
        if self.mode_index < len(self.mode_durations):
            if self.mode_timer >= self.mode_durations[self.mode_index]:
                self.mode_timer = 0
                self.mode_index += 1

                # Toggle mode
                if self.state != self.STATE_POWER_UP:
                    if self.mode_index % 2 == 0:
                        for ghost in self.ghosts:
                            if ghost.mode != Ghost.MODE_DEAD:
                                ghost.set_scatter()
                    else:
                        for ghost in self.ghosts:
                            if ghost.mode != Ghost.MODE_DEAD:
                                ghost.set_chase()

        # Update power-up timer
        if self.state == self.STATE_POWER_UP:
            self.power_up_timer -= dt
            if self.power_up_timer <= 0:
                self.state = self.STATE_PLAYING
                self.ghost_value = 200
                for ghost in self.ghosts:
                    if ghost.mode == Ghost.MODE_FRIGHTENED:
                        ghost.set_chase()

        # Update player
        self._update_player_movement(dt)
        self.player.update(dt)

        # Check pellet collection
        px, py = self.player.get_tile_pos()
        tile = self.maze.get_tile(px, py)

        if tile == Maze.PELLET:
            self.maze.set_tile(px, py, Maze.PATH)
            self.score += 10
        elif tile == Maze.POWER_PELLET:
            self.maze.set_tile(px, py, Maze.PATH)
            self.score += 50
            self._activate_power_up()

        # Update ghosts
        player_pos = self.player.get_tile_pos()
        for ghost in self.ghosts:
            ghost.update(dt, self.maze, player_pos, self.ghosts)

            # Check if ghost reached spawn (when dead)
            if ghost.mode == Ghost.MODE_DEAD:
                gx, gy = ghost.get_tile_pos()
                if (gx, gy) == ghost.spawn_pos:
                    ghost.respawn()

        # Check collisions
        self._check_collisions()

        # Check victory
        remaining_pellets = sum(row.count(Maze.PELLET) for row in self.maze.tiles)
        if remaining_pellets == 0:
            self.state = self.STATE_VICTORY

    def _update_player_movement(self, dt):
        """Update player movement based on input."""
        # Get input for next direction
        input_type = self.input_handler.get_input(timeout=0.001)

        if input_type == InputType.UP:
            self.next_direction = (0, -1)
        elif input_type == InputType.DOWN:
            self.next_direction = (0, 1)
        elif input_type == InputType.LEFT:
            self.next_direction = (-1, 0)
        elif input_type == InputType.RIGHT:
            self.next_direction = (1, 0)

        # Try to turn in next direction
        px, py = self.player.get_tile_pos()
        next_x = px + self.next_direction[0]
        next_y = py + self.next_direction[1]

        if self.maze.is_walkable(next_x, next_y):
            self.player.direction = self.next_direction

        # Stop if hit wall
        curr_x = px + self.player.direction[0]
        curr_y = py + self.player.direction[1]

        if not self.maze.is_walkable(curr_x, curr_y):
            # Align to tile and stop
            self.player.x = px
            self.player.y = py
            self.player.direction = (0, 0)

        # Wrap-around tunnels (left/right edges)
        if self.player.x < 0:
            self.player.x = self.maze.width - 1
        elif self.player.x >= self.maze.width:
            self.player.x = 0

    def _activate_power_up(self):
        """Activate power-up mode."""
        self.state = self.STATE_POWER_UP
        self.power_up_timer = self.power_up_duration
        self.ghost_value = 200

        for ghost in self.ghosts:
            if ghost.mode != Ghost.MODE_DEAD:
                ghost.set_frightened()

    def _check_collisions(self):
        """Check player-ghost collisions."""
        px, py = self.player.get_tile_pos()

        for ghost in self.ghosts:
            gx, gy = ghost.get_tile_pos()

            if (px, py) == (gx, gy):
                if ghost.mode == Ghost.MODE_FRIGHTENED:
                    # Eat ghost
                    self.score += self.ghost_value
                    self.ghost_value *= 2  # 200, 400, 800, 1600
                    ghost.die()
                elif ghost.mode != Ghost.MODE_DEAD:
                    # Player dies
                    self.state = self.STATE_DEATH
                    return

    def _reset_positions(self):
        """Reset player and ghost positions."""
        self.player.x, self.player.y = 14, 20
        self.player.direction = (0, 0)
        self.next_direction = (0, 0)

        for ghost in self.ghosts:
            ghost.respawn()

    def draw(self):
        """Draw the game."""
        self.renderer.clear_buffer()

        # Draw HUD
        self._draw_hud()

        # Draw maze
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                tile = self.maze.get_tile(x, y)
                screen_x = self.offset_x + x
                screen_y = self.offset_y + y

                if tile == Maze.WALL:
                    self.renderer.set_pixel(screen_x, screen_y, '█', Color.BLUE)
                elif tile == Maze.PELLET:
                    self.renderer.set_pixel(screen_x, screen_y, '·', Color.YELLOW)
                elif tile == Maze.POWER_PELLET:
                    # Blink power pellets
                    if int(time.time() * 2) % 2 == 0:
                        self.renderer.set_pixel(screen_x, screen_y, '●', Color.BRIGHT_WHITE)
                elif tile == Maze.GHOST_GATE:
                    self.renderer.set_pixel(screen_x, screen_y, '─', Color.MAGENTA)

        # Draw player
        px, py = self.player.get_tile_pos()
        self.renderer.set_pixel(self.offset_x + px, self.offset_y + py,
                                self.player.get_char(), Color.BRIGHT_YELLOW)

        # Draw ghosts
        for ghost in self.ghosts:
            gx, gy = ghost.get_tile_pos()
            self.renderer.set_pixel(self.offset_x + gx, self.offset_y + gy,
                                    ghost.get_char(), ghost.color)

        # Draw state messages
        if self.state == self.STATE_READY:
            msg = "READY!"
            self.renderer.draw_text(self.renderer.width // 2 - len(msg) // 2,
                                    self.renderer.height // 2, msg, Color.BRIGHT_YELLOW)

        elif self.state == self.STATE_VICTORY:
            msg = f"LEVEL {self.level} COMPLETE!"
            self.renderer.draw_text(self.renderer.width // 2 - len(msg) // 2,
                                    self.renderer.height // 2, msg, Color.BRIGHT_GREEN)

        elif self.state == self.STATE_GAME_OVER:
            msg = "GAME OVER"
            self.renderer.draw_text(self.renderer.width // 2 - len(msg) // 2,
                                    self.renderer.height // 2, msg, Color.BRIGHT_RED)
            score_msg = f"Score: {self.score}"
            self.renderer.draw_text(self.renderer.width // 2 - len(score_msg) // 2,
                                    self.renderer.height // 2 + 2, score_msg, Color.BRIGHT_WHITE)

        self.renderer.render()

    def _draw_hud(self):
        """Draw heads-up display."""
        # Score
        score_text = f"SCORE: {self.score}"
        self.renderer.draw_text(2, 1, score_text, Color.BRIGHT_WHITE)

        # Lives
        lives_text = f"LIVES: {'C ' * self.lives}"
        self.renderer.draw_text(self.renderer.width - len(lives_text) - 2, 1,
                                lives_text, Color.BRIGHT_YELLOW)

        # Power-up timer
        if self.state == self.STATE_POWER_UP:
            timer_text = f"POWER: {int(self.power_up_timer)}s"
            self.renderer.draw_text(self.renderer.width // 2 - len(timer_text) // 2, 1,
                                    timer_text, Color.BRIGHT_CYAN)

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
                        # Next level (for now, just restart)
                        self.level += 1
                        self.maze = Maze()
                        self._reset_positions()
                        self.state = self.STATE_READY
                        self.ready_timer = 2.0

                # Update
                self.update(dt)

                # Draw
                self.draw()

                # Frame rate (30 FPS)
                time.sleep(0.033)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_pacman():
    """Entry point for Pac-Man game."""
    game = PacMan()
    game.run()


if __name__ == "__main__":
    run_pacman()
