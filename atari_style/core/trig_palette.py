"""
Trigonometric Color Palette System

Based on Inigo Quilez's cosine palette technique, this module provides
smooth, cyclic color gradients using just 4 vector parameters.

The palette function:
    color = a + b * cos(2π * (c * t + d))

Where:
    t = input value (0.0 to 1.0, or beyond for cycling)
    a = DC offset (base color)
    b = amplitude (color range)
    c = frequency (how fast colors cycle)
    d = phase (color offset)

Reference: https://iquilezles.org/articles/palettes/

Usage:
    from atari_style.core.trig_palette import palette, PRESETS

    # Use a preset
    color = palette(0.5, **PRESETS['rainbow'])

    # Custom parameters
    color = palette(t, a=[0.5]*3, b=[0.5]*3, c=[1.0]*3, d=[0.0, 0.33, 0.67])

    # Get palette as list of colors
    colors = palette_to_list(32, **PRESETS['sunset'])
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Tuple, List, Dict, Union

# Type aliases
Vec3 = Tuple[float, float, float]
Color = Tuple[int, int, int]  # RGB 0-255


@dataclass
class PaletteParams:
    """Parameters for a trigonometric color palette."""
    a: Vec3  # DC offset (base color)
    b: Vec3  # Amplitude (color range)
    c: Vec3  # Frequency (cycle speed)
    d: Vec3  # Phase offset

    def to_dict(self) -> Dict[str, Vec3]:
        """Convert to dictionary for unpacking."""
        return {'a': self.a, 'b': self.b, 'c': self.c, 'd': self.d}


def palette(
    t: float,
    a: Vec3 = (0.5, 0.5, 0.5),
    b: Vec3 = (0.5, 0.5, 0.5),
    c: Vec3 = (1.0, 1.0, 1.0),
    d: Vec3 = (0.0, 0.33, 0.67)
) -> Vec3:
    """
    Generate a color from the trigonometric palette function.

    Args:
        t: Input value (0.0-1.0 for single cycle, can exceed for repetition)
        a: DC offset - determines the base/average color
        b: Amplitude - determines the color range/contrast
        c: Frequency - how many color cycles per unit t
        d: Phase - shifts the color cycle (offsets R, G, B independently)

    Returns:
        RGB color as tuple of floats (0.0-1.0)
    """
    TWO_PI = 2.0 * math.pi

    r = a[0] + b[0] * math.cos(TWO_PI * (c[0] * t + d[0]))
    g = a[1] + b[1] * math.cos(TWO_PI * (c[1] * t + d[1]))
    b_val = a[2] + b[2] * math.cos(TWO_PI * (c[2] * t + d[2]))

    # Clamp to valid range
    return (
        max(0.0, min(1.0, r)),
        max(0.0, min(1.0, g)),
        max(0.0, min(1.0, b_val))
    )


def palette_rgb(
    t: float,
    a: Vec3 = (0.5, 0.5, 0.5),
    b: Vec3 = (0.5, 0.5, 0.5),
    c: Vec3 = (1.0, 1.0, 1.0),
    d: Vec3 = (0.0, 0.33, 0.67)
) -> Color:
    """
    Generate a color as RGB integers (0-255).

    Args:
        t: Input value (0.0-1.0 for single cycle)
        a, b, c, d: Palette parameters (see palette())

    Returns:
        RGB color as tuple of integers (0-255)
    """
    col = palette(t, a, b, c, d)
    return (
        int(col[0] * 255),
        int(col[1] * 255),
        int(col[2] * 255)
    )


def palette_to_list(
    n: int,
    a: Vec3 = (0.5, 0.5, 0.5),
    b: Vec3 = (0.5, 0.5, 0.5),
    c: Vec3 = (1.0, 1.0, 1.0),
    d: Vec3 = (0.0, 0.33, 0.67),
    as_int: bool = True
) -> List[Union[Vec3, Color]]:
    """
    Generate a list of n colors from the palette.

    Args:
        n: Number of colors to generate
        a, b, c, d: Palette parameters
        as_int: If True, return RGB integers (0-255), else floats (0.0-1.0)

    Returns:
        List of RGB colors
    """
    if as_int:
        return [palette_rgb(i / n, a, b, c, d) for i in range(n)]
    else:
        return [palette(i / n, a, b, c, d) for i in range(n)]


def interpolate_palettes(
    t: float,
    params1: PaletteParams,
    params2: PaletteParams,
    mix: float
) -> Vec3:
    """
    Interpolate between two palettes.

    Args:
        t: Palette input value
        params1: First palette parameters
        params2: Second palette parameters
        mix: Blend factor (0.0 = params1, 1.0 = params2)

    Returns:
        Blended color
    """
    # Interpolate parameters
    def lerp_vec3(v1: Vec3, v2: Vec3, m: float) -> Vec3:
        return (
            v1[0] + (v2[0] - v1[0]) * m,
            v1[1] + (v2[1] - v1[1]) * m,
            v1[2] + (v2[2] - v1[2]) * m
        )

    a = lerp_vec3(params1.a, params2.a, mix)
    b = lerp_vec3(params1.b, params2.b, mix)
    c = lerp_vec3(params1.c, params2.c, mix)
    d = lerp_vec3(params1.d, params2.d, mix)

    return palette(t, a, b, c, d)


# ============================================================================
# Preset Palettes
# ============================================================================

PRESETS: Dict[str, Dict[str, Vec3]] = {
    # Classic rainbow - smooth cycling through all hues
    'rainbow': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 1.0, 1.0),
        'd': (0.0, 0.33, 0.67)
    },

    # Sunset - warm oranges to cool purples
    'sunset': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 1.0, 0.5),
        'd': (0.8, 0.9, 0.3)
    },

    # Ocean - deep blues to cyan to foam white
    'ocean': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 0.7, 0.4),
        'd': (0.0, 0.15, 0.2)
    },

    # Fire - black to red to orange to yellow
    'fire': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 1.0, 1.0),
        'd': (0.0, 0.1, 0.2)
    },

    # Neon - vibrant 80s aesthetic
    'neon': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 1.0, 1.0),
        'd': (0.3, 0.2, 0.2)
    },

    # Pastel - soft, muted colors
    'pastel': {
        'a': (0.8, 0.8, 0.8),
        'b': (0.2, 0.2, 0.2),
        'c': (1.0, 1.0, 1.0),
        'd': (0.0, 0.33, 0.67)
    },

    # Forest - greens and earth tones
    'forest': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 1.0, 1.0),
        'd': (0.3, 0.1, 0.4)
    },

    # Cyberpunk - pink, cyan, purple
    'cyberpunk': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 1.0, 1.0),
        'd': (0.5, 0.8, 0.9)
    },

    # Grayscale - black to white
    'grayscale': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (0.0, 0.0, 0.0),
        'd': (0.0, 0.0, 0.0)
    },

    # Heat - thermal imaging style
    'heat': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 1.0, 1.0),
        'd': (0.0, 0.05, 0.1)
    },

    # Ice - cold blues and whites
    'ice': {
        'a': (0.6, 0.7, 0.8),
        'b': (0.4, 0.3, 0.2),
        'c': (1.0, 1.0, 1.0),
        'd': (0.5, 0.6, 0.7)
    },

    # Lava - molten rock colors
    'lava': {
        'a': (0.5, 0.5, 0.5),
        'b': (0.5, 0.5, 0.5),
        'c': (1.0, 0.7, 0.4),
        'd': (0.0, 0.05, 0.1)
    },
}


def get_preset(name: str) -> PaletteParams:
    """
    Get a preset palette by name.

    Args:
        name: Preset name (see list_presets())

    Returns:
        PaletteParams for the preset

    Raises:
        KeyError: If preset name not found
    """
    if name not in PRESETS:
        raise KeyError(f"Unknown preset: {name}. Available: {list_presets()}")
    p = PRESETS[name]
    return PaletteParams(a=p['a'], b=p['b'], c=p['c'], d=p['d'])


def list_presets() -> List[str]:
    """Return list of available preset names."""
    return list(PRESETS.keys())


# ============================================================================
# GLSL Code Generation
# ============================================================================

def generate_glsl_function() -> str:
    """
    Generate GLSL code for the palette function.

    Returns:
        GLSL function code that can be included in shaders
    """
    return '''
// Trigonometric color palette function (Inigo Quilez)
// Usage: vec3 color = trig_palette(t, a, b, c, d);
vec3 trig_palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}
'''


def generate_glsl_preset(name: str) -> str:
    """
    Generate GLSL code for a specific preset.

    Args:
        name: Preset name

    Returns:
        GLSL constant definitions for the preset
    """
    if name not in PRESETS:
        raise KeyError(f"Unknown preset: {name}")

    p = PRESETS[name]
    return f'''
// {name.title()} palette preset
const vec3 {name.upper()}_A = vec3({p['a'][0]:.3f}, {p['a'][1]:.3f}, {p['a'][2]:.3f});
const vec3 {name.upper()}_B = vec3({p['b'][0]:.3f}, {p['b'][1]:.3f}, {p['b'][2]:.3f});
const vec3 {name.upper()}_C = vec3({p['c'][0]:.3f}, {p['c'][1]:.3f}, {p['c'][2]:.3f});
const vec3 {name.upper()}_D = vec3({p['d'][0]:.3f}, {p['d'][1]:.3f}, {p['d'][2]:.3f});
'''


# ============================================================================
# Terminal Color Mapping (for Phase 2)
# ============================================================================

def to_terminal_256(color: Vec3) -> int:
    """
    Map an RGB color to the closest terminal 256-color palette index.

    Args:
        color: RGB color as floats (0.0-1.0)

    Returns:
        Terminal color index (0-255)
    """
    r, g, b = color

    # Convert to 0-255
    r_int = int(r * 255)
    g_int = int(g * 255)
    b_int = int(b * 255)

    # Check grayscale ramp first (232-255)
    if r_int == g_int == b_int:
        if r_int < 8:
            return 16  # Black
        if r_int > 248:
            return 231  # White
        return round((r_int - 8) / 247 * 23) + 232

    # Map to 6x6x6 color cube (16-231)
    r_idx = round(r * 5)
    g_idx = round(g * 5)
    b_idx = round(b * 5)

    return 16 + (36 * r_idx) + (6 * g_idx) + b_idx


def palette_to_terminal_256(
    n: int,
    a: Vec3 = (0.5, 0.5, 0.5),
    b: Vec3 = (0.5, 0.5, 0.5),
    c: Vec3 = (1.0, 1.0, 1.0),
    d: Vec3 = (0.0, 0.33, 0.67)
) -> List[int]:
    """
    Generate a list of terminal 256-color indices from the palette.

    Args:
        n: Number of colors
        a, b, c, d: Palette parameters

    Returns:
        List of terminal color indices (0-255)
    """
    return [to_terminal_256(palette(i / n, a, b, c, d)) for i in range(n)]


# ============================================================================
# CLI/Demo Functions
# ============================================================================

def demo_palette(name: str = 'rainbow', width: int = 64) -> None:
    """
    Print a demo of a palette to the terminal.

    Args:
        name: Preset name
        width: Width in characters
    """
    params = PRESETS.get(name, PRESETS['rainbow'])
    colors = palette_to_list(width, **params)

    print(f"\n{name.title()} Palette:")
    print("─" * width)

    # Print colored blocks
    for r, g, b in colors:
        print(f"\033[48;2;{r};{g};{b}m \033[0m", end="")
    print()
    print("─" * width)


def demo_all_presets(width: int = 48) -> None:
    """Print demos of all preset palettes."""
    for name in PRESETS:
        demo_palette(name, width)


if __name__ == "__main__":
    # Demo all presets when run directly
    demo_all_presets()
