"""Game modules for atari-style terminal games."""

from .pacman import run_pacman
from .galaga import run_galaga
from .grandprix import run_grandprix
from .breakout import run_breakout

__all__ = ['run_pacman', 'run_galaga', 'run_grandprix', 'run_breakout']
