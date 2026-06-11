"""Splash screen for Terminal Arcade startup.

Displays animated logo and initialization messages.
"""

import time
from pathlib import Path
from ..engine.renderer import Renderer, Color
from ..engine.branding import Brand
from ..engine.animations import Animator
from ..engine.transitions import Transition


class SplashScreen:
    """Terminal Arcade splash screen with logo animation."""

    def __init__(self, renderer: Renderer):
        """Initialize splash screen.

        Args:
            renderer: Renderer instance
        """
        self.renderer = renderer

    def show(self, duration: float = 3.0, joystick_detected: bool = False):
        """Display splash screen with logo and initialization info.

        Args:
            duration: How long to display the splash (seconds)
            joystick_detected: Whether joystick was detected
        """
        try:
            self.renderer.enter_fullscreen()

            # Phase 1: Star field transition (0.8s)
            Transition.star_field_zoom(self.renderer, duration=0.8)

            # Phase 2: Display logo with fade-in effect (1.0s)
            self.renderer.clear_buffer()
            Brand.draw_logo_cabinet(self.renderer)
            Brand.draw_github_link(self.renderer)

            # Add joystick status
            status_y = self.renderer.height // 2 + 7
            if joystick_detected:
                status_text = "✓ Joystick Connected"
                status_color = Color.BRIGHT_GREEN
            else:
                status_text = "○ Keyboard Mode"
                status_color = Color.YELLOW

            status_x = (self.renderer.width - len(status_text)) // 2
            self.renderer.draw_text(status_x, status_y, status_text, status_color)

            # Loading message
            loading_text = "Loading Terminal Arcade..."
            loading_x = (self.renderer.width - len(loading_text)) // 2
            self.renderer.draw_text(loading_x, status_y + 2, loading_text, Color.DARK_GRAY)

            self.renderer.render()
            time.sleep(duration)

            # Phase 3: Transition out with curtain close (0.4s)
            Transition.curtain_close(self.renderer, duration=0.4)

        finally:
            self.renderer.exit_fullscreen()

    def show_compact(self, duration: float = 2.0, joystick_detected: bool = False):
        """Display compact splash screen (faster version).

        Args:
            duration: How long to display the splash (seconds)
            joystick_detected: Whether joystick was detected
        """
        try:
            self.renderer.enter_fullscreen()

            # Simple display with compact logo
            self.renderer.clear_buffer()
            Brand.draw_logo_compact(self.renderer)

            # Joystick status
            status_y = self.renderer.height // 2 + 4
            if joystick_detected:
                status_text = "🎮 Joystick Ready"
                status_color = Color.BRIGHT_GREEN
            else:
                status_text = "⌨️  Keyboard Mode"
                status_color = Color.YELLOW

            status_x = (self.renderer.width - len(status_text)) // 2
            self.renderer.draw_text(status_x, status_y, status_text, status_color)

            # GitHub link
            Brand.draw_github_link(self.renderer)

            self.renderer.render()
            time.sleep(duration)

        finally:
            self.renderer.exit_fullscreen()

    def show_animated(self, joystick_detected: bool = False):
        """Display fully animated splash screen with multiple effects.

        Args:
            joystick_detected: Whether joystick was detected
        """
        try:
            self.renderer.enter_fullscreen()

            # Animation sequence
            # 1. Star field zoom (1.0s)
            Transition.star_field_zoom(self.renderer, duration=1.0)

            # 2. Large logo with pulse effect (1.5s)
            self.renderer.clear_buffer()

            def draw_logo_content():
                Brand.draw_logo_large(self.renderer, color=Color.BRIGHT_CYAN)

            # Pulse the logo
            for _ in range(2):
                self.renderer.clear_buffer()
                draw_logo_content()
                self.renderer.render()
                time.sleep(0.25)

                self.renderer.clear_buffer()
                Brand.draw_logo_large(self.renderer, color=Color.CYAN)
                self.renderer.render()
                time.sleep(0.25)

            # 3. Add text with typewriter effect (1.0s)
            tagline = "Retro Gaming in Your Terminal"
            tagline_x = (self.renderer.width - len(tagline)) // 2
            tagline_y = self.renderer.height // 2 + 8

            for i, char in enumerate(tagline):
                self.renderer.clear_buffer()
                draw_logo_content()
                self.renderer.draw_text(tagline_x, tagline_y, tagline[:i+1], Color.BRIGHT_YELLOW)
                self.renderer.render()
                time.sleep(0.04)

            # 4. Add status info (0.5s)
            time.sleep(0.3)

            status_y = tagline_y + 2
            if joystick_detected:
                status_text = "✓ JOYSTICK DETECTED"
                status_color = Color.BRIGHT_GREEN
            else:
                status_text = "○ KEYBOARD MODE"
                status_color = Color.YELLOW

            status_x = (self.renderer.width - len(status_text)) // 2
            self.renderer.draw_text(status_x, status_y, status_text, status_color)

            # GitHub link
            Brand.draw_github_link(self.renderer)

            self.renderer.render()
            time.sleep(1.0)

            # 5. Circle expand transition out (0.6s)
            Transition.circle_expand(self.renderer, duration=0.6)

        finally:
            self.renderer.exit_fullscreen()

    def show_quick(self, joystick_detected: bool = False):
        """Show minimal splash screen for fast startup.

        Args:
            joystick_detected: Whether joystick was detected
        """
        try:
            self.renderer.enter_fullscreen()

            self.renderer.clear_buffer()

            # Simple title
            title = "TERMINAL ARCADE"
            title_x = (self.renderer.width - len(title)) // 2
            title_y = self.renderer.height // 2 - 1

            self.renderer.draw_text(title_x, title_y, title, Color.BRIGHT_CYAN)

            # Status
            if joystick_detected:
                status = "🎮 Ready"
                color = Color.BRIGHT_GREEN
            else:
                status = "⌨️  Ready"
                color = Color.YELLOW

            status_x = (self.renderer.width - len(status)) // 2
            self.renderer.draw_text(status_x, title_y + 2, status, color)

            self.renderer.render()
            time.sleep(0.8)

        finally:
            self.renderer.exit_fullscreen()
