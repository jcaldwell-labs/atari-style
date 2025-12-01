"""Visual demo modules for atari-style terminal demos."""

from .screensaver import run_screensaver
from .starfield import run_starfield
from .platonic_solids import run_platonic_solids
from .flux_control import run_flux_control
from .flux_control_patterns import run_pattern_flux
from .flux_control_rhythm import run_rhythm_flux
from .flux_control_zen import run_flux_zen
from .flux_control_explorer import run_flux_explorer
from .gl_mandelbrot import run_gl_mandelbrot

__all__ = [
    'run_screensaver',
    'run_starfield',
    'run_platonic_solids',
    'run_flux_control',
    'run_pattern_flux',
    'run_rhythm_flux',
    'run_flux_zen',
    'run_flux_explorer',
    'run_gl_mandelbrot',
]
