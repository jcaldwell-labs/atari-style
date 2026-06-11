"""Screen transition effects for switching between games and menus.

Provides cinematic transitions to enhance the user experience when moving
between different screens or launching games.
"""

import time
import random
from .renderer import Renderer, Color


class Transition:
    """Screen transition effects."""

    @staticmethod
    def curtain_close(renderer: Renderer, duration: float = 0.8, fps: int = 30):
        """Close curtain effect (horizontal bars moving to center).

        Args:
            renderer: Renderer instance
            duration: Transition duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps
        height = renderer.height
        half_height = height // 2

        for frame in range(frames + 1):
            progress = frame / frames
            bars_closed = int(half_height * progress)

            # Draw bars from top and bottom
            for i in range(bars_closed):
                for x in range(renderer.width):
                    # Top curtain
                    renderer.set_pixel(x, i, '█', Color.DARK_GRAY)
                    # Bottom curtain
                    renderer.set_pixel(x, height - 1 - i, '█', Color.DARK_GRAY)

            renderer.render()
            time.sleep(frame_delay)

    @staticmethod
    def curtain_open(renderer: Renderer, duration: float = 0.8, fps: int = 30):
        """Open curtain effect (horizontal bars moving from center).

        Args:
            renderer: Renderer instance
            duration: Transition duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps
        height = renderer.height
        half_height = height // 2

        # Start fully closed
        for y in range(height):
            for x in range(renderer.width):
                renderer.set_pixel(x, y, '█', Color.DARK_GRAY)

        for frame in range(frames + 1):
            progress = frame / frames
            bars_open = int(half_height * progress)

            # Clear revealed area
            for i in range(bars_open):
                for x in range(renderer.width):
                    # Top curtain opening
                    renderer.set_pixel(x, half_height - i - 1, ' ', None)
                    # Bottom curtain opening
                    renderer.set_pixel(x, half_height + i, ' ', None)

            renderer.render()
            time.sleep(frame_delay)

    @staticmethod
    def star_field_zoom(renderer: Renderer, duration: float = 1.0, fps: int = 30):
        """Zoom through star field effect (classic space jump).

        Args:
            renderer: Renderer instance
            duration: Transition duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps
        width = renderer.width
        height = renderer.height
        center_x = width // 2
        center_y = height // 2

        # Generate random stars
        stars = []
        for _ in range(50):
            angle = random.uniform(0, 6.28)  # 2*pi radians
            distance = random.uniform(0, 1)
            stars.append((angle, distance))

        for frame in range(frames + 1):
            renderer.clear_buffer()
            progress = frame / frames
            speed = 1 + progress * 20  # Accelerate over time

            for angle, initial_dist in stars:
                # Calculate star position based on angle and expanding distance
                dist = initial_dist + progress * speed * 2
                if dist > 2:  # Star passed the screen
                    continue

                # Convert polar to cartesian
                x = center_x + int(dist * width * 0.5 * (1.0 if angle < 3.14 else -1.0) * abs(angle % 3.14 - 1.57) / 1.57)
                y = center_y + int(dist * height * 0.3 * (1.0 if angle < 1.57 or angle > 4.71 else -1.0) *
                                  abs((angle + 1.57) % 3.14 - 1.57) / 1.57)

                if 0 <= x < width and 0 <= y < height:
                    # Stars get brighter/bigger as they approach
                    char = '·' if dist < 0.5 else ('*' if dist < 1.0 else '✦')
                    color = Color.WHITE if dist > 0.8 else Color.CYAN
                    renderer.set_pixel(x, y, char, color)

            renderer.render()
            time.sleep(frame_delay)

    @staticmethod
    def matrix_rain(renderer: Renderer, duration: float = 1.5, fps: int = 30):
        """Matrix-style falling characters effect.

        Args:
            renderer: Renderer instance
            duration: Transition duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps
        width = renderer.width
        height = renderer.height

        # Initialize columns with random positions
        columns = []
        for x in range(0, width, 2):
            columns.append({
                'x': x,
                'y': random.randint(-height, 0),
                'speed': random.randint(1, 3),
                'chars': [chr(random.randint(33, 126)) for _ in range(height)]
            })

        for frame in range(frames):
            renderer.clear_buffer()

            for col in columns:
                col['y'] += col['speed']

                # Draw column trail
                for i in range(min(col['y'], height)):
                    y = col['y'] - i
                    if 0 <= y < height:
                        char = col['chars'][i % len(col['chars'])]
                        # Brightest at head, fading down
                        if i == 0:
                            color = Color.BRIGHT_GREEN
                        elif i < 5:
                            color = Color.GREEN
                        else:
                            color = Color.DARK_GRAY
                        renderer.set_pixel(col['x'], y, char, color)

                # Reset column when off screen
                if col['y'] > height + 10:
                    col['y'] = random.randint(-height // 2, 0)
                    col['chars'] = [chr(random.randint(33, 126)) for _ in range(height)]

            renderer.render()
            time.sleep(frame_delay)

        # Clear at end
        renderer.clear_buffer()
        renderer.render()

    @staticmethod
    def diagonal_wipe(renderer: Renderer, duration: float = 0.6, fps: int = 30):
        """Diagonal wipe from top-left to bottom-right.

        Args:
            renderer: Renderer instance
            duration: Transition duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps
        width = renderer.width
        height = renderer.height
        max_distance = width + height

        for frame in range(frames + 1):
            progress = frame / frames
            wipe_distance = int(max_distance * progress)

            renderer.clear_buffer()

            # Fill wiped area with pattern
            for y in range(height):
                for x in range(width):
                    if x + y < wipe_distance:
                        # Use gradient character
                        char = '░' if (x + y) % 3 == 0 else '▒' if (x + y) % 3 == 1 else '▓'
                        renderer.set_pixel(x, y, char, Color.BRIGHT_BLUE)

            renderer.render()
            time.sleep(frame_delay)

    @staticmethod
    def circle_expand(renderer: Renderer, duration: float = 0.8, fps: int = 30):
        """Expanding circle from center.

        Args:
            renderer: Renderer instance
            duration: Transition duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps
        width = renderer.width
        height = renderer.height
        center_x = width // 2
        center_y = height // 2
        max_radius = max(width, height)

        for frame in range(frames + 1):
            renderer.clear_buffer()
            progress = frame / frames
            radius = int(max_radius * progress)

            for y in range(height):
                for x in range(width):
                    # Calculate distance from center (with aspect ratio correction)
                    dx = (x - center_x)
                    dy = (y - center_y) * 2  # Terminal chars are ~2x taller than wide
                    dist = (dx * dx + dy * dy) ** 0.5

                    if dist < radius:
                        # Filled circle with gradient
                        if dist > radius - 3:
                            char = '░'
                            color = Color.BRIGHT_CYAN
                        elif dist > radius - 6:
                            char = '▒'
                            color = Color.CYAN
                        else:
                            char = '▓'
                            color = Color.BLUE
                        renderer.set_pixel(x, y, char, color)

            renderer.render()
            time.sleep(frame_delay)
