"""GLSL-inspired utility functions for Python.

This module provides Python implementations of common GLSL functions used in
shader programming. These functions are useful for procedural graphics,
terminal visualizers, and prototyping shader algorithms.

All functions support both scalar values and numpy arrays for vectorized
operations when performance is needed.

Usage:
    from atari_style.core.glsl_utils import fract, smoothstep, mix, palette

    # Create repeating pattern
    pattern = fract(x * 5.0)

    # Smooth transition
    alpha = smoothstep(0.3, 0.7, distance)

    # Blend colors
    color = mix(color_a, color_b, t)

    # Inigo Quilez color palette
    rgb = palette(t, offset, amplitude, frequency, phase)
"""

from __future__ import annotations

import math
from typing import Union, Tuple

# Type alias for numeric values (scalar or array)
# Using Union for compatibility - numpy arrays handled at runtime
Numeric = Union[float, int]

# Constants matching GLSL
PI = 3.14159265358979323846
TAU = 6.28318530717958647692
E = 2.71828182845904523536


# =============================================================================
# Core GLSL Functions
# =============================================================================

def fract(x: Numeric) -> Numeric:
    """Return the fractional part of x.

    GLSL equivalent: fract(x)

    Creates repeating/tiling patterns. The result is always in [0, 1).

    Args:
        x: Input value (scalar or array)

    Returns:
        Fractional part: x - floor(x)

    Examples:
        >>> fract(1.7)
        0.7
        >>> fract(-0.3)  # Note: always positive
        0.7
    """
    return x - math.floor(x) if isinstance(x, (int, float)) else x - _np_floor(x)


def step(edge: float, x: Numeric) -> Numeric:
    """Hard threshold function.

    GLSL equivalent: step(edge, x)

    Returns 0.0 if x < edge, else 1.0.

    Args:
        edge: Threshold value
        x: Input value (scalar or array)

    Returns:
        0.0 or 1.0 based on threshold

    Examples:
        >>> step(0.5, 0.3)
        0.0
        >>> step(0.5, 0.7)
        1.0
    """
    if isinstance(x, (int, float)):
        return 0.0 if x < edge else 1.0
    # Numpy array
    import numpy as np
    return np.where(x < edge, 0.0, 1.0)


def smoothstep(edge0: float, edge1: float, x: Numeric) -> Numeric:
    """Hermite interpolation between 0 and 1.

    GLSL equivalent: smoothstep(edge0, edge1, x)

    Returns 0.0 if x <= edge0, 1.0 if x >= edge1, otherwise performs smooth
    Hermite interpolation. The derivative is zero at both edges.

    Args:
        edge0: Lower edge of transition
        edge1: Upper edge of transition
        x: Input value (scalar or array)

    Returns:
        Smoothly interpolated value in [0, 1]

    Examples:
        >>> smoothstep(0.0, 1.0, 0.5)
        0.5
        >>> smoothstep(0.0, 1.0, 0.25)
        0.15625
    """
    # Clamp x to [0, 1]
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    # Hermite interpolation: 3t^2 - 2t^3
    return t * t * (3.0 - 2.0 * t)


def mix(a: Numeric, b: Numeric, t: Numeric) -> Numeric:
    """Linear interpolation between a and b.

    GLSL equivalent: mix(a, b, t)

    Also known as lerp. Returns a + t * (b - a).

    Args:
        a: Start value
        b: End value
        t: Interpolation factor (0 = a, 1 = b)

    Returns:
        Interpolated value

    Examples:
        >>> mix(0.0, 10.0, 0.5)
        5.0
        >>> mix(100.0, 200.0, 0.25)
        125.0
    """
    return a + t * (b - a)


# Alias for compatibility
lerp = mix


def clamp(x: Numeric, min_val: float, max_val: float) -> Numeric:
    """Constrain value to a range.

    GLSL equivalent: clamp(x, min, max)

    Args:
        x: Input value (scalar or array)
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Value clamped to [min_val, max_val]

    Examples:
        >>> clamp(1.5, 0.0, 1.0)
        1.0
        >>> clamp(-0.5, 0.0, 1.0)
        0.0
    """
    if isinstance(x, (int, float)):
        return max(min_val, min(max_val, x))
    # Numpy array
    import numpy as np
    return np.clip(x, min_val, max_val)


