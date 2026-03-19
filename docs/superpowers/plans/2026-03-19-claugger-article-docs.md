# Claugger + Article + Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Frogger-style terminal game (Claugger), a late-90s Linux Journal blog article, project documentation, and a cross-repo publishing workflow — all serving issue #144 (project visibility).

**Architecture:** Article-driven development. The blog article is the spine — the game exists to prove its thesis, the docs exist so readers can go deeper. Claugger follows the existing game pattern (class with `__init__`, `update`, `draw`, `handle_input`, `run`) using `Renderer`/`InputHandler` from `atari_style.core`. Docs and blog are Hugo-compatible markdown published via cross-repo `repository_dispatch`.

**Tech Stack:** Python 3.8+, blessed (terminal rendering), pygame (joystick), Hugo + PaperMod (docs site), GitHub Actions (publishing)

**Spec:** `docs/superpowers/specs/2026-03-19-claugger-article-docs-design.md`

---

## File Map

### New Files

| File | Responsibility |
|------|----------------|
| `atari_style/demos/games/claugger.py` | Claugger game implementation (~900-1100 lines) |
| `tests/test_claugger.py` | Game unit tests (lanes, collision, eggs, scoring, easter eggs) |
| `docs/blog/2026-03-19-claugger-terminal-arcade.md` | Blog article (Hugo markdown) |
| `docs/site/atari-style/getting-started.md` | Quickstart guide |
| `docs/site/atari-style/architecture.md` | Architecture overview |
| `docs/site/atari-style/api-reference.md` | Core module API reference |
| `docs/site/atari-style/tutorial.md` | "Build Your First Game" tutorial |
| `docs/site/atari-style/contributing.md` | Contributor guide |
| `.github/workflows/publish-docs.yml` | Cross-repo dispatch workflow |

### Modified Files

| File | Change |
|------|--------|
| `atari_style/main.py` | Add Claugger to registry and menu |

---

## Task 1: Article Outline

Write the article outline first — this drives what the game needs to demonstrate and what the docs need to cover.

**Files:**
- Create: `docs/blog/2026-03-19-claugger-terminal-arcade.md`

- [ ] **Step 1: Create blog directory**

```bash
mkdir -p docs/blog
```

- [ ] **Step 2: Write the article outline with Hugo front matter**

Create `docs/blog/2026-03-19-claugger-terminal-arcade.md` with PaperMod front matter and section headers. Each section should have 2-3 bullet points capturing the key beats. The full prose comes later (Task 8) after the game is built and we have real code snippets to reference.

Front matter format:
```yaml
---
title: "Why Did the Chicken Cross the Terminal? Building Arcade Games Where Nobody Expected Them"
date: 2026-03-19
description: "A manifesto for terminal gaming and a walkthrough of building Claugger, a Frogger clone starring an ASCII chicken"
tags: ["python", "terminal", "gamedev", "ascii", "atari-style"]
author: "jcaldwell"
showToc: true
TocOpen: true
---
```

Sections per spec: Cold Open, The Thesis (Terminals as Canvas), The Toolkit, Building Claugger, The Bigger Picture, Closing.

- [ ] **Step 3: Commit**

```bash
git add docs/blog/2026-03-19-claugger-terminal-arcade.md
git commit -m "docs: Add article outline for Claugger terminal arcade post"
```

---

## Task 2: Claugger Game Skeleton + Lane System

Build the foundational game structure: class skeleton, lane data model, and scrolling objects. No chicken, no collision, no eggs yet — just the world the chicken will inhabit.

**Files:**
- Create: `atari_style/demos/games/claugger.py`
- Create: `tests/test_claugger.py`

- [ ] **Step 1: Write failing tests for lane data model**

Create `tests/test_claugger.py`. Test that:
- A `Lane` can be created with direction, speed, and lane type (ROAD/RIVER/SAFE/START/GOAL)
- Lane objects scroll horizontally and wrap around screen edges
- Road lanes contain vehicle objects with correct widths (car=4, truck=6, motorcycle=2)
- River lanes contain log objects (5-8 chars) and turtle groups (2-3 `@` chars)
- 13 lanes are created in correct order (start, 5 road, median, 5 river, goal)

```python
"""Tests for Claugger game."""

import random
import unittest
from atari_style.demos.games.claugger import (
    Lane, LaneType, LaneObject, Claugger,
    LANE_COUNT, ROWS_PER_LANE,
)


class TestLaneModel(unittest.TestCase):
    """Test lane data structures."""

    def test_lane_count(self):
        """13 logical lanes in the game."""
        self.assertEqual(LANE_COUNT, 13)

    def test_rows_per_lane(self):
        """Each lane renders as 3 terminal rows."""
        self.assertEqual(ROWS_PER_LANE, 3)

    def test_road_lane_creation(self):
        """Road lane has correct type and direction."""
        lane = Lane(lane_type=LaneType.ROAD, speed=2.0, direction=1)
        self.assertEqual(lane.lane_type, LaneType.ROAD)
        self.assertEqual(lane.direction, 1)

    def test_lane_object_wraps(self):
        """Objects wrap around when they scroll past screen edge."""
        obj = LaneObject(x=78.0, width=4, chars="AUTO")
        obj.x += 3  # Push past 80-col screen
        screen_width = 80
        if obj.x >= screen_width:
            obj.x = -obj.width
        self.assertEqual(obj.x, -4)

    def test_river_lane_creation(self):
        """River lane has correct type."""
        lane = Lane(lane_type=LaneType.RIVER, speed=1.5, direction=-1)
        self.assertEqual(lane.lane_type, LaneType.RIVER)


class TestTerminalSize(unittest.TestCase):
    """Test terminal size requirements."""

    def test_min_dimensions_constants(self):
        """Game defines minimum terminal dimensions."""
        from atari_style.demos.games.claugger import MIN_TERM_HEIGHT, MIN_TERM_WIDTH
        self.assertEqual(MIN_TERM_HEIGHT, 44)
        self.assertEqual(MIN_TERM_WIDTH, 80)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m unittest tests.test_claugger -v
```

