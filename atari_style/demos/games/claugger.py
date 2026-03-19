"""Claugger - Why did the chicken cross the road? A Frogger tribute."""

import time
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import List
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANE_COUNT = 13          # Logical lanes in the game
ROWS_PER_LANE = 3        # Each lane renders as 3 terminal rows
HUD_ROWS = 3             # Score / status bar at the bottom
MIN_TERM_HEIGHT = 44     # LANE_COUNT * ROWS_PER_LANE + HUD_ROWS + 2 border
MIN_TERM_WIDTH = 80      # Classic 80-column terminal
TARGET_FPS = 30

SCREEN_WIDTH = 80        # Working column count

# ---------------------------------------------------------------------------
# Chicken sprite constants
# ---------------------------------------------------------------------------

CHICKEN_WIDTH = 3        # Character width of each sprite row

# Each entry is a list of 2 strings (top row, bottom row), each exactly
# CHICKEN_WIDTH characters wide.
CHICKEN_SPRITES = {
    "up":    [">^<", "/|\\"],
    "down":  ["\\|/", ">v<"],
    "left":  ["<(^", " )>"],
    "right": ["^)>", "<( "],
    "idle":  [">Q<", " ^ "],
}

# ---------------------------------------------------------------------------
# Vehicle / river-object ASCII art constants
# ---------------------------------------------------------------------------

CAR_SPRITES: List[str] = [
    "[==]",   # sedan
    "[##]",   # truck-like car
    "[<>]",   # sports car
    "[--]",   # flat car
]

TRUCK_SPRITES: List[str] = [
    "[====]",   # standard truck
    "[####]",   # heavy truck
    "[<===>]",  # long truck (7 chars — kept as-is, width varies)
]

MOTORCYCLE_SPRITES: List[str] = [
    "()>",
    "(*)",
]

LOG_CHAR = "="
TURTLE_CHAR = "@"

# ---------------------------------------------------------------------------
# Lane type enum
# ---------------------------------------------------------------------------


class LaneType(Enum):
    """Types of lanes in the Claugger playing field."""

    START = "start"    # Starting platform (bottom)
    ROAD = "road"      # Car/truck traffic
    SAFE = "safe"      # Median / safe island
    RIVER = "river"    # Logs and turtles
    GOAL = "goal"      # Lily-pad goal row (top)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class LaneObject:
    """A scrolling object within a lane (car, log, turtle group, etc.).

    Args:
        x: Horizontal position (float, may be negative during wrap).
        width: Character width of the object.
        chars: ASCII string representing the object's visual.
        color: Color constant string used for rendering.
        is_diving: True when this turtle group is submerged.
        dive_timer: Elapsed time in the current dive phase.
        dive_phase: Total duration of current dive phase (seconds).
    """

    x: float
    width: int
    chars: str
    color: str = Color.WHITE
    is_diving: bool = False
    dive_timer: float = 0.0
    dive_phase: float = 0.0


@dataclass
class Lane:
    """One logical lane of the playing field.

    Args:
        lane_type: Classification of this lane (ROAD, RIVER, etc.).
        speed: Scroll speed in characters per second.
        direction: +1 scrolls right, -1 scrolls left.
        objects: List of scrolling objects in this lane.
    """

    lane_type: LaneType
    speed: float
    direction: int
    objects: List[LaneObject] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Main game class
# ---------------------------------------------------------------------------