def mod(x: Numeric, y: float) -> Numeric:
    """GLSL-style modulo (always positive).

    GLSL equivalent: mod(x, y)

    Unlike Python's %, this always returns a positive value.

    Args:
        x: Dividend (scalar or array)
        y: Divisor

    Returns:
        x mod y (always positive)

    Examples:
        >>> mod(5.5, 2.0)
        1.5
        >>> mod(-0.5, 1.0)  # Returns 0.5, not -0.5
        0.5
    """
    if isinstance(x, (int, float)):
        return x - y * math.floor(x / y)
    # Numpy array
    import numpy as np
    return x - y * np.floor(x / y)


def sign(x: Numeric) -> Numeric:
    """Extract the sign of x.

    GLSL equivalent: sign(x)

    Args:
        x: Input value (scalar or array)

    Returns:
        -1.0, 0.0, or 1.0

    Examples:
        >>> sign(-5.0)
        -1.0
        >>> sign(3.0)
        1.0
        >>> sign(0.0)
        0.0
    """
    if isinstance(x, (int, float)):
        if x > 0:
            return 1.0
        elif x < 0:
            return -1.0
        else:
            return 0.0
    # Numpy array
    import numpy as np
    return np.sign(x).astype(float)


def abs_(x: Numeric) -> Numeric:
    """Absolute value.

    GLSL equivalent: abs(x)

    Args:
        x: Input value (scalar or array)

    Returns:
        Absolute value of x
    """
    if isinstance(x, (int, float)):
        return abs(x)
    import numpy as np
    return np.abs(x)


# =============================================================================
# Vector/Coordinate Functions
# =============================================================================

def length(x: float, y: float, z: float = 0.0) -> float:
    """Calculate vector length.

    GLSL equivalent: length(vec2/vec3)

    Args:
        x: X component
        y: Y component
        z: Z component (default 0 for 2D)

    Returns:
        Euclidean length of vector

    Examples:
        >>> length(3.0, 4.0)
        5.0
    """
    return math.sqrt(x * x + y * y + z * z)


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate distance between two 2D points.

    GLSL equivalent: distance(vec2, vec2)

    Args:
        x1, y1: First point
        x2, y2: Second point

    Returns:
        Euclidean distance

    Examples:
        >>> distance(0.0, 0.0, 3.0, 4.0)
        5.0
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def normalize_2d(x: float, y: float) -> Tuple[float, float]:
    """Normalize a 2D vector to unit length.

    GLSL equivalent: normalize(vec2)

    Args:
        x: X component
        y: Y component

    Returns:
        Tuple of (normalized_x, normalized_y)

    Examples:
        >>> normalize_2d(3.0, 4.0)
        (0.6, 0.8)
    """
    len_ = length(x, y)
    if len_ == 0:
        return (0.0, 0.0)
    return (x / len_, y / len_)


def dot_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """2D dot product.

    GLSL equivalent: dot(vec2, vec2)

    Args:
        x1, y1: First vector
        x2, y2: Second vector

    Returns:
        Dot product

    Examples:
        >>> dot_2d(1.0, 0.0, 0.0, 1.0)
        0.0
    """
    return x1 * x2 + y1 * y2


# =============================================================================
# Color & Palette Functions
# =============================================================================

def palette(
    t: Numeric,
    a: Tuple[float, float, float] = (0.5, 0.5, 0.5),
    b: Tuple[float, float, float] = (0.5, 0.5, 0.5),
    c: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    d: Tuple[float, float, float] = (0.0, 0.33, 0.67)
) -> Tuple[float, float, float]:
    """Inigo Quilez's cosine color palette.

    Creates smooth, cyclic color gradients using the formula:
    color = a + b * cos(2*pi * (c*t + d))

    See: https://iquilezles.org/articles/palettes/

    Args:
        t: Parameter value (0-1 cycles through palette, but can exceed)
        a: Offset (brightness baseline)
        b: Amplitude (color range)
        c: Frequency (how many times colors cycle)
        d: Phase (color offset)

    Returns:
        Tuple of (r, g, b) values in [0, 1]

    Common Presets:
        Rainbow: a=(0.5,0.5,0.5), b=(0.5,0.5,0.5), c=(1,1,1), d=(0,0.33,0.67)
        Fire:    a=(0.5,0.2,0.0), b=(0.5,0.3,0.1), c=(1,0.8,0.4), d=(0,0.15,0.3)
        Ocean:   a=(0.0,0.3,0.5), b=(0.2,0.4,0.4), c=(1,1,0.5), d=(0,0.1,0.2)

    Examples:
        >>> r, g, b = palette(0.5)
    """
    if isinstance(t, (int, float)):
        r = a[0] + b[0] * math.cos(TAU * (c[0] * t + d[0]))
        g = a[1] + b[1] * math.cos(TAU * (c[1] * t + d[1]))
        b_val = a[2] + b[2] * math.cos(TAU * (c[2] * t + d[2]))
        # Clamp to valid color range
        return (
            max(0.0, min(1.0, r)),
            max(0.0, min(1.0, g)),
            max(0.0, min(1.0, b_val))
        )
    # Numpy array
    import numpy as np
    r = a[0] + b[0] * np.cos(TAU * (c[0] * t + d[0]))
    g = a[1] + b[1] * np.cos(TAU * (c[1] * t + d[1]))
    b_val = a[2] + b[2] * np.cos(TAU * (c[2] * t + d[2]))
    return (
        np.clip(r, 0.0, 1.0),
        np.clip(g, 0.0, 1.0),
        np.clip(b_val, 0.0, 1.0)
    )


