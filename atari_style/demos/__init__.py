"""Demo modules for atari-style terminal games and visualizers."""

from .games import run_pacman, run_galaga, run_grandprix, run_breakout
from .visualizers import run_screensaver, run_starfield, run_platonic_solids
from .tools import run_ascii_painter, run_joystick_test

__all__ = [
    # Games
    'run_pacman',
    'run_galaga',
    'run_grandprix',
    'run_breakout',
    # Visualizers
    'run_screensaver',
    'run_starfield',
    'run_platonic_solids',
    # Tools
    'run_ascii_painter',
    'run_joystick_test',
]
