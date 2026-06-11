"""Pac-Man intro cutscene.

Animated intro showing the maze drawing in and characters appearing.
"""

import time
from ...engine.renderer import Renderer, Color
from ...engine.animations import Animator


def show_intro(renderer: Renderer, duration: float = 5.0):
    """Display Pac-Man intro cutscene.

    Args:
        renderer: Renderer instance
        duration: Total intro duration in seconds
    """
    try:
        renderer.enter_fullscreen()

        # Phase 1: Draw title with better ASCII art (2.0s)
        renderer.clear_buffer()

        # Larger, clearer ASCII art logo
        title_lines = [
            "  ████████                      ███╗   ███╗ █████╗ ███╗   ██╗  ",
            "  ██╔════██   █████╗   ██████╗ ████╗ ████║██╔══██╗████╗  ██║  ",
            "  ██║   ██║  ██╔══██╗ ██╔════╝ ██╔████╔██║███████║██╔██╗ ██║  ",
            "  ████████╔╝ ███████║ ██║      ██║╚██╔╝██║██╔══██║██║╚██╗██║  ",
            "  ██╔═══╝    ██╔══██║ ██║      ██║ ╚═╝ ██║██║  ██║██║ ╚████║  ",
            "  ██║        ██║  ██║ ╚██████╗ ██║     ██║██║  ██║██║  ╚═══╝  ",
            "  ╚═╝        ╚═╝  ╚═╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝        ",
        ]

        title_y = renderer.height // 2 - 10

        # Draw title line by line with animation
        for i, line in enumerate(title_lines):
            title_x = (renderer.width - len(line)) // 2
            renderer.draw_text(title_x, title_y + i, line, Color.BRIGHT_YELLOW)
            renderer.render()
            time.sleep(0.15)  # Slower reveal

        time.sleep(0.5)  # Pause to appreciate the logo

        # Phase 2: Draw mini maze (1.5s)
        maze_art = [
            "    ╔════════════════════╗",
            "    ║ ••••••  •••••••• ║",
            "    ║ █▀▀█  ████  █▀█ ║",
            "    ║ •••• Ο    Ο •••• ║",
            "    ║ ████  ████  ████ ║",
            "    ║ •••••••••••••••• ║",
            "    ╚════════════════════╝",
        ]

        maze_y = title_y + len(title_lines) + 2
        for i, line in enumerate(maze_art):
            maze_x = (renderer.width - len(line)) // 2
            # Draw line character by character for animation
            for j, char in enumerate(line):
                if char == '•':
                    color = Color.YELLOW
                elif char == 'Ο':
                    color = Color.BRIGHT_WHITE
                elif char in '█▀':
                    color = Color.BLUE
                else:
                    color = Color.CYAN

                renderer.draw_text(maze_x + j, maze_y + i, char, color)

            renderer.render()
            time.sleep(0.2)  # Slower line drawing

        # Phase 3: Show characters (1.5s)
        time.sleep(0.5)

        # Pac-Man - larger and centered
        pacman_text = "◐◐ PAC-MAN ◐◐"
        pacman_x = (renderer.width - len(pacman_text)) // 2
        pacman_y = maze_y + len(maze_art) + 2
        renderer.draw_text(pacman_x, pacman_y, pacman_text, Color.BRIGHT_YELLOW)
        renderer.render()
        time.sleep(0.4)

        # Ghosts - with labels
        ghost_title = "THE GHOSTS:"
        ghost_title_x = (renderer.width - len(ghost_title)) // 2
        renderer.draw_text(ghost_title_x, pacman_y + 2, ghost_title, Color.WHITE)
        renderer.render()
        time.sleep(0.3)

        ghosts = [
            ("◆ Blinky", Color.BRIGHT_RED, 0),
            ("◆ Pinky", Color.BRIGHT_MAGENTA, 1),
            ("◆ Inky", Color.BRIGHT_CYAN, 2),
            ("◆ Clyde", Color.YELLOW, 3),
        ]

        ghost_start_x = (renderer.width - 44) // 2
        for name, color, offset in ghosts:
            x = ghost_start_x + (offset * 11)
            renderer.draw_text(x, pacman_y + 4, name, color)
            renderer.render()
            time.sleep(0.25)  # Slower ghost reveal

        # Phase 4: Ready message (0.5s)
        time.sleep(0.5)
        ready_text = ">>> READY! <<<"
        ready_x = (renderer.width - len(ready_text)) // 2
        ready_y = pacman_y + 6

        # Blink effect
        for _ in range(3):
            renderer.draw_text(ready_x, ready_y, ready_text, Color.BRIGHT_WHITE)
            renderer.render()
            time.sleep(0.2)

            # Clear ready text
            renderer.draw_text(ready_x, ready_y, " " * len(ready_text), None)
            renderer.render()
            time.sleep(0.15)

        # Final ready
        renderer.draw_text(ready_x, ready_y, ready_text, Color.BRIGHT_WHITE)
        renderer.render()
        time.sleep(0.5)

    finally:
        renderer.exit_fullscreen()


def show_intro_quick(renderer: Renderer):
    """Display quick Pac-Man intro (< 1 second).

    Args:
        renderer: Renderer instance
    """
    try:
        renderer.enter_fullscreen()
        renderer.clear_buffer()

        # Simple title
        title = "PAC-MAN"
        title_x = (renderer.width - len(title)) // 2
        title_y = renderer.height // 2 - 2

        renderer.draw_text(title_x, title_y, title, Color.BRIGHT_YELLOW)

        # Characters
        chars = "◐ ◆ ◆ ◆ ◆"
        chars_x = (renderer.width - len(chars)) // 2
        renderer.draw_text(chars_x, title_y + 2, chars, Color.YELLOW)

        # Ready
        ready = "READY!"
        ready_x = (renderer.width - len(ready)) // 2
        renderer.draw_text(ready_x, title_y + 4, ready, Color.BRIGHT_WHITE)

        renderer.render()
        time.sleep(0.6)

    finally:
        renderer.exit_fullscreen()
