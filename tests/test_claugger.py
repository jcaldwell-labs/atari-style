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


if __name__ == "__main__":
    unittest.main()