Expected: ImportError — `claugger` module doesn't exist yet.

- [ ] **Step 3: Implement game skeleton with lane system**

Create `atari_style/demos/games/claugger.py` with:

1. Module docstring, imports (`time`, `random`, `Renderer`, `Color`, `InputHandler`, `InputType`)
2. Constants: `LANE_COUNT = 13`, `ROWS_PER_LANE = 3`, `HUD_ROWS = 3`, `MIN_TERM_HEIGHT = 44`, `MIN_TERM_WIDTH = 80`, `TARGET_FPS = 30`
3. `LaneType` enum: `START`, `ROAD`, `SAFE`, `RIVER`, `GOAL`
4. `LaneObject` dataclass: `x: float`, `width: int`, `chars: str`, `color: str`, `is_diving: bool = False`, `dive_timer: float = 0.0`, `dive_phase: float = 0.0` (for turtles)
5. `Lane` dataclass: `lane_type: LaneType`, `speed: float`, `direction: int` (+1 right, -1 left), `objects: list[LaneObject]`
6. `Claugger` class with:
   - `__init__()`: create Renderer, InputHandler, build 13 lanes with objects, init game state
   - `_build_lanes(level: int) -> list[Lane]`: generate lane configuration for given level
   - `_spawn_road_objects(lane, density)`: populate road lane with cars/trucks/motorcycles
   - `_spawn_river_objects(lane)`: populate river lane with logs and turtle groups
   - `update(dt)`: scroll all lane objects, handle wrap-around, tick turtle dive timers
   - `draw()`: render lanes and objects (no chicken yet)
   - `run()`: main loop skeleton (enter_fullscreen, loop with dt calc, exit_fullscreen in finally). On startup, check terminal dimensions against `MIN_TERM_HEIGHT` and `MIN_TERM_WIDTH` — if too small, display "Please resize your terminal to at least 80x44" and wait for resize before proceeding.
   - `run_claugger()` entry function
7. Vehicle ASCII art constants:
   - `CAR_SPRITES`: list of 4-char vehicle strings (e.g., `">==>"`, `"<##<"`, `"[==]"`)
   - `TRUCK_SPRITES`: list of 6-char truck strings (e.g., `">====>"`  `"<####<"`)
   - `MOTORCYCLE_SPRITES`: list of 2-char sprites (e.g., `"o>"`, `"<o"`)
   - `LOG_CHAR = "="`, `TURTLE_CHAR = "@"`

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m unittest tests.test_claugger -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add atari_style/demos/games/claugger.py tests/test_claugger.py
git commit -m "feat(claugger): Add game skeleton with lane system and scrolling objects"
```

---

## Task 3: Chicken Sprite + Movement

Add the chicken character with directional sprites, movement between lanes (instantaneous snap), and basic input handling.

**Files:**
- Modify: `atari_style/demos/games/claugger.py`
- Modify: `tests/test_claugger.py`

- [ ] **Step 1: Write failing tests for chicken movement**

Add to `tests/test_claugger.py`:

```python
class TestChicken(unittest.TestCase):
    """Test chicken sprite and movement."""

    def test_chicken_starts_at_lane_1(self):
        """Chicken starts in the henhouse (lane 0, bottom)."""
        game = Claugger()
        self.assertEqual(game.chicken_lane, 0)

    def test_chicken_moves_up(self):
        """Moving up increments lane by 1."""
        game = Claugger()
        game.move_chicken(0, 1)  # dx=0, dy=1 (up)
        self.assertEqual(game.chicken_lane, 1)

    def test_chicken_cannot_move_below_start(self):
        """Chicken cannot move below lane 0."""
        game = Claugger()
        game.move_chicken(0, -1)
        self.assertEqual(game.chicken_lane, 0)

    def test_chicken_cannot_move_above_goal(self):
        """Chicken cannot move above lane 12."""
        game = Claugger()
        game.chicken_lane = 12
        game.move_chicken(0, 1)
        self.assertEqual(game.chicken_lane, 12)

    def test_chicken_horizontal_movement(self):
        """Chicken can move left and right within screen bounds."""
        game = Claugger()
        start_x = game.chicken_x
        game.move_chicken(1, 0)
        self.assertEqual(game.chicken_x, start_x + 3)  # 3 = sprite width

    def test_chicken_has_facing_direction(self):
        """Chicken facing changes with movement."""
        game = Claugger()
        game.move_chicken(0, 1)
        self.assertEqual(game.chicken_facing, "up")
        game.move_chicken(1, 0)
        self.assertEqual(game.chicken_facing, "right")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m unittest tests.test_claugger.TestChicken -v
