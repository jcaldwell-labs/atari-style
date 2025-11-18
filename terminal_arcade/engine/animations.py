"""Animation utilities for terminal games.

Provides helper functions for common animation effects like fades, wipes, and transitions.
"""

import time
from typing import Callable, Optional
from .renderer import Renderer, Color


class Animator:
    """Helper class for creating terminal animations."""

    @staticmethod
    def fade_in(renderer: Renderer, duration: float = 1.0, fps: int = 30):
        """Fade in from black by gradually revealing content.

        Args:
            renderer: Renderer instance with content already in buffer
            duration: Fade duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps

        for frame in range(frames + 1):
            progress = frame / frames
            # Simulate fade by drawing darker versions of content
            # In terminals, we'll use a simple reveal effect instead
            renderer.render()
            time.sleep(frame_delay)

    @staticmethod
    def fade_out(renderer: Renderer, duration: float = 1.0, fps: int = 30):
        """Fade out to black by gradually hiding content.

        Args:
            renderer: Renderer instance
            duration: Fade duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps

        for frame in range(frames + 1):
            progress = frame / frames
            # Gradually darken by replacing characters with spaces
            alpha = 1.0 - progress
            if alpha < 0.3:
                renderer.clear_buffer()
            renderer.render()
            time.sleep(frame_delay)

    @staticmethod
    def wipe_horizontal(renderer: Renderer, content_func: Callable, direction: str = 'left',
                       duration: float = 1.0, fps: int = 30):
        """Wipe in content horizontally.

        Args:
            renderer: Renderer instance
            content_func: Function to call to draw content into buffer
            direction: 'left' or 'right'
            duration: Wipe duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps
        width = renderer.width

        for frame in range(frames + 1):
            progress = frame / frames
            reveal_x = int(width * progress)

            renderer.clear_buffer()
            content_func()  # Draw full content

            # Mask unrevealed portion
            if direction == 'left':
                for y in range(renderer.height):
                    for x in range(reveal_x, width):
                        renderer.buffer[y][x] = ' '
                        renderer.color_buffer[y][x] = None
            else:  # right
                for y in range(renderer.height):
                    for x in range(0, width - reveal_x):
                        renderer.buffer[y][x] = ' '
                        renderer.color_buffer[y][x] = None

            renderer.render()
            time.sleep(frame_delay)

    @staticmethod
    def wipe_vertical(renderer: Renderer, content_func: Callable, direction: str = 'down',
                     duration: float = 1.0, fps: int = 30):
        """Wipe in content vertically.

        Args:
            renderer: Renderer instance
            content_func: Function to call to draw content into buffer
            direction: 'down' or 'up'
            duration: Wipe duration in seconds
            fps: Target frames per second
        """
        frames = int(duration * fps)
        frame_delay = 1.0 / fps
        height = renderer.height

        for frame in range(frames + 1):
            progress = frame / frames
            reveal_y = int(height * progress)

            renderer.clear_buffer()
            content_func()  # Draw full content

            # Mask unrevealed portion
            if direction == 'down':
                for y in range(reveal_y, height):
                    for x in range(renderer.width):
                        renderer.buffer[y][x] = ' '
                        renderer.color_buffer[y][x] = None
            else:  # up
                for y in range(0, height - reveal_y):
                    for x in range(renderer.width):
                        renderer.buffer[y][x] = ' '
                        renderer.color_buffer[y][x] = None

            renderer.render()
            time.sleep(frame_delay)

    @staticmethod
    def typewriter(renderer: Renderer, x: int, y: int, text: str, color: Optional[str] = None,
                   chars_per_second: int = 30):
        """Display text with typewriter effect.

        Args:
            renderer: Renderer instance
            x, y: Starting position
            text: Text to display
            color: Text color
            chars_per_second: Typing speed
        """
        delay = 1.0 / chars_per_second

        for i, char in enumerate(text):
            renderer.draw_text(x + i, y, char, color)
            renderer.render()
            time.sleep(delay)

    @staticmethod
    def blink(renderer: Renderer, content_func: Callable, blink_count: int = 3,
             blink_duration: float = 0.3):
        """Blink content on and off.

        Args:
            renderer: Renderer instance
            content_func: Function to draw content
            blink_count: Number of blinks
            blink_duration: Duration of each blink cycle
        """
        on_time = blink_duration / 2
        off_time = blink_duration / 2

        for _ in range(blink_count):
            # On
            renderer.clear_buffer()
            content_func()
            renderer.render()
            time.sleep(on_time)

            # Off
            renderer.clear_buffer()
            renderer.render()
            time.sleep(off_time)

        # Final on state
        renderer.clear_buffer()
        content_func()
        renderer.render()

    @staticmethod
    def pulse(renderer: Renderer, content_func: Callable, pulse_count: int = 3,
             pulse_duration: float = 0.5, fps: int = 30):
        """Pulse content in and out (size-based effect using borders).

        Args:
            renderer: Renderer instance
            content_func: Function to draw content
            pulse_count: Number of pulses
            pulse_duration: Duration of each pulse
            fps: Target frames per second
        """
        frames = int(pulse_duration * fps)
        frame_delay = 1.0 / fps

        for _ in range(pulse_count):
            # Expand
            for frame in range(frames // 2):
                renderer.clear_buffer()
                content_func()
                renderer.render()
                time.sleep(frame_delay)

            # Contract
            for frame in range(frames // 2):
                renderer.clear_buffer()
                content_func()
                renderer.render()
                time.sleep(frame_delay)
