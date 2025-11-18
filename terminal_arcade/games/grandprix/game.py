"""Grand Prix first-person racing game with 3D road rendering."""

import time
import random
import math
from ...engine.renderer import Renderer, Color
from ...engine.input_handler import InputHandler, InputType


class RoadSegment:
    """Represents a segment of the track."""

    def __init__(self, index, curve=0, height=0):
        self.index = index
        self.curve = curve  # -1.0 to 1.0 (left to right)
        self.height = height  # Vertical offset
        self.world_x = 0  # Accumulated horizontal offset
        self.world_y = 0  # Accumulated vertical offset


class OpponentCar:
    """AI opponent car."""

    def __init__(self, position, speed_offset=0):
        self.position = position  # Position along track (segment index + fraction)
        self.lateral = random.uniform(-0.5, 0.5)  # -1 to 1, left to right
        self.speed = 100 + speed_offset  # Base speed variance
        self.color = random.choice([Color.RED, Color.BLUE, Color.YELLOW, Color.MAGENTA, Color.CYAN])

    def update(self, dt, track, player_speed):
        """Update opponent position."""
        # Move forward
        self.position += (self.speed / 100) * player_speed * dt

        # Wrap around track
        if self.position >= len(track.segments):
            self.position -= len(track.segments)

        # Follow racing line through curves
        segment_index = int(self.position) % len(track.segments)
        segment = track.segments[segment_index]

        # Adjust lateral position for curves (simple AI)
        target_lateral = -segment.curve * 0.3  # Slight inside line

        # Smoothly move toward target
        diff = target_lateral - self.lateral
        self.lateral += diff * dt * 2  # Adjust speed

        # Clamp to road bounds
        self.lateral = max(-0.8, min(0.8, self.lateral))


class Track:
    """Race track with segments."""

    def __init__(self, theme='desert'):
        self.theme = theme
        self.segments = []
        self.total_laps = 3
        self.segment_length = 200  # How much Z distance per segment
        self._generate_track()

    def _generate_track(self):
        """Generate track segments."""
        num_segments = 300

        for i in range(num_segments):
            # Create varied track with curves and hills
            # Use sine waves for smooth transitions

            # Curves
            curve = 0
            if 50 <= i < 70:
                curve = 0.8  # Right curve
            elif 100 <= i < 120:
                curve = -0.6  # Left curve
            elif 150 <= i < 170:
                curve = 0.5  # Right curve
            elif 220 <= i < 250:
                curve = -0.9  # Sharp left
            elif 270 <= i < 285:
                curve = 0.4  # Gentle right

            # Hills
            height = 0
            if 30 <= i < 60:
                height = math.sin((i - 30) / 30 * math.pi) * 300  # Hill
            elif 130 <= i < 160:
                height = -math.sin((i - 130) / 30 * math.pi) * 200  # Dip
            elif 200 <= i < 220:
                height = math.sin((i - 200) / 20 * math.pi) * 400  # Big hill

            segment = RoadSegment(i, curve, height)
            self.segments.append(segment)

        # Calculate world coordinates (cumulative offsets)
        world_x = 0
        world_y = 0

        for i, segment in enumerate(self.segments):
            segment.world_x = world_x
            segment.world_y = world_y

            # Update offsets for next segment
            world_x += segment.curve * 50
            # world_y updated by height automatically

    def get_segment(self, position):
        """Get segment at position."""
        index = int(position) % len(self.segments)
        return self.segments[index]