```

Expected: AttributeError — chicken attributes don't exist yet.

- [ ] **Step 3: Implement chicken sprite and movement**

Add to `claugger.py`:

1. `CHICKEN_SPRITES` dict with directional 3x2 ASCII art:
   ```python
   CHICKEN_SPRITES = {
       "up":    [r" /\ ", r"/~~\\"],
       "down":  [r" \/ ", r"\\__/"],
       "left":  [r"<\\ ", r" \\>"],
       "right": [r" //>" , r"<// "],
       "idle":  [r" >Q<", r" /\\ "],
   }
   ```
   (Exact art will be refined during implementation — these are placeholders showing the 3x2 structure)

2. Chicken state in `__init__`:
   - `self.chicken_x: int` — horizontal position (column)
   - `self.chicken_lane: int` — current lane (0-12)
   - `self.chicken_facing: str` — "up", "down", "left", "right", "idle"
   - `self.chicken_frame: int` — animation frame (0 or 1)
   - `self.chicken_hop_timer: float` — brief visual hop countdown

3. `move_chicken(dx, dy)` method:
   - Validate bounds: lane 0-12, x within screen
   - Update `chicken_lane` atomically (instantaneous snap per spec)
   - Update `chicken_facing` based on direction
   - Set `chicken_hop_timer = 0.1` for 2-frame visual

4. Update `handle_input()` to call `move_chicken()` on arrow keys
5. Update `draw()` to render chicken sprite at correct position

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m unittest tests.test_claugger -v
```

Expected: All tests PASS (both TestLaneModel and TestChicken).

- [ ] **Step 5: Commit**

```bash
git add atari_style/demos/games/claugger.py tests/test_claugger.py
git commit -m "feat(claugger): Add chicken sprite with directional movement and lane snapping"
```

---

## Task 4: Collision Detection + Death Animations

Add collision between chicken and vehicles (death on road), water (death if not on log/turtle), and riding mechanics on river objects.

**Files:**
- Modify: `atari_style/demos/games/claugger.py`
- Modify: `tests/test_claugger.py`

- [ ] **Step 1: Write failing tests for collision**

```python
class TestCollision(unittest.TestCase):
    """Test collision detection."""

    def test_road_collision_kills_chicken(self):
        """Chicken dies when overlapping a vehicle."""
        game = Claugger()
        game.chicken_lane = 1  # First road lane
        # Place a car directly on the chicken
        game.lanes[1].objects[0].x = float(game.chicken_x)
        game.check_collisions()
        self.assertEqual(game.state, Claugger.STATE_DYING)

    def test_no_collision_when_not_overlapping(self):
        """Chicken is safe when no vehicle overlap."""
        game = Claugger()
        game.chicken_lane = 1
        # Move all objects far from chicken
        for obj in game.lanes[1].objects:
            obj.x = -20.0
        game.check_collisions()
        self.assertNotEqual(game.state, Claugger.STATE_DYING)

    def test_river_no_object_kills_chicken(self):
        """Chicken drowns when on river lane without a log/turtle."""
        game = Claugger()
        game.chicken_lane = 7  # First river lane
        # Move all objects away
        for obj in game.lanes[7].objects:
            obj.x = -20.0
        game.check_collisions()
        self.assertEqual(game.state, Claugger.STATE_DYING)

    def test_river_on_log_is_safe(self):
        """Chicken is safe when standing on a log."""
        game = Claugger()
        game.chicken_lane = 7
        # Place a log under the chicken
        game.lanes[7].objects[0].x = float(game.chicken_x)
        game.lanes[7].objects[0].width = 6
        game.check_collisions()
        self.assertNotEqual(game.state, Claugger.STATE_DYING)

    def test_chicken_rides_log(self):
        """Chicken moves with the log it's standing on."""
        game = Claugger()
        game.chicken_lane = 7
        game.lanes[7].objects[0].x = float(game.chicken_x)
        game.lanes[7].objects[0].width = 6
        start_x = game.chicken_x
        game.update_river_riding(0.1)
        # Chicken x should have shifted by lane speed * direction * dt
        self.assertNotEqual(game.chicken_x, start_x)

    def test_turtle_dive_kills_chicken(self):
        """Chicken drowns when turtle it's on dives."""
        game = Claugger()
        game.chicken_lane = 7
        turtle = game.lanes[7].objects[0]
        turtle.x = float(game.chicken_x)
        turtle.is_diving = True
        game.check_collisions()
        self.assertEqual(game.state, Claugger.STATE_DYING)

    def test_collision_uses_bounding_box(self):
        """Collision checks full 3x2 sprite area."""
        game = Claugger()
        game.chicken_lane = 1
        # Place car overlapping just the right edge of the chicken
        game.lanes[1].objects[0].x = float(game.chicken_x + 2)  # Overlaps rightmost col
        game.lanes[1].objects[0].width = 4
        game.check_collisions()
        self.assertEqual(game.state, Claugger.STATE_DYING)

    def test_turtle_dive_cycle_timing(self):
        """Turtles dive for 2s and surface for 4s."""
        game = Claugger()
        # Find a turtle object in a river lane
        turtle = None
        for lane in game.lanes:
            if lane.lane_type == LaneType.RIVER:
                for obj in lane.objects:
                    if obj.chars and "@" in obj.chars:
                        turtle = obj
                        break
            if turtle:
                break
        if turtle is None:
            self.skipTest("No turtle found in lanes")
        # Surface phase should be 4 seconds
        turtle.is_diving = False
        turtle.dive_timer = 0.0
        game.update_turtle_dives(4.0)
        self.assertTrue(turtle.is_diving)
        # Dive phase should last 2 seconds
        turtle.dive_timer = 0.0
        game.update_turtle_dives(2.0)
        self.assertFalse(turtle.is_diving)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m unittest tests.test_claugger.TestCollision -v
```

