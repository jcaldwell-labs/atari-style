"""Claugger - Why did the chicken cross the road? A Frogger tribute."""

import time
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
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

DEATH_MESSAGES = [
    "Fowl play!",
    "Chicken tender!",
    "Poultry in motion... denied!",
    "That's not how you cross the road!",
    "Hen-ded!",
    "Clucked out!",
]

KONAMI_SEQUENCE = [
    InputType.UP, InputType.UP,
    InputType.DOWN, InputType.DOWN,
    InputType.LEFT, InputType.RIGHT,
    InputType.LEFT, InputType.RIGHT,
    InputType.SELECT, InputType.BACK,
]

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


@dataclass
class Egg:
    """An egg laid by the chicken on a lane.

    Args:
        x: Horizontal position of the egg.
        lane: Lane index where the egg was laid.
        attached_object: The river object this egg rides on, or None for road eggs.
        squashed: True when a vehicle has run over this egg.
        splat_timer: Elapsed time since squashing (for removal delay).
    """

    x: float
    lane: int
    attached_object: LaneObject = None
    squashed: bool = False
    splat_timer: float = 0.0


# ---------------------------------------------------------------------------
# Main game class
# ---------------------------------------------------------------------------


class Claugger:
    """Claugger game — a Frogger tribute in the terminal.

    Builds a 13-lane playing field with scrolling road and river objects.
    The chicken, collision detection, and egg mechanics are not yet present;
    this skeleton provides the world the chicken will inhabit.
    """

    # Game state constants
    STATE_TITLE = 0
    STATE_PLAYING = 1
    STATE_DYING = 2
    STATE_GAME_OVER = 3
    STATE_LEVEL_COMPLETE = 4
    STATE_READY = 5

    def __init__(self) -> None:
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.last_time: float = time.time()
        self.running: bool = True

        # Scoring / progression
        self.score: int = 0
        self.lives: int = 3
        self.level: int = 1
        self.timer: float = 60.0
        self.nests_filled: int = 0
        self.nests: List[bool] = [False] * 5

        # Tracks the highest lane reached this life (prevents re-scoring same lane)
        self.highest_lane_this_life: int = 0

        # Level-complete display timer
        self._level_complete_timer: float = 0.0

        self.lanes: List[Lane] = self._build_lanes(level=1)

        # Game state
        self.state: int = Claugger.STATE_TITLE

        # Chicken state
        self.chicken_x: int = (SCREEN_WIDTH - CHICKEN_WIDTH) // 2
        self.chicken_lane: int = 0
        self.chicken_facing: str = "up"
        self.chicken_frame: int = 0
        self.chicken_hop_timer: float = 0.0

        # Death animation state
        self.death_type: str = ""
        self.death_timer: float = 0.0
        self.death_message: str = ""

        # HUD message (level complete, etc.)
        self._hud_message: str = ""
        self._hud_message_timer: float = 0.0

        # Egg system
        self.eggs: List[Egg] = []
        self.total_eggs_laid: int = 0

        # Konami Code / Easter eggs
        self.input_buffer: list = []
        self.golden_rooster_active: bool = False
        self.golden_rooster_used: bool = False
        self.golden_rooster_timer: float = 5.0

        # Road Scholar achievement
        self.consecutive_deathless_levels: int = 0
        self.deaths_this_level: int = 0
        self.road_scholar_triggered: bool = False

    # ------------------------------------------------------------------
    # Easter egg helpers
    # ------------------------------------------------------------------

    def record_input(self, input_type: InputType) -> None:
        """Record an input into the Konami Code rolling buffer.

        Appends the input to a rolling buffer of the last 10 inputs. If the
        buffer matches the Konami sequence and the golden rooster has not been
        used this session, the golden rooster mode is activated.

        Args:
            input_type: The InputType value to record.
        """
        self.input_buffer.append(input_type)
        if len(self.input_buffer) > len(KONAMI_SEQUENCE):
            self.input_buffer = self.input_buffer[-len(KONAMI_SEQUENCE):]

        if (
            self.input_buffer == KONAMI_SEQUENCE
            and not self.golden_rooster_used
        ):
            self.golden_rooster_active = True
            self.golden_rooster_used = True
            self.golden_rooster_timer = 5.0
            self._hud_message = "COCKA-DOODLE-CHEAT!"
            self._hud_message_timer = 3.0

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
                # Award 10 points per new highest lane reached
                if dy > 0 and self.chicken_lane > self.highest_lane_this_life:
                    points = (self.chicken_lane - self.highest_lane_this_life) * 10
                    self.score += points
                    self.highest_lane_this_life = self.chicken_lane
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
            self.try_lay_egg()

    # ------------------------------------------------------------------
    # Egg system
    # ------------------------------------------------------------------

    def try_lay_egg(self) -> None:
        """Attempt to lay an egg with a 5% chance per hop.

        Eggs are not laid on SAFE, START, or GOAL lanes.
        """
        lane = self.lanes[self.chicken_lane]
        if lane.lane_type in (LaneType.SAFE, LaneType.START, LaneType.GOAL):
            return
        if random.random() < 0.05:
            self.lay_egg()

    def lay_egg(self) -> None:
        """Lay an egg at the chicken's current position.

        For RIVER lanes, the egg is attached to whichever object the chicken
        is standing on (so it scrolls with the object).  Increments
        total_eggs_laid and awards an extra life every 10 eggs.
        """
        lane = self.lanes[self.chicken_lane]
        attached: LaneObject = None

        if lane.lane_type == LaneType.RIVER:
            chicken_left = self.chicken_x
            chicken_right = self.chicken_x + CHICKEN_WIDTH
            for obj in lane.objects:
                obj_left = obj.x
                obj_right = obj.x + obj.width
                if chicken_left < obj_right and chicken_right > obj_left and not obj.is_diving:
                    attached = obj
                    break

        egg = Egg(x=float(self.chicken_x), lane=self.chicken_lane, attached_object=attached)
        self.eggs.append(egg)
        self.total_eggs_laid += 1

        if self.total_eggs_laid % 10 == 0:
            self.lives += 1
            self._hud_message = "EGGS-tra life!"
            self._hud_message_timer = 2.0

    def lay_egg_at(self, lane: int, x: float) -> None:
        """Place an egg deterministically at a given lane and x position.

        This helper is used by tests and special game events. It does not
        increment total_eggs_laid or check for extra-life milestones.

        Args:
            lane: Lane index for the egg.
            x: Horizontal position of the egg.
        """
        egg = Egg(x=x, lane=lane)
        self.eggs.append(egg)

    def update_eggs(self, dt: float) -> None:
        """Update all eggs: check for vehicle squashing and river scrolling.

        Road eggs: destroyed when a vehicle bounding box overlaps the egg x.
        River eggs: x position follows their attached_object; removed when the
        object scrolls off-screen.
        Squashed eggs linger for 0.5 s (splat animation) then are removed.

        Args:
            dt: Delta time in seconds since the last update.
        """
        eggs_to_remove = []

        for egg in self.eggs:
            if egg.squashed:
                egg.splat_timer += dt
                if egg.splat_timer >= 0.5:
                    eggs_to_remove.append(egg)
                continue

            lane = self.lanes[egg.lane]

            if lane.lane_type == LaneType.ROAD:
                for obj in lane.objects:
                    obj_left = obj.x
                    obj_right = obj.x + obj.width
                    # Egg is a single-character point; check if egg.x falls inside obj
                    if obj_left <= egg.x < obj_right:
                        egg.squashed = True
                        break

            elif lane.lane_type == LaneType.RIVER and egg.attached_object is not None:
                obj = egg.attached_object
                egg.x = obj.x
                # Remove if object scrolled fully off-screen
                if obj.x + obj.width < 0 or obj.x >= SCREEN_WIDTH:
                    eggs_to_remove.append(egg)

        for egg in eggs_to_remove:
            if egg in self.eggs:
                self.eggs.remove(egg)

    def score_eggs(self) -> int:
        """Score all surviving (non-squashed) eggs at 200 points each.

        Clears the egg list after scoring.

        Returns:
            Total points awarded for surviving eggs.
        """
        points = sum(200 for egg in self.eggs if not egg.squashed)
        self.eggs.clear()
        return points

    # ------------------------------------------------------------------
    # Collision detection
    # ------------------------------------------------------------------

    def _trigger_death(self, death_type: str) -> None:
        """Transition to STATE_DYING and track death count.

        Skip collision effects when golden rooster is active (invincibility).

        Args:
            death_type: "squash", "drown", or "timeout".
        """
        if self.golden_rooster_active:
            return
        self.state = Claugger.STATE_DYING
        self.death_type = death_type
        self.death_timer = 1.5
        self.death_message = random.choice(DEATH_MESSAGES)
        self.deaths_this_level += 1

    def check_collisions(self) -> None:
        """Check for collisions between the chicken and lane objects.

        Road lanes: any bounding-box overlap with a vehicle → STATE_DYING (squash).
        River lanes: chicken must overlap a non-diving object; if not → STATE_DYING
        (drown). Overlapping a diving turtle also → STATE_DYING (drown).
        Safe, Start, and Goal lanes have no hazard.
        """
        if self.state != Claugger.STATE_PLAYING:
            return

        lane = self.lanes[self.chicken_lane]
        chicken_left = self.chicken_x
        chicken_right = self.chicken_x + CHICKEN_WIDTH

        if lane.lane_type == LaneType.ROAD:
            for obj in lane.objects:
                obj_left = obj.x
                obj_right = obj.x + obj.width
                # Bounding box overlap: intervals overlap when left < other_right and right > other_left
                if chicken_left < obj_right and chicken_right > obj_left:
                    self._trigger_death("squash")
                    return

        elif lane.lane_type == LaneType.RIVER:
            # Check each object for overlap
            for obj in lane.objects:
                obj_left = obj.x
                obj_right = obj.x + obj.width
                if chicken_left < obj_right and chicken_right > obj_left:
                    # Overlapping an object — check if it's a diving turtle
                    if obj.is_diving:
                        self._trigger_death("drown")
                    # Otherwise safe — found a valid platform
                    return
            # No overlap with any object → drown
            self._trigger_death("drown")

    # ------------------------------------------------------------------
    # Nest filling and level progression
    # ------------------------------------------------------------------

    def fill_nest(self) -> None:
        """Fill the current nest when the chicken reaches the GOAL lane.

        Awards 50 base points plus a time bonus equal to twice the remaining
        timer seconds.  After filling, the chicken respawns at lane 0 without
        resetting the timer.  When all 5 nests are filled the game transitions
        to STATE_LEVEL_COMPLETE.
        """
        time_bonus = int(self.timer * 2)
        self.score += 50 + time_bonus

        self.nests[self.nests_filled] = True
        self.nests_filled += 1

        if self.nests_filled >= 5:
            self.score += self.score_eggs()
            self.state = Claugger.STATE_LEVEL_COMPLETE
            self._level_complete_timer = 2.0
            self._hud_message = f"EGG-cellent! Level {self.level} complete!"
            self._hud_message_timer = 2.0
        else:
            # Respawn without resetting the timer
            _saved_timer = self.timer
            self._respawn_chicken()
            self.timer = _saved_timer

    def next_level(self) -> None:
        """Advance to the next level, rebuilding lanes with increased speed.

        Increments the level counter, rebuilds lane objects scaled to the new
        level, resets nest state, resets the timer, and respawns the chicken.
        Also checks the Road Scholar achievement: 3 consecutive deathless levels
        award 5000 bonus points.
        """
        # Road Scholar tracking
        if self.deaths_this_level == 0:
            self.consecutive_deathless_levels += 1
        else:
            self.consecutive_deathless_levels = 0

        if self.consecutive_deathless_levels >= 3 and not self.road_scholar_triggered:
            self.road_scholar_triggered = True
            self.score += 5000
            self._hud_message = "Why did the chicken cross the road? To get to the other SIDE of knowledge!"
            self._hud_message_timer = 4.0

        self.deaths_this_level = 0

        self.level += 1
        self.lanes = self._build_lanes(self.level)
        self.nests = [False] * 5
        self.nests_filled = 0
        self._respawn_chicken()
        self.state = Claugger.STATE_PLAYING

    # ------------------------------------------------------------------
    # River riding
    # ------------------------------------------------------------------

    def update_river_riding(self, dt: float) -> None:
        """Shift the chicken along with any log or non-diving turtle it rides.

        Called only during STATE_PLAYING. If the chicken is in a RIVER lane
        and overlaps a non-diving object, the chicken is moved by the lane's
        scroll velocity for this frame.

        Args:
            dt: Delta time in seconds since the last update.
        """
        if self.state != Claugger.STATE_PLAYING:
            return

        lane = self.lanes[self.chicken_lane]
        if lane.lane_type != LaneType.RIVER:
            return

        chicken_left = self.chicken_x
        chicken_right = self.chicken_x + CHICKEN_WIDTH

        for obj in lane.objects:
            obj_left = obj.x
            obj_right = obj.x + obj.width
            if chicken_left < obj_right and chicken_right > obj_left and not obj.is_diving:
                drift = lane.speed * lane.direction * dt
                self.chicken_x += drift
                # Clamp to screen bounds
                self.chicken_x = max(0, min(SCREEN_WIDTH - CHICKEN_WIDTH, self.chicken_x))
                return

    # ------------------------------------------------------------------
    # Turtle dive updates
    # ------------------------------------------------------------------

    def update_turtle_dives(self, dt: float) -> None:
        """Advance turtle dive timers and toggle diving state when phases expire.

        Each turtle object toggles between surfaced (4 s default) and diving
        (2 s default) phases. The phase durations are fixed so tests can
        predict transitions reliably.

        Args:
            dt: Delta time in seconds since the last update.
        """
        for lane in self.lanes:
            if lane.lane_type != LaneType.RIVER:
                continue
            for obj in lane.objects:
                if TURTLE_CHAR not in obj.chars:
                    continue
                if obj.dive_phase <= 0:
                    continue
                obj.dive_timer += dt
                if obj.dive_timer >= obj.dive_phase:
                    obj.is_diving = not obj.is_diving
                    obj.dive_timer = 0.0
                    obj.dive_phase = 2.0 if obj.is_diving else 4.0

    # ------------------------------------------------------------------
    # Game loop helpers
    # ------------------------------------------------------------------

    def _respawn_chicken(self) -> None:
        """Reset the chicken to the starting position and restore the timer."""
        self.chicken_x = (SCREEN_WIDTH - CHICKEN_WIDTH) // 2
        self.chicken_lane = 0
        self.chicken_facing = "up"
        self.timer = 60.0
        self.highest_lane_this_life = 0

    def update(self, dt: float) -> None:
        """Advance game state for one frame.

        During STATE_PLAYING: scrolls lane objects, runs turtle dive timers,
        river riding, and collision detection.
        During STATE_DYING: counts down the death animation timer and
        transitions back to STATE_PLAYING (respawn) when it expires.

        Args:
            dt: Delta time in seconds since the last update.
        """
        if self.state == Claugger.STATE_DYING:
            self.death_timer -= dt
            if self.death_timer <= 0.0:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = Claugger.STATE_GAME_OVER
                else:
                    self._respawn_chicken()
                    self.state = Claugger.STATE_PLAYING
            return

        if self.state == Claugger.STATE_LEVEL_COMPLETE:
            self._level_complete_timer -= dt
            if self._level_complete_timer <= 0.0:
                self.next_level()
            return

        if self.state in (Claugger.STATE_TITLE, Claugger.STATE_GAME_OVER):
            return

        if self.state != Claugger.STATE_PLAYING:
            return

        # Golden rooster countdown (invincibility timer)
        if self.golden_rooster_active:
            self.golden_rooster_timer -= dt
            if self.golden_rooster_timer <= 0.0:
                self.golden_rooster_active = False

        # Count down egg timer
        self.timer -= dt
        if self.timer <= 0.0:
            self.timer = 0.0
            self._trigger_death("timeout")
            return

        # Decay HUD message timer
        if self._hud_message_timer > 0.0:
            self._hud_message_timer -= dt
            if self._hud_message_timer <= 0.0:
                self._hud_message = ""

        # Scroll lane objects
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

        # Update turtle dives, river riding, then collisions
        self.update_turtle_dives(dt)
        self.update_river_riding(dt)
        self.update_eggs(dt)
        self.check_collisions()

        # Auto-fill nest when chicken reaches the GOAL lane
        if self.state == Claugger.STATE_PLAYING and self.chicken_lane == LANE_COUNT - 1:
            self.fill_nest()

    def _draw_title_screen(self) -> None:
        """Render the title screen with ASCII art and prompt."""
        self.renderer.clear_buffer()
        term_height = self.renderer.height
        term_width = self.renderer.width

        title_art = [
            " ██████╗██╗      █████╗ ██╗   ██╗ ██████╗  ██████╗ ███████╗██████╗ ",
            "██╔════╝██║     ██╔══██╗██║   ██║██╔════╝ ██╔════╝ ██╔════╝██╔══██╗",
            "██║     ██║     ███████║██║   ██║██║  ███╗██║  ███╗█████╗  ██████╔╝",
            "██║     ██║     ██╔══██║██║   ██║██║   ██║██║   ██║██╔══╝  ██╔══██╗",
            "╚██████╗███████╗██║  ██║╚██████╔╝╚██████╔╝╚██████╔╝███████╗██║  ██║",
            " ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝",
        ]
        chicken_art = [
            "   >Q<   ",
            "   /|\\   ",
            "  / | \\  ",
        ]
        start_y = max(1, term_height // 2 - 8)

        for i, line in enumerate(title_art):
            x = max(0, (term_width - len(line)) // 2)
            self.renderer.draw_text(x, start_y + i, line, Color.BRIGHT_YELLOW)

        chk_y = start_y + len(title_art) + 1
        for i, line in enumerate(chicken_art):
            x = max(0, (term_width - len(line)) // 2)
            self.renderer.draw_text(x, chk_y + i, line, Color.BRIGHT_GREEN)

        tagline = "Why did the chicken cross the road?"
        press_enter = "Press ENTER to start"
        quit_hint = "Press Q to quit"

        tl_x = max(0, (term_width - len(tagline)) // 2)
        pe_x = max(0, (term_width - len(press_enter)) // 2)
        qi_x = max(0, (term_width - len(quit_hint)) // 2)

        self.renderer.draw_text(tl_x, chk_y + len(chicken_art) + 1, tagline, Color.CYAN)
        self.renderer.draw_text(pe_x, chk_y + len(chicken_art) + 3, press_enter, Color.BRIGHT_WHITE)
        self.renderer.draw_text(qi_x, chk_y + len(chicken_art) + 4, quit_hint, Color.BRIGHT_BLACK)

        self.renderer.render()

    def _draw_game_over_screen(self) -> None:
        """Render the game over screen with final stats."""
        self.renderer.clear_buffer()
        term_height = self.renderer.height
        term_width = self.renderer.width

        header = "THE ROOST IS COOKED"
        start_y = max(1, term_height // 2 - 6)

        h_x = max(0, (term_width - len(header)) // 2)
        self.renderer.draw_text(h_x, start_y, header, Color.BRIGHT_RED)

        stats = [
            f"Final Score:  {self.score:,}",
            f"Level Reached: {self.level}",
            f"Eggs Laid:    {self.total_eggs_laid}",
            f"Nests Filled: {self.nests_filled}",
        ]
        for i, stat in enumerate(stats):
            sx = max(0, (term_width - len(stat)) // 2)
            self.renderer.draw_text(sx, start_y + 2 + i, stat, Color.BRIGHT_WHITE)

        play_again = "Press ENTER to play again"
        pa_x = max(0, (term_width - len(play_again)) // 2)
        self.renderer.draw_text(pa_x, start_y + 2 + len(stats) + 2, play_again, Color.BRIGHT_GREEN)

        self.renderer.render()

    def _reset_game(self) -> None:
        """Reset all game state for a fresh playthrough."""
        self.score = 0
        self.lives = 3
        self.level = 1
        self.timer = 60.0
        self.nests_filled = 0
        self.nests = [False] * 5
        self.highest_lane_this_life = 0
        self._level_complete_timer = 0.0
        self.lanes = self._build_lanes(level=1)
        self.chicken_x = (SCREEN_WIDTH - CHICKEN_WIDTH) // 2
        self.chicken_lane = 0
        self.chicken_facing = "up"
        self.chicken_frame = 0
        self.chicken_hop_timer = 0.0
        self.death_type = ""
        self.death_timer = 0.0
        self.death_message = ""
        self._hud_message = ""
        self._hud_message_timer = 0.0
        self.eggs = []
        self.total_eggs_laid = 0
        self.input_buffer = []
        self.golden_rooster_active = False
        self.golden_rooster_used = False
        self.golden_rooster_timer = 5.0
        self.consecutive_deathless_levels = 0
        self.deaths_this_level = 0
        self.road_scholar_triggered = False

    def draw(self) -> None:
        """Render all lanes and their scrolling objects to the terminal buffer.

        Lanes are drawn bottom-to-top. Lane 0 (START) is at the bottom of the
        playing field; lane 12 (GOAL) is at the top.  A 1-row border and the
        HUD occupy the remaining rows.
        """
        if self.state == Claugger.STATE_TITLE:
            self._draw_title_screen()
            return

        if self.state == Claugger.STATE_GAME_OVER:
            self._draw_game_over_screen()
            return

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
        visual_lane = LANE_COUNT - 1 - self.chicken_lane
        lane_row_start = field_top + visual_lane * ROWS_PER_LANE
        sprite_top_row = lane_row_start
        sprite_bot_row = lane_row_start + 1

        if self.state == Claugger.STATE_DYING:
            # Death animation: show a flattened/splashed sprite
            if self.death_type == "squash":
                death_sprite = ["%X%", "~~~"]
            else:
                death_sprite = ["~o~", "~~~"]
            death_color = Color.BRIGHT_RED if self.death_type == "squash" else Color.CYAN
            if sprite_top_row < term_height - HUD_ROWS - 1:
                self.renderer.draw_text(int(self.chicken_x), sprite_top_row, death_sprite[0], death_color)
            if sprite_bot_row < term_height - HUD_ROWS - 1:
                self.renderer.draw_text(int(self.chicken_x), sprite_bot_row, death_sprite[1], death_color)
            # Centered death message
            if self.death_message:
                msg_x = max(0, (SCREEN_WIDTH - len(self.death_message)) // 2)
                msg_y = term_height // 2
                self.renderer.draw_text(msg_x, msg_y, self.death_message, Color.BRIGHT_YELLOW)
        else:
            sprite_rows = CHICKEN_SPRITES.get(self.chicken_facing, CHICKEN_SPRITES["idle"])
            chicken_color = Color.BRIGHT_YELLOW
            if sprite_top_row < term_height - HUD_ROWS - 1:
                self.renderer.draw_text(int(self.chicken_x), sprite_top_row, sprite_rows[0], chicken_color)
            if sprite_bot_row < term_height - HUD_ROWS - 1:
                self.renderer.draw_text(int(self.chicken_x), sprite_bot_row, sprite_rows[1], chicken_color)

        # Draw eggs
        for egg in self.eggs:
            visual_lane = LANE_COUNT - 1 - egg.lane
            egg_row = field_top + visual_lane * ROWS_PER_LANE + 1
            egg_x = int(egg.x)
            if 0 <= egg_x < SCREEN_WIDTH and egg_row < term_height - HUD_ROWS - 1:
                if egg.squashed:
                    self.renderer.set_pixel(egg_x, egg_row, "*", Color.BRIGHT_RED)
                else:
                    self.renderer.set_pixel(egg_x, egg_row, "o", Color.YELLOW)

        # HUD rows at the bottom
        hud_y = term_height - HUD_ROWS
        self.renderer.draw_text(0, hud_y, "─" * SCREEN_WIDTH, Color.BRIGHT_WHITE)

        # Row 1: Score (left), Level (center), Lives (right)
        score_text = f"EGGS-cellent: {self.score:,}"
        level_text = f"Crossing #{self.level}"
        lives_text = ">Q< " * self.lives

        level_x = max(0, (SCREEN_WIDTH - len(level_text)) // 2)
        lives_x = max(0, SCREEN_WIDTH - len(lives_text))

        self.renderer.draw_text(2, hud_y + 1, score_text, Color.BRIGHT_YELLOW)
        self.renderer.draw_text(level_x, hud_y + 1, level_text, Color.BRIGHT_CYAN)
        self.renderer.draw_text(lives_x, hud_y + 1, lives_text, Color.BRIGHT_GREEN)

        # Row 2: Egg timer bar + HUD message
        bar_width = 40
        filled = int(bar_width * max(0.0, self.timer) / 60.0)
        timer_bar = "█" * filled + "░" * (bar_width - filled)
        timer_label = f"Egg Timer: [{timer_bar}]"
        self.renderer.draw_text(2, hud_y + 2, timer_label, Color.BRIGHT_RED)

        if self._hud_message:
            msg_x = max(0, SCREEN_WIDTH - len(self._hud_message) - 2)
            self.renderer.draw_text(msg_x, hud_y + 2, self._hud_message, Color.BRIGHT_MAGENTA)

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

                # Always record input for Konami Code detection
                if input_type not in (InputType.NONE, None):
                    self.record_input(input_type)

                if input_type in (InputType.BACK, InputType.QUIT):
                    running = False
                elif self.state == Claugger.STATE_TITLE:
                    if input_type == InputType.SELECT:
                        self.state = Claugger.STATE_PLAYING
                elif self.state == Claugger.STATE_GAME_OVER:
                    if input_type == InputType.SELECT:
                        self._reset_game()
                        self.state = Claugger.STATE_TITLE
                elif self.state == Claugger.STATE_PLAYING:
                    if input_type == InputType.UP:
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
