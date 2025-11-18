"""Terminal Arcade Launcher System.

Provides menu system, game registry, and startup experience.
"""

from .game_registry import GameRegistry, GameMetadata
from .splash_screen import SplashScreen

__all__ = [
    'GameRegistry',
    'GameMetadata',
    'SplashScreen',
]