# Predefined color palette presets
PALETTE_RAINBOW = (
    (0.5, 0.5, 0.5),  # a
    (0.5, 0.5, 0.5),  # b
    (1.0, 1.0, 1.0),  # c
    (0.0, 0.33, 0.67)  # d
)

PALETTE_FIRE = (
    (0.5, 0.2, 0.0),
    (0.5, 0.3, 0.1),
    (1.0, 0.8, 0.4),
    (0.0, 0.15, 0.3)
)

PALETTE_OCEAN = (
    (0.0, 0.3, 0.5),
    (0.2, 0.4, 0.4),
    (1.0, 1.0, 0.5),
    (0.0, 0.1, 0.2)
)

PALETTE_PLASMA = (
    (0.5, 0.5, 0.5),
    (0.5, 0.5, 0.5),
    (1.0, 1.0, 1.0),
    (0.0, 0.33, 0.67)
)


# =============================================================================
# Pattern/Domain Functions
# =============================================================================

def tile_uv(x: float, y: float, scale: float) -> Tuple[float, float]:
    """Create tiling UV coordinates.

    Useful for creating repeating patterns.

    Args:
        x: X coordinate
        y: Y coordinate
        scale: Number of tiles

    Returns:
        Tuple of (tiled_x, tiled_y) in [0, 1)

    Examples:
        >>> tile_uv(2.5, 3.7, 2.0)
        (0.0, 0.4)
    """
    return (fract(x * scale), fract(y * scale))


def repeat_polar(angle: float, count: int) -> float:
    """Repeat pattern around center in polar coordinates.

    Useful for creating radial symmetry.

    Args:
        angle: Input angle in radians
        count: Number of repetitions around circle

    Returns:
        Angle folded into one segment

    Examples:
        >>> repeat_polar(math.pi, 4)  # 4-fold symmetry
    """
    segment = TAU / count
    return mod(angle, segment) - segment / 2.0


def rotate_2d(x: float, y: float, angle: float) -> Tuple[float, float]:
    """Rotate 2D point around origin.

    Args:
        x: X coordinate
        y: Y coordinate
        angle: Rotation angle in radians

    Returns:
        Tuple of (rotated_x, rotated_y)
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (
        x * cos_a - y * sin_a,
        x * sin_a + y * cos_a
    )


def warp(x: float, y: float, time: float, strength: float = 0.5) -> Tuple[float, float]:
    """Domain warping for organic motion.

    Displaces coordinates based on sine waves for flowing effects.

    Args:
        x: X coordinate
        y: Y coordinate
        time: Animation time
        strength: Warp intensity

    Returns:
        Tuple of (warped_x, warped_y)
    """
    return (
        x + strength * math.sin(y * 3.0 + time),
        y + strength * math.cos(x * 3.0 + time)
    )


# =============================================================================
# Noise & Hash Functions
# =============================================================================

def hash_1d(x: float) -> float:
    """Simple 1D hash function.

    Returns pseudo-random value in [0, 1) based on input.

    Args:
        x: Input value

    Returns:
        Pseudo-random value in [0, 1)
    """
    return fract(math.sin(x * 127.1) * 43758.5453)


def hash_2d(x: float, y: float) -> float:
    """Simple 2D hash function.

    Returns pseudo-random value in [0, 1) based on 2D input.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        Pseudo-random value in [0, 1)
    """
    return fract(math.sin(x * 127.1 + y * 311.7) * 43758.5453)


# =============================================================================
# Helper for numpy compatibility
# =============================================================================

def _np_floor(x):
    """Floor function that works with numpy arrays."""
    import numpy as np
    return np.floor(x)