Expected: AttributeError — `check_collisions` and `STATE_DYING` don't exist.

- [ ] **Step 3: Implement collision detection and death states**

Add to `claugger.py`:

1. Game states as class constants:
   ```python
   STATE_TITLE = 0
   STATE_PLAYING = 1
   STATE_DYING = 2
   STATE_GAME_OVER = 3
   STATE_LEVEL_COMPLETE = 4
   STATE_READY = 5
   ```

2. `check_collisions()` method:
   - Get current lane by `self.chicken_lane`
   - If lane is ROAD: check bounding box overlap between chicken (x, x+3) and each vehicle object (obj.x, obj.x+obj.width). Any overlap → `STATE_DYING`
   - If lane is RIVER: check if chicken bounding box overlaps any non-diving object. If no overlap with any object → `STATE_DYING` (drowning). If on a diving turtle → `STATE_DYING`
   - SAFE, START, GOAL lanes: no collision

3. `update_river_riding(dt)` method:
   - If on a river lane and overlapping a log/turtle, shift `chicken_x` by `lane.speed * lane.direction * dt`

4. Death animation state:
   - `self.death_type`: "squash", "drown", "timeout"
   - `self.death_timer: float` — counts down death animation (1.5 seconds)
   - Death animation sprites per type
   - `DEATH_MESSAGES` list for rotating puns
   - After death timer expires: decrement lives, respawn at lane 0, or STATE_GAME_OVER if lives == 0

5. `update_turtle_dives(dt)` method:
   - Each turtle group has a `dive_timer` that counts up
   - When surfaced (`is_diving=False`): after 4 seconds, set `is_diving=True`, reset timer
   - When diving (`is_diving=True`): after 2 seconds, set `is_diving=False`, reset timer
   - Initial `dive_phase` offsets stagger groups so they don't all dive at once

