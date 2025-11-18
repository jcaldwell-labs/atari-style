"""Terminal Arcade - A collection of terminal-based games and demos.

Terminal Arcade provides a rich collection of playable arcade games,
creative tools, and visual demonstrations, all running in your terminal
with full keyboard and joystick support.

GitHub: https://github.com/jcaldwell-labs/terminal-arcade
"""

__version__ = "2.0.0"
__author__ = "jcaldwell-labs"
__license__ = "MIT"

from .engine import Renderer, Color, InputHandler, InputType, Menu, MenuItem

__all__ = [
    'Renderer',
    'Color',
    'InputHandler',
    'InputType',
    'Menu',
    'MenuItem',
    '__version__',
]
