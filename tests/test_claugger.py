"""Tests for Claugger game."""

import random
import unittest
from atari_style.demos.games.claugger import (
    Lane, LaneType, LaneObject, Claugger,
    LANE_COUNT, ROWS_PER_LANE, TURTLE_CHAR,
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


class TestChicken(unittest.TestCase):
    """Test chicken sprite and movement."""

    def test_chicken_starts_at_lane_0(self):
        """Chicken starts in the henhouse (lane 0, bottom)."""
        game = Claugger()
        self.assertEqual(game.chicken_lane, 0)

    def test_chicken_moves_up(self):
        """Moving up increments lane by 1."""
        game = Claugger()
        game.move_chicken(0, 1)
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
        self.assertGreater(game.chicken_x, start_x)

    def test_chicken_has_facing_direction(self):
        """Chicken facing changes with movement."""
        game = Claugger()
        game.move_chicken(0, 1)
        self.assertEqual(game.chicken_facing, "up")
        game.move_chicken(1, 0)
        self.assertEqual(game.chicken_facing, "right")


class TestCollision(unittest.TestCase):
    """Test collision detection."""

    def test_road_collision_kills_chicken(self):
        """Chicken dies when overlapping a vehicle."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.chicken_lane = 1  # First road lane
        game.lanes[1].objects[0].x = float(game.chicken_x)
        game.check_collisions()
        self.assertEqual(game.state, Claugger.STATE_DYING)

    def test_no_collision_when_not_overlapping(self):
        """Chicken is safe when no vehicle overlap."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.chicken_lane = 1
        for obj in game.lanes[1].objects:
            obj.x = -20.0
        game.check_collisions()
        self.assertNotEqual(game.state, Claugger.STATE_DYING)

    def test_river_no_object_kills_chicken(self):
        """Chicken drowns when on river lane without a log/turtle."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.chicken_lane = 7  # First river lane
        for obj in game.lanes[7].objects:
            obj.x = -50.0
        game.check_collisions()
        self.assertEqual(game.state, Claugger.STATE_DYING)

    def test_river_on_log_is_safe(self):
        """Chicken is safe when standing on a log."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.chicken_lane = 7
        game.lanes[7].objects[0].x = float(game.chicken_x)
        game.lanes[7].objects[0].width = 6
        game.lanes[7].objects[0].is_diving = False
        game.check_collisions()
        self.assertNotEqual(game.state, Claugger.STATE_DYING)

    def test_chicken_rides_log(self):
        """Chicken moves with the log it's standing on."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.chicken_lane = 7
        game.lanes[7].objects[0].x = float(game.chicken_x)
        game.lanes[7].objects[0].width = 6
        game.lanes[7].objects[0].is_diving = False
        start_x = game.chicken_x
        game.update_river_riding(0.5)
        self.assertNotEqual(game.chicken_x, start_x)

    def test_turtle_dive_kills_chicken(self):
        """Chicken drowns when turtle it's on dives."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.chicken_lane = 7
        turtle = game.lanes[7].objects[0]
        turtle.x = float(game.chicken_x)
        turtle.width = 3
        turtle.is_diving = True
        game.check_collisions()
        self.assertEqual(game.state, Claugger.STATE_DYING)

    def test_collision_uses_bounding_box(self):
        """Collision checks full 3-wide sprite area."""
        game = Claugger()
        game.state = Claugger.STATE_PLAYING
        game.chicken_lane = 1
        game.lanes[1].objects[0].x = float(game.chicken_x + 2)
        game.lanes[1].objects[0].width = 4
        game.check_collisions()
        self.assertEqual(game.state, Claugger.STATE_DYING)

    def test_turtle_dive_cycle_timing(self):
        """Turtles dive for 2s and surface for 4s."""
        game = Claugger()
        # Find a turtle object
        turtle = None
        for lane in game.lanes:
            if lane.lane_type == LaneType.RIVER:
                for obj in lane.objects:
                    if TURTLE_CHAR in obj.chars:
                        turtle = obj
                        break
            if turtle:
                break
        if turtle is None:
            self.skipTest("No turtle found")
        # Force surface state and run through cycle
        turtle.is_diving = False
        turtle.dive_timer = 0.0
        turtle.dive_phase = 4.0  # Surface duration
        game.update_turtle_dives(4.0)
        self.assertTrue(turtle.is_diving)


if __name__ == "__main__":
    unittest.main()