class Claugger:
    """Claugger game — a Frogger tribute in the terminal.

    Builds a 13-lane playing field with scrolling road and river objects.
    The chicken, collision detection, and egg mechanics are not yet present;
    this skeleton provides the world the chicken will inhabit.
    """

    def __init__(self) -> None:
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.lanes: List[Lane] = self._build_lanes(level=1)
        self.last_time: float = time.time()
        self.running: bool = True

        # Chicken state
        self.chicken_x: int = (SCREEN_WIDTH - CHICKEN_WIDTH) // 2
        self.chicken_lane: int = 0
        self.chicken_facing: str = "up"
        self.chicken_frame: int = 0
        self.chicken_hop_timer: float = 0.0

    # ------------------------------------------------------------------
    # Lane construction
    # ------------------------------------------------------------------

    def _build_lanes(self, level: int) -> List[Lane]:
        """Generate 13-lane configuration for the given level.

        Lane order, index 0 = bottom of screen:
          0        : START (home row)
          1–5      : ROAD  (5 traffic lanes)
          6        : SAFE  (median island)
          7–11     : RIVER (5 water lanes)
          12       : GOAL  (lily-pad finish row)

        Args:
            level: Current game level; higher levels increase speed.

        Returns:
            List of Lane objects ordered bottom-to-top.
        """
        speed_scale = 1.0 + (level - 1) * 0.2

        lanes: List[Lane] = []

        # --- Lane 0: START ---
        lanes.append(Lane(lane_type=LaneType.START, speed=0.0, direction=1))

        # --- Lanes 1–5: ROAD ---
        road_configs = [
            (2.0 * speed_scale, 1),
            (3.0 * speed_scale, -1),
            (2.5 * speed_scale, 1),
            (4.0 * speed_scale, -1),
            (3.5 * speed_scale, 1),
        ]
        for speed, direction in road_configs:
            lane = Lane(lane_type=LaneType.ROAD, speed=speed, direction=direction)
            density = 0.3 + (level - 1) * 0.05
            self._spawn_road_objects(lane, density)
            lanes.append(lane)

        # --- Lane 6: SAFE ---
        lanes.append(Lane(lane_type=LaneType.SAFE, speed=0.0, direction=1))

        # --- Lanes 7–11: RIVER ---
        river_configs = [
            (2.0 * speed_scale, 1),
            (2.5 * speed_scale, -1),
            (1.5 * speed_scale, 1),
            (3.0 * speed_scale, -1),
            (2.0 * speed_scale, 1),
        ]
        for speed, direction in river_configs:
            lane = Lane(lane_type=LaneType.RIVER, speed=speed, direction=direction)
            self._spawn_river_objects(lane)
            lanes.append(lane)

        # --- Lane 12: GOAL ---
        lanes.append(Lane(lane_type=LaneType.GOAL, speed=0.0, direction=1))

        return lanes

    def _spawn_road_objects(self, lane: Lane, density: float) -> None:
        """Populate a road lane with cars, trucks, and motorcycles.

        Objects are placed at random x positions across the screen width,
        spread out to avoid immediate overlap.

        Args:
            lane: The ROAD lane to populate.
            density: Float in [0, 1] controlling how many objects to spawn.
        """
        x = random.uniform(0, SCREEN_WIDTH)
        gap = SCREEN_WIDTH / max(1, int(density * 8))

        for _ in range(int(density * 8) + 1):
            roll = random.random()
            if roll < 0.5:
                sprite = random.choice(CAR_SPRITES)
                color = random.choice([Color.BRIGHT_RED, Color.YELLOW, Color.CYAN])
            elif roll < 0.75:
                sprite = random.choice(TRUCK_SPRITES)
                color = Color.BRIGHT_WHITE
            else:
                sprite = random.choice(MOTORCYCLE_SPRITES)
                color = Color.BRIGHT_MAGENTA

            obj = LaneObject(
                x=x % SCREEN_WIDTH,
                width=len(sprite),
                chars=sprite,
                color=color,
            )
            lane.objects.append(obj)
            x += gap + random.uniform(2, 6)

    def _spawn_river_objects(self, lane: Lane) -> None:
        """Populate a river lane with logs and turtle groups.

        Logs are longer platforms; turtle groups are shorter and can dive.

        Args:
            lane: The RIVER lane to populate.
        """
        x = random.uniform(0, SCREEN_WIDTH)

        for _ in range(random.randint(3, 5)):
            if random.random() < 0.5:
                # Log: 4–8 chars wide
                log_len = random.randint(4, 8)
                obj = LaneObject(
                    x=x % SCREEN_WIDTH,
                    width=log_len,
                    chars=LOG_CHAR * log_len,
                    color=Color.GREEN,
                )
            else:
                # Turtle group: 2–3 turtles
                count = random.randint(2, 3)
                obj = LaneObject(
                    x=x % SCREEN_WIDTH,
                    width=count,
                    chars=TURTLE_CHAR * count,
                    color=Color.BRIGHT_GREEN,
                    dive_phase=random.uniform(3.0, 6.0),
                )
            lane.objects.append(obj)
            x += random.uniform(8, 16)

    # ------------------------------------------------------------------
    # Chicken movement
    # ------------------------------------------------------------------

    def move_chicken(self, dx: int, dy: int) -> None:
        """Move the chicken by (dx, dy) steps, clamping to valid bounds.

        Lane numbers run 0 (bottom/start) to 12 (top/goal).  Moving up
        (toward the goal) passes dy=+1; moving down passes dy=-1.
        Horizontal steps move by CHICKEN_WIDTH characters.

        Args:
            dx: Horizontal direction: +1 right, -1 left, 0 no change.
            dy: Vertical direction: +1 up (higher lane), -1 down, 0 no change.
        """
        moved = False

        if dy != 0:
            new_lane = self.chicken_lane + dy
            new_lane = max(0, min(LANE_COUNT - 1, new_lane))
            if new_lane != self.chicken_lane:
                self.chicken_lane = new_lane
                moved = True
            if dy > 0:
                self.chicken_facing = "up"
            else:
                self.chicken_facing = "down"

        if dx != 0:
            new_x = self.chicken_x + dx * CHICKEN_WIDTH
            new_x = max(0, min(SCREEN_WIDTH - CHICKEN_WIDTH, new_x))
            if new_x != self.chicken_x:
                self.chicken_x = new_x
                moved = True
            if dx > 0:
                self.chicken_facing = "right"
            else:
                self.chicken_facing = "left"

        if moved:
            self.chicken_hop_timer = 0.1

    # ------------------------------------------------------------------
    # Game loop helpers
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance all scrolling lane objects and tick turtle dive timers.

        Args:
            dt: Delta time in seconds since the last update.
        """
        for lane in self.lanes:
            if lane.speed == 0.0:
                continue

            dx = lane.speed * lane.direction * dt

            for obj in lane.objects:
                obj.x += dx

                # Wrap around: right-scrolling objects exiting right edge
                if lane.direction == 1:
                    if obj.x >= SCREEN_WIDTH:
                        obj.x = -obj.width
                else:
                    # Left-scrolling: exit left edge → reappear at right
                    if obj.x + obj.width <= 0:
                        obj.x = float(SCREEN_WIDTH)

                # Turtle dive timer
                if obj.chars.startswith(TURTLE_CHAR) and obj.dive_phase > 0:
                    obj.dive_timer += dt
                    if obj.dive_timer >= obj.dive_phase:
                        obj.dive_timer = 0.0
                        obj.is_diving = not obj.is_diving
                        # Swap phase length for the next state
                        obj.dive_phase = (
                            random.uniform(1.5, 3.0)
                            if obj.is_diving
                            else random.uniform(3.0, 6.0)
                        )

    def draw(self) -> None:
        """Render all lanes and their scrolling objects to the terminal buffer.

        Lanes are drawn bottom-to-top. Lane 0 (START) is at the bottom of the
        playing field; lane 12 (GOAL) is at the top.  A 1-row border and the
        HUD occupy the remaining rows.
        """
        self.renderer.clear_buffer()

        term_height = self.renderer.height

        # Playing field starts just below the top border.
        # Lanes drawn from index 12 (top) to 0 (bottom).
        field_top = 1  # row 0 is top border

        # Lane colors by type
        lane_bg_colors = {
            LaneType.START: Color.GREEN,
            LaneType.ROAD: Color.BRIGHT_BLACK,
            LaneType.SAFE: Color.GREEN,
            LaneType.RIVER: Color.BLUE,
            LaneType.GOAL: Color.BRIGHT_GREEN,
        }

        for lane_idx in range(LANE_COUNT - 1, -1, -1):
            lane = self.lanes[lane_idx]
            # Visual row of the top of this lane (lanes render top-to-bottom)
            visual_lane = LANE_COUNT - 1 - lane_idx
            row_start = field_top + visual_lane * ROWS_PER_LANE

            if row_start >= term_height - HUD_ROWS - 1:
                break  # Don't overwrite HUD

            bg_color = lane_bg_colors.get(lane.lane_type, Color.WHITE)

            # Draw lane background (3 rows)
            bg_char = "~" if lane.lane_type == LaneType.RIVER else " "
            for row_offset in range(ROWS_PER_LANE):
                row = row_start + row_offset
                if row < term_height - HUD_ROWS - 1:
                    self.renderer.draw_text(0, row, bg_char * SCREEN_WIDTH, bg_color)

            # Draw objects on the middle row of each lane
            mid_row = row_start + 1
            if mid_row < term_height - HUD_ROWS - 1:
                for obj in lane.objects:
                    x = int(obj.x)
                    chars = obj.chars
                    # Submerged turtles show as water
                    if obj.is_diving:
                        chars = "~" * obj.width
                        color = Color.BLUE
                    else:
                        color = obj.color

                    for i, ch in enumerate(chars):
                        draw_x = x + i
                        if 0 <= draw_x < SCREEN_WIDTH:
                            self.renderer.set_pixel(draw_x, mid_row, ch, color)

        # Top border
        self.renderer.draw_text(0, 0, "─" * SCREEN_WIDTH, Color.BRIGHT_WHITE)

        # --- Chicken sprite ---
        sprite_rows = CHICKEN_SPRITES.get(self.chicken_facing, CHICKEN_SPRITES["idle"])
        # Calculate terminal row for the chicken's lane (same formula as lanes above)
        visual_lane = LANE_COUNT - 1 - self.chicken_lane
        lane_row_start = field_top + visual_lane * ROWS_PER_LANE
        # Center sprite vertically within the 3 rows of the lane (row offset 0 = top row,
        # 1 = middle row used for the bottom sprite row so both rows fit neatly)
        sprite_top_row = lane_row_start  # top row of sprite
        sprite_bot_row = lane_row_start + 1  # bottom row of sprite
        chicken_color = Color.BRIGHT_YELLOW
        if sprite_top_row < term_height - HUD_ROWS - 1:
            self.renderer.draw_text(self.chicken_x, sprite_top_row, sprite_rows[0], chicken_color)
        if sprite_bot_row < term_height - HUD_ROWS - 1:
            self.renderer.draw_text(self.chicken_x, sprite_bot_row, sprite_rows[1], chicken_color)

        # HUD rows at the bottom
        hud_y = term_height - HUD_ROWS
        self.renderer.draw_text(0, hud_y, "─" * SCREEN_WIDTH, Color.BRIGHT_WHITE)
        self.renderer.draw_text(
            2, hud_y + 1,
            "CLAUGGER  |  Arrows/WASD: Move  |  Q/ESC: Quit",
            Color.BRIGHT_YELLOW,
        )

        self.renderer.render()

    # ------------------------------------------------------------------
    # Terminal size check
    # ------------------------------------------------------------------

    def _check_terminal_size(self) -> bool:
        """Return True if the terminal meets the minimum dimensions.

        Returns:
            True when the terminal is large enough; False otherwise.
        """
        return (
            self.renderer.height >= MIN_TERM_HEIGHT
            and self.renderer.width >= MIN_TERM_WIDTH
        )

    def _wait_for_resize(self) -> bool:
        """Display a resize prompt and wait until dimensions are met or the
        user quits.

        Returns:
            True when the terminal is large enough; False if the user quit.
        """
        while True:
            self.renderer.clear_buffer()
            msg = f"Please resize your terminal to at least {MIN_TERM_WIDTH}x{MIN_TERM_HEIGHT}"
            cx = max(0, (self.renderer.width - len(msg)) // 2)
            cy = self.renderer.height // 2
            self.renderer.draw_text(cx, cy, msg, Color.BRIGHT_YELLOW)
            self.renderer.render()

            # Re-query dimensions on each check (blessed updates term.width/height)
            self.renderer.width = self.renderer.term.width
            self.renderer.height = self.renderer.term.height

            if self._check_terminal_size():
                return True

            input_type = self.input_handler.get_input(timeout=0.5)
            if input_type in (InputType.BACK, InputType.QUIT):
                return False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Enter fullscreen and run the game loop until the user quits."""
        self.renderer.enter_fullscreen()
        try:
            # Check terminal dimensions before starting
            if not self._check_terminal_size():
                if not self._wait_for_resize():
                    return

            self.last_time = time.time()
            running = True

            while running:
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time
                dt = min(dt, 0.1)  # Cap to avoid spiral of death

                input_type = self.input_handler.get_input(timeout=0.001)
                if input_type in (InputType.BACK, InputType.QUIT):
                    running = False
                elif input_type == InputType.UP:
                    self.move_chicken(0, 1)
                elif input_type == InputType.DOWN:
                    self.move_chicken(0, -1)
                elif input_type == InputType.LEFT:
                    self.move_chicken(-1, 0)
                elif input_type == InputType.RIGHT:
                    self.move_chicken(1, 0)

                self.update(dt)
                self.draw()
                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_claugger() -> None:
    """Launch the Claugger game.

    Example:
        >>> run_claugger()
    """
    game = Claugger()
    game.run()


if __name__ == "__main__":
    run_claugger()
