"""Terminal Arcade - A collection of terminal-based games and demos.

.. deprecated::
    The ``terminal_arcade`` package is deprecated. Use ``atari_style`` instead.
    Game metadata in ``terminal_arcade/games/*/metadata.json`` is consumed by
    ``atari_style.core.registry.ContentRegistry.scan_directory()``. All new
    development should target ``atari_style/``.

GitHub: https://github.com/jcaldwell-labs/terminal-arcade
"""

import warnings

__version__ = "2.0.0"
__author__ = "jcaldwell-labs"
__license__ = "MIT"

warnings.warn(
    "terminal_arcade is deprecated. Use atari_style instead. "
    "See issue #155 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

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