class GrandPrix:
    """Main Grand Prix game class."""

    # Game states
    STATE_COUNTDOWN = 0
    STATE_RACING = 1
    STATE_FINISHED = 2

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.width = self.renderer.width
        self.height = self.renderer.height

        # Game state
        self.state = self.STATE_COUNTDOWN
        self.countdown_timer = 3.0

        # Track
        self.track = Track('desert')

        # Player state
        self.position = 0  # Position on track (segment index + fraction)
        self.speed = 0  # Current speed (0-200 km/h)
        self.lateral = 0  # Lateral position (-1 = left, 1 = right)
        self.max_speed = 200
        self.acceleration = 60  # km/h per second
        self.deceleration = 80
        self.off_road_penalty = 120

        # Lap tracking
        self.current_lap = 1
        self.lap_times = []
        self.current_lap_time = 0
        self.total_time = 0
        self.best_lap_time = float('inf')

        # Checkpoint tracking
        self.last_checkpoint = 0

        # Opponent cars
        self.opponents = []
        for i in range(8):
            pos = (i + 1) * 30  # Spread out opponents
            speed_offset = random.uniform(-20, 20)
            self.opponents.append(OpponentCar(pos, speed_offset))

        # Camera
        self.camera_height = 1000
        self.draw_distance = 300  # How many segments to draw

        # Frame timing
        self.last_time = time.time()

    def update(self, dt):
        """Update game state."""
        if self.state == self.STATE_COUNTDOWN:
            self.countdown_timer -= dt
            if self.countdown_timer <= 0:
                self.state = self.STATE_RACING

        elif self.state == self.STATE_RACING:
            self._update_racing(dt)

    def _update_racing(self, dt):
        """Update during racing."""
        # Update lap time
        self.current_lap_time += dt
        self.total_time += dt

        # Get current segment
        current_segment = self.track.get_segment(self.position)

        # Check lap completion
        checkpoint = int(self.position / len(self.track.segments))
        if checkpoint > self.last_checkpoint:
            self.last_checkpoint = checkpoint
            self.current_lap += 1

            # Record lap time
            if len(self.lap_times) < self.current_lap - 1:
                self.lap_times.append(self.current_lap_time)
                if self.current_lap_time < self.best_lap_time:
                    self.best_lap_time = self.current_lap_time
                self.current_lap_time = 0

            # Check race finish
            if self.current_lap > self.track.total_laps:
                self.state = self.STATE_FINISHED
                return

        # Update speed based on input
        # (Input handled separately, this is just physics)

        # Move forward
        self.position += (self.speed / 100) * dt * 2  # Scale factor for game feel

        # Wrap position
        if self.position >= len(self.track.segments):
            self.position -= len(self.track.segments)

        # Check if off-road
        if abs(self.lateral) > 1.0:
            # Off-road, slow down
            self.speed = max(0, self.speed - self.off_road_penalty * dt)

        # Update opponents
        for opponent in self.opponents:
            opponent.update(dt, self.track, self.speed)

        # Check collisions with opponents
        for opponent in self.opponents:
            # Check if opponent is close to player
            pos_diff = abs(opponent.position - self.position)

            # Consider wrap-around
            if pos_diff > len(self.track.segments) / 2:
                pos_diff = len(self.track.segments) - pos_diff

            if pos_diff < 0.5 and abs(opponent.lateral - self.lateral) < 0.3:
                # Collision! Slow down
                self.speed = max(0, self.speed - 50)
                # Push laterally
                if self.lateral < opponent.lateral:
                    self.lateral -= 0.3
                else:
                    self.lateral += 0.3

    def handle_input(self, dt):
        """Handle player input."""
        # Get joystick state
        jx, jy = self.input_handler.get_joystick_state()

        # Keyboard input (read once for better responsiveness)
        accelerating = False
        braking = False
        turning_left = False
        turning_right = False

        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)

            if key:
                # Check all keys in one pass
                if key.name == 'KEY_LEFT' or key.lower() == 'a':
                    turning_left = True
                elif key.name == 'KEY_RIGHT' or key.lower() == 'd':
                    turning_right = True

                if key.name == 'KEY_UP' or key.lower() == 'w':
                    accelerating = True
                elif key.name == 'KEY_DOWN' or key.lower() == 's':
                    braking = True

        # Steering (joystick overrides keyboard)
        if abs(jx) > 0:
            self.lateral += jx * dt * 2  # Steering speed
        elif turning_left:
            self.lateral -= dt * 2
        elif turning_right:
            self.lateral += dt * 2

        # Clamp lateral position
        self.lateral = max(-1.5, min(1.5, self.lateral))

        # Acceleration/Braking (joystick overrides keyboard)
        if abs(jy) > 0:
            if jy < 0:  # Up
                accelerating = True
            elif jy > 0:  # Down
                braking = True

        # Update speed
        if accelerating:
            self.speed = min(self.max_speed, self.speed + self.acceleration * dt)
        elif braking:
            self.speed = max(0, self.speed - self.deceleration * dt)
        else:
            # Natural deceleration
            self.speed = max(0, self.speed - 20 * dt)

    def draw(self):
        """Draw the game."""
        self.renderer.clear_buffer()

        if self.state == self.STATE_COUNTDOWN:
            self._draw_countdown()
        else:
            self._draw_racing()

        self.renderer.render()

    def _draw_countdown(self):
        """Draw countdown."""
        count = int(self.countdown_timer) + 1
        if count <= 3:
            msg = str(count) if count > 0 else "GO!"
            color = Color.BRIGHT_RED if count > 0 else Color.BRIGHT_GREEN
            self.renderer.draw_text(self.width // 2 - len(msg) // 2,
                                    self.height // 2, msg, color)

    def _draw_racing(self):
        """Draw racing view."""
        # Draw sky
        sky_height = self.height // 3
        for y in range(sky_height):
            for x in range(self.width):
                self.renderer.set_pixel(x, y, ' ', Color.CYAN)

        # Draw horizon
        horizon_y = sky_height

        # Draw road (3D perspective)
        base_segment = int(self.position)

        for n in range(self.draw_distance):
            segment_index = (base_segment + n) % len(self.track.segments)
            segment = self.track.segments[segment_index]

            # 3D projection
            z = n * self.track.segment_length
            if z == 0:
                z = 1  # Avoid division by zero

            # Perspective projection
            scale = self.camera_height / z

            # Road width in screen coordinates
            road_width = scale * 2000

            # Calculate screen position
            screen_y = horizon_y + int(scale * segment.height * 0.1)
            screen_y = max(0, min(screen_y, self.height - 1))

            # Calculate horizontal offset from curves
            curve_offset = segment.world_x - self.track.get_segment(self.position).world_x
            screen_x_offset = int(scale * curve_offset * 0.5)

            # Road center
            road_center_x = self.width // 2 + screen_x_offset

            # Draw road segment
            road_half_width = int(road_width / 2)

            # Grass (sides)
            grass_color = Color.GREEN if n % 10 < 5 else Color.BRIGHT_GREEN

            # Road surface
            road_color = Color.WHITE if n % 20 < 10 else Color.BRIGHT_WHITE

            # Draw grass left
            for x in range(max(0, road_center_x - road_half_width * 2),
                           max(0, road_center_x - road_half_width)):
                if 0 <= x < self.width:
                    self.renderer.set_pixel(x, screen_y, '░', grass_color)

            # Draw road
            for x in range(max(0, road_center_x - road_half_width),
                           min(self.width, road_center_x + road_half_width)):
                if 0 <= x < self.width:
                    self.renderer.set_pixel(x, screen_y, '▓', road_color)

            # Draw grass right
            for x in range(min(self.width, road_center_x + road_half_width),
                           min(self.width, road_center_x + road_half_width * 2)):
                if 0 <= x < self.width:
                    self.renderer.set_pixel(x, screen_y, '░', grass_color)

            # Draw lane markers
            if n % 15 < 8:
                marker_x = road_center_x
                if 0 <= marker_x < self.width:
                    self.renderer.set_pixel(marker_x, screen_y, '│', Color.YELLOW)

            # Draw opponent cars on this segment
            for opponent in self.opponents:
                opp_segment_index = int(opponent.position) % len(self.track.segments)
                if opp_segment_index == segment_index:
                    # Draw opponent
                    opp_x = road_center_x + int(opponent.lateral * road_half_width)
                    if 0 <= opp_x < self.width and 0 <= screen_y < self.height:
                        # Scale car size by distance
                        car_char = '█' if scale > 0.05 else '▓' if scale > 0.02 else '▪'
                        self.renderer.set_pixel(opp_x, screen_y, car_char, opponent.color)

        # Draw player car (at bottom center)
        player_y = self.height - 5
        player_x = self.width // 2 + int(self.lateral * 10)

        # Player car (simple ASCII representation)
        self.renderer.set_pixel(player_x, player_y, '▲', Color.BRIGHT_RED)
        self.renderer.set_pixel(player_x - 1, player_y + 1, '█', Color.RED)
        self.renderer.set_pixel(player_x, player_y + 1, '█', Color.RED)
        self.renderer.set_pixel(player_x + 1, player_y + 1, '█', Color.RED)

        # Draw HUD
        self._draw_hud()

        # Draw finish message
        if self.state == self.STATE_FINISHED:
            msg = "RACE COMPLETE!"
            self.renderer.draw_text(self.width // 2 - len(msg) // 2,
                                    self.height // 2, msg, Color.BRIGHT_GREEN)
            time_msg = f"Total Time: {self._format_time(self.total_time)}"
            self.renderer.draw_text(self.width // 2 - len(time_msg) // 2,
                                    self.height // 2 + 2, time_msg, Color.BRIGHT_WHITE)
            if self.best_lap_time != float('inf'):
                best_msg = f"Best Lap: {self._format_time(self.best_lap_time)}"
                self.renderer.draw_text(self.width // 2 - len(best_msg) // 2,
                                        self.height // 2 + 4, best_msg, Color.BRIGHT_YELLOW)

    def _draw_hud(self):
        """Draw heads-up display."""
        # Speed
        speed_text = f"SPEED: {int(self.speed)} km/h"
        self.renderer.draw_text(2, self.height - 2, speed_text, Color.BRIGHT_WHITE)

        # Speedometer bar
        bar_width = 20
        filled = int((self.speed / self.max_speed) * bar_width)
        bar = '[' + '█' * filled + '░' * (bar_width - filled) + ']'
        self.renderer.draw_text(2, self.height - 1, bar, Color.BRIGHT_GREEN)

        # Lap info
        lap_text = f"LAP: {min(self.current_lap, self.track.total_laps)}/{self.track.total_laps}"
        self.renderer.draw_text(self.width - len(lap_text) - 2, self.height - 2,
                                lap_text, Color.BRIGHT_CYAN)

        # Current lap time
        time_text = f"TIME: {self._format_time(self.current_lap_time)}"
        self.renderer.draw_text(self.width - len(time_text) - 2, self.height - 1,
                                time_text, Color.BRIGHT_YELLOW)

        # Best lap
        if self.best_lap_time != float('inf'):
            best_text = f"BEST: {self._format_time(self.best_lap_time)}"
            self.renderer.draw_text(self.width // 2 - len(best_text) // 2, self.height - 1,
                                    best_text, Color.BRIGHT_MAGENTA)

        # Position indicator (where on track)
        progress = (self.position % len(self.track.segments)) / len(self.track.segments)
        progress_text = f"TRACK: {int(progress * 100)}%"
        self.renderer.draw_text(self.width // 2 - len(progress_text) // 2, self.height - 2,
                                progress_text, Color.WHITE)

    def _format_time(self, seconds):
        """Format time as MM:SS.MS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{mins:02d}:{secs:02d}.{ms:02d}"

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
                    if self.state == self.STATE_FINISHED:
                        self.__init__()  # Restart

                # Continuous input for driving
                if self.state == self.STATE_RACING:
                    self.handle_input(dt)

                # Update
                self.update(dt)

                # Draw
                self.draw()

                # Frame rate (30 FPS for 3D rendering)
                time.sleep(0.033)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_grandprix():
    """Entry point for Grand Prix game."""
    game = GrandPrix()
    game.run()


if __name__ == "__main__":
    run_grandprix()
