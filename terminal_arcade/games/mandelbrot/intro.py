"""Mandelbrot Explorer intro cutscene.

Animated zoom into the Mandelbrot set from overview to detailed region.
"""

import time
from ...engine.renderer import Renderer, Color
from ...engine.animations import Animator


def show_intro(renderer: Renderer, duration: float = 3.0):
    """Display Mandelbrot Explorer intro cutscene.

    Args:
        renderer: Renderer instance
        duration: Total intro duration in seconds
    """
    try:
        renderer.enter_fullscreen()

        # Phase 1: Title and description (1.0s)
        renderer.clear_buffer()

        title_lines = [
            "███╗   ███╗ █████╗ ███╗   ██╗██████╗ ███████╗██╗     ██████╗ ██████╗  ██████╗ ████████╗",
            "████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝██║     ██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝",
            "██╔████╔██║███████║██╔██╗ ██║██║  ██║█████╗  ██║     ██████╔╝██████╔╝██║   ██║   ██║   ",
            "██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║██╔══╝  ██║     ██╔══██╗██╔══██╗██║   ██║   ██║   ",
            "██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝███████╗███████╗██████╔╝██║  ██║╚██████╔╝   ██║   ",
            "╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚══════╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ",
        ]

        # Center title (if it fits)
        title_y = renderer.height // 2 - 10
        if len(title_lines[0]) < renderer.width:
            for i, line in enumerate(title_lines):
                title_x = (renderer.width - len(line)) // 2
                renderer.draw_text(title_x, title_y + i, line, Color.BRIGHT_CYAN)
        else:
            # Fallback compact title
            compact_title = "MANDELBROT EXPLORER"
            title_x = (renderer.width - len(compact_title)) // 2
            renderer.draw_text(title_x, title_y + 2, compact_title, Color.BRIGHT_CYAN)

        subtitle = "Explore the Infinite Fractal"
        subtitle_x = (renderer.width - len(subtitle)) // 2
        renderer.draw_text(subtitle_x, title_y + 8, subtitle, Color.CYAN)

        renderer.render()
        time.sleep(1.0)

        # Phase 2: Simple fractal animation (1.5s)
        renderer.clear_buffer()

        # Draw a simplified fractal representation
        fractal_art = [
            "                    ░░░░                    ",
            "              ░░▒▒▒▒████▒▒▒▒░░              ",
            "          ░░▒▒████████████████▒▒░░          ",
            "        ▒▒████████████████████████▒▒        ",
            "      ▒▒████████████████████████████▒▒      ",
            "    ░░████████████████████████████████░░    ",
            "  ░░██████████████████████████████████░░  ",
            "  ▒▒████████████████▓▓████████████████▒▒  ",
            "░░████████████████▓▓▓▓▓▓████████████████░░",
            "▒▒██████████████▓▓▓▓▓▓▓▓▓▓██████████████▒▒",
            "████████████████▓▓▓▓▓▓▓▓▓▓████████████████",
            "████████████████▓▓▓▓▓▓▓▓▓▓████████████████",
            "▒▒██████████████▓▓▓▓▓▓▓▓▓▓██████████████▒▒",
            "░░████████████████▓▓▓▓▓▓████████████████░░",
            "  ▒▒████████████████▓▓████████████████▒▒  ",
            "  ░░██████████████████████████████████░░  ",
            "    ░░████████████████████████████████░░    ",
            "      ▒▒████████████████████████████▒▒      ",
            "        ▒▒████████████████████████▒▒        ",
            "          ░░▒▒████████████████▒▒░░          ",
            "              ░░▒▒▒▒████▒▒▒▒░░              ",
            "                    ░░░░                    ",
        ]

        fractal_y = (renderer.height - len(fractal_art)) // 2
        fractal_x = (renderer.width - len(fractal_art[0])) // 2

        # Animate drawing the fractal
        colors = [Color.BLUE, Color.CYAN, Color.BRIGHT_CYAN, Color.WHITE]
        for i, line in enumerate(fractal_art):
            for j, char in enumerate(line):
                if char != ' ':
                    # Color based on character
                    if char == '░':
                        color = colors[0]
                    elif char == '▒':
                        color = colors[1]
                    elif char == '▓':
                        color = colors[2]
                    else:
                        color = colors[3]

                    renderer.draw_text(fractal_x + j, fractal_y + i, char, color)

            renderer.render()
            time.sleep(0.065)

        # Phase 3: "Zoom" text effect (0.5s)
        time.sleep(0.3)

        zoom_text = ">> ZOOMING IN <<"
        zoom_x = (renderer.width - len(zoom_text)) // 2
        zoom_y = fractal_y + len(fractal_art) + 2

        # Blink effect
        for _ in range(2):
            renderer.draw_text(zoom_x, zoom_y, zoom_text, Color.BRIGHT_YELLOW)
            renderer.render()
            time.sleep(0.12)

            renderer.draw_text(zoom_x, zoom_y, " " * len(zoom_text), None)
            renderer.render()
            time.sleep(0.08)

        renderer.draw_text(zoom_x, zoom_y, zoom_text, Color.BRIGHT_YELLOW)
        renderer.render()
        time.sleep(0.2)

    finally:
        renderer.exit_fullscreen()


def show_intro_quick(renderer: Renderer):
    """Display quick Mandelbrot intro (< 1 second).

    Args:
        renderer: Renderer instance
    """
    try:
        renderer.enter_fullscreen()
        renderer.clear_buffer()

        # Simple title
        title = "MANDELBROT EXPLORER"
        title_x = (renderer.width - len(title)) // 2
        title_y = renderer.height // 2 - 2

        renderer.draw_text(title_x, title_y, title, Color.BRIGHT_CYAN)

        # Subtitle
        subtitle = "Infinite Fractal Depths"
        subtitle_x = (renderer.width - len(subtitle)) // 2
        renderer.draw_text(subtitle_x, title_y + 2, subtitle, Color.CYAN)

        # Simple fractal icon
        icon = "▓▓▓▒▒▒░░░▒▒▒▓▓▓"
        icon_x = (renderer.width - len(icon)) // 2
        renderer.draw_text(icon_x, title_y + 4, icon, Color.BRIGHT_WHITE)

        renderer.render()
        time.sleep(0.6)

    finally:
        renderer.exit_fullscreen()