6. Update `update(dt)` to call `check_collisions()` and `update_turtle_dives(dt)` during STATE_PLAYING, handle STATE_DYING countdown.
7. Update `draw()` to render death animation and message when STATE_DYING. Hide diving turtles.

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m unittest tests.test_claugger -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add atari_style/demos/games/claugger.py tests/test_claugger.py
git commit -m "feat(claugger): Add collision detection, death animations, and river riding"
```

---

## Task 5: Scoring, Lives, Timer, and HUD

Add the scoring system, lives, egg timer countdown, nest filling, level progression, and the pun-filled HUD.

**Files:**
- Modify: `atari_style/demos/games/claugger.py`
- Modify: `tests/test_claugger.py`

- [ ] **Step 1: Write failing tests for scoring and game progression**

```python
class TestScoring(unittest.TestCase):
    """Test scoring, lives, and level progression."""

    def test_initial_score_is_zero(self):
        game = Claugger()
        self.assertEqual(game.score, 0)

    def test_initial_lives_is_three(self):
        game = Claugger()
        self.assertEqual(game.lives, 3)

    def test_forward_hop_awards_points(self):
        """Moving forward awards 10 points per lane."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.move_chicken(0, 1)
        self.assertEqual(game.score, 10)

    def test_reaching_nest_awards_bonus(self):
        """Filling a nest awards 50 points + time bonus."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.chicken_lane = 12
        game.fill_nest()
        self.assertGreater(game.score, 50)

    def test_five_nests_completes_level(self):
        """Filling all 5 nests triggers level complete."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.nests_filled = 4
        game.chicken_lane = 12
        game.fill_nest()
        self.assertEqual(game.state, Claugger.STATE_LEVEL_COMPLETE)

    def test_timer_resets_on_death(self):
        """Timer resets when chicken respawns."""
        game = Claugger()
        game.timer = 30.0
        game.respawn_chicken()
        self.assertEqual(game.timer, 60.0)

    def test_timer_does_not_reset_on_nest_fill(self):
        """Timer keeps running when a nest is filled mid-level."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.timer = 30.0
        game.chicken_lane = 12
        game.fill_nest()
        self.assertLessEqual(game.timer, 30.0)

    def test_level_progression_increases_speed(self):
        """Higher levels have faster lane speeds."""
        game = Claugger()
        level1_speeds = [l.speed for l in game.lanes if l.lane_type == LaneType.ROAD]
        game.next_level()
        level2_speeds = [l.speed for l in game.lanes if l.lane_type == LaneType.ROAD]
        self.assertTrue(all(s2 > s1 for s1, s2 in zip(level1_speeds, level2_speeds)))

    def test_timer_expiry_kills_chicken(self):
        """Chicken dies when timer reaches zero."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.timer = 0.01
        game.update(0.02)
        self.assertEqual(game.state, Claugger.STATE_DYING)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m unittest tests.test_claugger.TestScoring -v
```

- [ ] **Step 3: Implement scoring, lives, timer, nests, and HUD**

Add to `claugger.py`:

1. Game state in `__init__`:
   - `self.score = 0`
   - `self.lives = 3`
   - `self.level = 1`
   - `self.timer = 60.0`
   - `self.nests_filled = 0`
   - `self.nests = [False] * 5` — tracks which nest positions are filled
   - `self.highest_lane_this_life = 0` — prevents re-scoring same lane

2. Scoring rules in `move_chicken()`:
   - Award 10 points per new forward lane reached (track with `highest_lane_this_life`)
   - Reset `highest_lane_this_life` on respawn

3. `fill_nest()` method:
   - Award 50 points + (remaining_timer * 2) time bonus
   - Mark nest as filled
   - If all 5 nests filled → `STATE_LEVEL_COMPLETE`
   - Respawn chicken at lane 0

4. `respawn_chicken()`: reset position, timer to 60.0, `highest_lane_this_life` to 0
5. `next_level()`: increment level, rebuild lanes with `_build_lanes(self.level)`, reset nests, reset timer

6. Timer in `update(dt)`:
   - Decrement `self.timer -= dt` during STATE_PLAYING
   - If timer <= 0: death by timeout

7. HUD in `draw()`:
   - Top 3 rows of screen:
   - Row 0: `"EGGS-cellent: {score:,}"` left, `"Crossing #{level}"` center, `">Q< " * lives` right
   - Row 1: egg timer bar (visual bar that shrinks from 40 chars to 0 as timer drains)
   - Row 2: death message or level complete message (fades after 2 seconds)

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m unittest tests.test_claugger -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add atari_style/demos/games/claugger.py tests/test_claugger.py
git commit -m "feat(claugger): Add scoring, lives, timer, nest filling, and HUD"
```

---

## Task 6: Egg-Laying Bonus System

Add the egg-laying mechanic: 5% chance per hop, lane persistence, vehicle squashing, river scrolling, and the EGGS-tra life bonus.

**Files:**
- Modify: `atari_style/demos/games/claugger.py`
- Modify: `tests/test_claugger.py`

- [ ] **Step 1: Write failing tests for egg mechanics**

```python
class TestEggs(unittest.TestCase):
    """Test egg-laying bonus system."""

    def test_egg_not_laid_on_safe_median(self):
        """No eggs on safe zones."""
        game = Claugger()
        game.chicken_lane = 6  # Safe median
        game.try_lay_egg()
        self.assertEqual(len(game.eggs), 0)

    def test_egg_laid_on_road(self):
        """Eggs can be laid on road lanes."""
        game = Claugger()
        game.chicken_lane = 1
        random.seed(42)  # Seed for deterministic test
        # Force lay by calling with override
        game.lay_egg()
        self.assertEqual(len(game.eggs), 1)
        self.assertEqual(game.eggs[0].lane, 1)

    def test_egg_on_river_scrolls_with_object(self):
        """Eggs on river objects move with the object."""
        game = Claugger()
        game.chicken_lane = 7
        # Place chicken on a log
        log = game.lanes[7].objects[0]
        log.x = float(game.chicken_x)
        game.lay_egg()
        egg = game.eggs[0]
        self.assertIsNotNone(egg.attached_object)

    def test_egg_squashed_by_vehicle(self):
        """Vehicles destroy eggs on road lanes."""
        game = Claugger()
        game.chicken_lane = 1
        game.lay_egg()
        egg = game.eggs[0]
        # Move a vehicle onto the egg
        game.lanes[1].objects[0].x = egg.x
        game.update_eggs(0.1)
        self.assertTrue(egg.squashed)

    def test_ten_eggs_award_extra_life(self):
        """Collecting 10 eggs gives an extra life."""
        game = Claugger()
        game.total_eggs_laid = 9
        game.lay_egg()
        self.assertEqual(game.lives, 4)  # Started with 3

    def test_eggs_award_points_on_level_complete(self):
        """Surviving eggs are worth 200 points each on level complete."""
        game = Claugger()
        game.lay_egg_at(lane=1, x=10)
        game.lay_egg_at(lane=2, x=20)
        points = game.score_eggs()
        self.assertEqual(points, 400)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m unittest tests.test_claugger.TestEggs -v
```

- [ ] **Step 3: Implement egg system**

Add to `claugger.py`:

1. `Egg` dataclass: `x: float`, `lane: int`, `attached_object: LaneObject | None`, `squashed: bool = False`, `splat_timer: float = 0.0`
2. Game state: `self.eggs: list[Egg] = []`, `self.total_eggs_laid = 0`
3. `try_lay_egg()`: 5% random chance, calls `lay_egg()` if successful. No eggs on SAFE, START, or GOAL lanes.
4. `lay_egg()`: create Egg at chicken position. If on river, attach to the log/turtle object.
5. `lay_egg_at(lane, x)`: helper for deterministic egg placement (used by tests and Konami Code).
6. `update_eggs(dt)`:
   - Road eggs: check collision with vehicles → set `squashed = True`, start splat animation
   - River eggs: move with attached object. If object off-screen, remove egg.
   - Remove squashed eggs after splat animation (0.5s)
7. `score_eggs() -> int`: count non-squashed eggs × 200 points. Called on level complete.
8. EGGS-tra life check: when `total_eggs_laid` reaches 10, 20, 30... award extra life.
9. Hook into `move_chicken()`: call `try_lay_egg()` on each hop.
10. Hook into `fill_nest()` / level complete: call `score_eggs()`.
11. Draw eggs as `"o"` on screen, squashed eggs as `"*"` briefly.

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m unittest tests.test_claugger -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add atari_style/demos/games/claugger.py tests/test_claugger.py
git commit -m "feat(claugger): Add egg-laying bonus system with road squashing and river scrolling"
```

---

## Task 7: Easter Eggs + Title Screen + Game Over

Add the Konami Code golden rooster, Road Scholar achievement, title screen, and game over screen.

**Files:**
- Modify: `atari_style/demos/games/claugger.py`
- Modify: `tests/test_claugger.py`

- [ ] **Step 1: Write failing tests for easter eggs**

```python
class TestEasterEggs(unittest.TestCase):
    """Test easter egg triggers."""

    def test_konami_code_detection(self):
        """Konami sequence activates golden rooster."""
        game = Claugger()
        sequence = [
            InputType.UP, InputType.UP,
            InputType.DOWN, InputType.DOWN,
            InputType.LEFT, InputType.RIGHT,
            InputType.LEFT, InputType.RIGHT,
            InputType.SELECT, InputType.BACK,
        ]
        for inp in sequence:
            game.record_input(inp)
        self.assertTrue(game.golden_rooster_active)

    def test_konami_code_single_use(self):
        """Golden rooster can only be triggered once per session."""
        game = Claugger()
        game.golden_rooster_used = True
        sequence = [
            InputType.UP, InputType.UP,
            InputType.DOWN, InputType.DOWN,
            InputType.LEFT, InputType.RIGHT,
            InputType.LEFT, InputType.RIGHT,
            InputType.SELECT, InputType.BACK,
        ]
        for inp in sequence:
            game.record_input(inp)
        self.assertFalse(game.golden_rooster_active)

    def test_road_scholar_triggers_after_3_deathless_levels(self):
        """Road Scholar triggers after completing 3 levels without dying."""
        game = Claugger()
        game.consecutive_deathless_levels = 2
        game.next_level()
        self.assertTrue(game.road_scholar_triggered)

    def test_road_scholar_awards_bonus(self):
        """Road Scholar awards 5000 points."""
        game = Claugger()
        game.consecutive_deathless_levels = 2
        score_before = game.score
        game.next_level()
        self.assertEqual(game.score - score_before, 5000)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m unittest tests.test_claugger.TestEasterEggs -v
```

- [ ] **Step 3: Implement easter eggs, title screen, and game over**

Add to `claugger.py`:

1. Konami Code tracker:
   - `KONAMI_SEQUENCE` constant
   - `self.input_buffer: list[InputType]` — rolling buffer of last 10 inputs
   - `record_input(input_type)`: append to buffer, check if tail matches KONAMI_SEQUENCE
   - `self.golden_rooster_active = False`, `self.golden_rooster_used = False`, `self.golden_rooster_timer = 5.0`
   - When active: swap chicken sprites for golden variants (yellow colored), invincibility for 5s, lay golden eggs (500 pts each)

2. Road Scholar tracker:
   - `self.consecutive_deathless_levels = 0`
   - `self.deaths_this_level = 0`
   - On death: `deaths_this_level += 1`
   - On level complete: if `deaths_this_level == 0`: increment `consecutive_deathless_levels`. If reaches 3: trigger Road Scholar.
   - `self.road_scholar_triggered = False`
   - Road Scholar animation: brief diploma ASCII art, "ROAD SCHOLAR" text, 5000 points

3. Title screen (STATE_TITLE):
   - Large ASCII art "CLAUGGER" title
   - Chicken ASCII art
   - "Press ENTER to start" / "Why did the chicken cross the road?"
   - Konami Code works here

4. Game over screen (STATE_GAME_OVER):
   - "THE ROOST IS COOKED"
   - Final stats: score, level reached, eggs laid, nests filled
   - "Press ENTER to play again"

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m unittest tests.test_claugger -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add atari_style/demos/games/claugger.py tests/test_claugger.py
git commit -m "feat(claugger): Add easter eggs, title screen, and game over screen"
```

---

## Task 8: Menu Registration + Integration Test

Register Claugger in ContentRegistry and main menu. Verify the game launches from the menu.

**Files:**
- Modify: `atari_style/main.py`
- Modify: `atari_style/demos/games/claugger.py`

- [ ] **Step 1: Write failing test for registry integration**

Add to `tests/test_claugger.py`:

```python
class TestRegistration(unittest.TestCase):
    """Test Claugger registration in ContentRegistry."""

    def test_claugger_importable(self):
        """run_claugger function is importable."""
        from atari_style.demos.games.claugger import run_claugger
        self.assertTrue(callable(run_claugger))

    def test_claugger_in_registry(self):
        """Claugger appears in the content registry."""
        from atari_style.core.registry import ContentRegistry
        reg = ContentRegistry()
        # Simulate the registration that main.py does
        from atari_style.main import _build_registry
        reg = _build_registry()
        entry = reg.get("claugger")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.title, "Claugger")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m unittest tests.test_claugger.TestRegistration -v
```

Expected: `get("claugger")` returns None — not registered yet.

- [ ] **Step 3: Add Claugger to registry and menu**

In `atari_style/main.py`, add to `_build_registry()`:

```python
reg.register_metadata(ContentMetadata(
    id="claugger",
    title="Claugger",
    category=ContentCategory.GAME,
    description="Why did the chicken cross the road? A Frogger tribute.",
    run_module="atari_style.demos.games.claugger",
    run_function_name="run_claugger",
))
```

Add to the Games section of the menu items list.

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m unittest tests.test_claugger -v
```

Expected: All tests PASS.

- [ ] **Step 5: Smoke test — launch the game manually**

```bash
python -c "from atari_style.demos.games.claugger import run_claugger; run_claugger()"
```

Verify: title screen appears, chicken moves, vehicles scroll, collision works, HUD shows score/lives/timer. Press ESC to exit cleanly.

- [ ] **Step 6: Run full test suite and linter**

```bash
ruff check atari_style/ tests/
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: All checks pass, no regressions.

- [ ] **Step 7: Commit**

```bash
git add atari_style/main.py atari_style/demos/games/claugger.py tests/test_claugger.py
git commit -m "feat(claugger): Register in ContentRegistry and add to game menu"
```

---

## Task 9: Blog Article — Full Draft

Write the complete article with real code snippets from the now-built Claugger game.

**Files:**
- Modify: `docs/blog/2026-03-19-claugger-terminal-arcade.md`

- [ ] **Step 1: Read key code sections for article snippets**

Read these from the now-built `claugger.py` to extract real code for the article:
- Chicken sprite definitions
- Lane setup / `_build_lanes()`
- Collision detection logic
- Egg-laying mechanic
- HUD rendering
- Entry function and menu registration

Also read:
- `atari_style/core/renderer.py` — key method signatures for the Toolkit section
- `atari_style/core/input_handler.py` — InputHandler overview for the Toolkit section
- `PHILOSOPHY.md` — for the Thesis section

- [ ] **Step 2: Write the full article**

Replace the outline in `docs/blog/2026-03-19-claugger-terminal-arcade.md` with the complete ~2500-3500 word article.

Voice: Late-90s Linux Journal. Practical, irreverent, opinionated. Write like someone who's genuinely excited about terminals and slightly bemused that anyone would use Electron for anything.

Sections per spec:
1. **Cold Open** (~200 words) — Scene-setting, running the game, the delight
2. **The Thesis** (~400 words) — "The terminal is a canvas, not a cage." History, constraints breed creativity
3. **The Toolkit** (~500 words) — blessed, pygame, Renderer, InputHandler. Real code snippets from the codebase. Link to architecture docs.
4. **Building Claugger** (~1200 words) — Walk through the game in stages with real code snippets. The chicken, the lanes, collision, eggs, HUD. Link to full source.
5. **The Bigger Picture** (~400 words) — The full project, modular architecture, other games. Link to contributor guide.
6. **Closing** (~200 words) — Chickens, terminals, open source.

Include links to docs: `https://jcaldwell-labs.github.io/docs/atari-style/architecture/`, `/api-reference/`, `/tutorial/`, `/contributing/`

- [ ] **Step 3: Commit**

```bash
git add docs/blog/2026-03-19-claugger-terminal-arcade.md
git commit -m "docs: Write full Claugger terminal arcade blog article"
```

---

## Task 10: Project Documentation — 5 Pages

Write all 5 documentation pages for the docs site.

**Files:**
- Create: `docs/site/atari-style/getting-started.md`
- Create: `docs/site/atari-style/architecture.md`
- Create: `docs/site/atari-style/api-reference.md`
- Create: `docs/site/atari-style/tutorial.md`
- Create: `docs/site/atari-style/contributing.md`

- [ ] **Step 1: Create docs directory**

```bash
mkdir -p docs/site/atari-style
```

- [ ] **Step 2: Read source files for accurate documentation**

Read:
- `atari_style/core/renderer.py` — all public methods for API reference
- `atari_style/core/input_handler.py` — InputHandler and InputType for API reference
- `atari_style/core/registry.py` — ContentRegistry, ContentMetadata, ContentCategory for API reference
- `atari_style/core/config.py` — Config dataclass for API reference
- `atari_style/utils/fonts.py` — load_monospace_font for API reference
- `atari_style/main.py` — entry point and menu structure for architecture
- `CLAUDE.md` — code conventions for contributor guide
- `requirements.txt` — dependencies for getting started

- [ ] **Step 3: Write Getting Started page**

Create `docs/site/atari-style/getting-started.md` with Hugo front matter:
```yaml
---
title: "Getting Started"
weight: 1
---
```

Content per spec: prerequisites, installation, first launch, "try these first" recommendations, troubleshooting.

- [ ] **Step 4: Write Architecture Overview page**

Create `docs/site/atari-style/architecture.md`:
```yaml
---
title: "Architecture Overview"
weight: 2
---
```

Content: ASCII diagram of module relationships, Renderer explanation, InputHandler explanation, Menu + ContentRegistry, game loop pattern, module dependency map.

- [ ] **Step 5: Write API Reference page**

Create `docs/site/atari-style/api-reference.md`:
```yaml
---
title: "API Reference"
weight: 3
---
```

Content: Renderer class (all public methods with type signatures, params, return values, examples), InputHandler class, Color constants, Config dataclass, ContentRegistry, load_monospace_font(). All documented from actual source code.

- [ ] **Step 6: Write Building Your First Game tutorial**

Create `docs/site/atari-style/tutorial.md`:
```yaml
---
title: "Building Your First Game"
weight: 4
---
```

Content: Step-by-step bouncing ball demo. NOT Claugger — a simpler example. Covers: skeleton class, rendering, input, adding to menu. Points to Claugger source as "a more complete example."

- [ ] **Step 7: Write Contributor Guide**

Create `docs/site/atari-style/contributing.md`:
```yaml
---
title: "Contributing"
weight: 5
---
```

Content: Dev setup, running tests, linting, code conventions, adding a new demo, PR process. Adapted from CLAUDE.md for human readers.

- [ ] **Step 8: Commit**

```bash
git add docs/site/atari-style/
git commit -m "docs: Add 5-page project documentation for jcaldwell-labs.github.io"
```

---

## Task 11: Publishing Workflow

Create the GitHub Actions workflow that dispatches content to the Hugo site repo.

**Files:**
- Create: `.github/workflows/publish-docs.yml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/publish-docs.yml`:

```yaml
name: Publish Docs to Site

on:
  push:
    branches: [master]
    paths:
      - 'docs/blog/**'
      - 'docs/site/**'

jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Determine changed content
        id: changes
        run: |
          blog_changed=false
          docs_changed=false
          if git diff --name-only HEAD~1 HEAD | grep -q '^docs/blog/'; then
            blog_changed=true
          fi
          if git diff --name-only HEAD~1 HEAD | grep -q '^docs/site/'; then
            docs_changed=true
          fi
          echo "blog=$blog_changed" >> "$GITHUB_OUTPUT"
          echo "docs=$docs_changed" >> "$GITHUB_OUTPUT"

      - name: Dispatch to site repo
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.DOCS_PUBLISH_TOKEN }}
          repository: jcaldwell-labs/jcaldwell-labs.github.io
          event-type: publish-atari-style-docs
          client-payload: |
            {
              "source_repo": "${{ github.repository }}",
              "source_ref": "${{ github.sha }}",
              "blog_changed": "${{ steps.changes.outputs.blog }}",
              "docs_changed": "${{ steps.changes.outputs.docs }}"
            }
```

- [ ] **Step 2: Verify workflow YAML is valid**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/publish-docs.yml'))"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/publish-docs.yml
git commit -m "ci: Add cross-repo dispatch workflow for docs publishing"
```

---

## Task 12: Final Integration + Verification

Run full test suite, linter, and verify everything works together.

**Files:** None new — verification only.

- [ ] **Step 1: Run linter**

```bash
ruff check atari_style/ tests/
```

Expected: All checks passed.

- [ ] **Step 2: Run full test suite**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: All tests pass (existing + new claugger tests).

- [ ] **Step 3: Smoke test Claugger from menu**

```bash
python run.py
```

Navigate to Games → Claugger. Verify:
- Title screen renders with ASCII chicken
- Game starts on ENTER
- Chicken moves, vehicles scroll, river objects scroll
- Collision kills chicken with death animation and pun message
- River riding works (chicken moves with log)
- Eggs appear randomly, can be squashed
- HUD shows score, lives, timer
- Filling all 5 nests completes level
- Timer expiry kills chicken
- Game over screen shows stats
- ESC returns to menu cleanly

- [ ] **Step 4: Verify article has real code snippets**

Check that code blocks in `docs/blog/2026-03-19-claugger-terminal-arcade.md` match actual code in `atari_style/demos/games/claugger.py`. No placeholder or pseudo-code should remain.

- [ ] **Step 5: Verify docs reference correct APIs**

Check that method signatures in `docs/site/atari-style/api-reference.md` match the actual source files. Spot-check 3-4 methods.

- [ ] **Step 6: Final commit if any fixes were needed**

Review `git status` and stage only the specific files that were modified:

```bash
git status
# Stage only the specific files that needed fixes:
git add <specific-files-that-changed>
git commit -m "fix: Final integration fixes for Claugger + docs"
```

---

## Summary

| Task | Description | Depends On |
|------|-------------|------------|
| 1 | Article outline | — |
| 2 | Game skeleton + lanes | — |
| 3 | Chicken sprite + movement | 2 |
| 4 | Collision + death | 3 |
| 5 | Scoring, lives, timer, HUD | 4 |
| 6 | Egg-laying system | 5 |
| 7 | Easter eggs + title/game over | 6 |
| 8 | Menu registration + integration | 7 |
| 9 | Blog article full draft | 1, 8 |
| 10 | Project docs (5 pages) | 8 |
| 11 | Publishing workflow | — |
| 12 | Final verification | 9, 10, 11 |

**Parallelizable:** Tasks 1 and 2 can run in parallel. Tasks 9, 10, and 11 can run in parallel after Task 8 completes.
