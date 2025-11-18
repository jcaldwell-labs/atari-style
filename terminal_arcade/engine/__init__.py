"""Terminal Arcade Game Engine.

Core infrastructure for terminal-based games and demos.
"""

from .renderer import Renderer, Color
from .input_handler import InputHandler, InputType
from .menu import Menu, MenuItem

__all__ = [
    'Renderer',
    'Color',
    'InputHandler',
    'InputType',
    'Menu',
    'MenuItem',
]
