"""Shared font loading utility for consistent monospace font resolution.

Centralizes the font loading cascade pattern used across renderers,
eliminating duplicated try/except blocks and ensuring cross-platform
font discovery.

Usage:
    from atari_style.utils.fonts import load_monospace_font

    font = load_monospace_font(22)
    font = load_monospace_font(16, preferred_paths=['/my/custom/font.ttf'])
"""

import logging
from typing import Optional

from PIL import ImageFont

logger = logging.getLogger(__name__)

DEFAULT_FONT_PATHS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
    '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf',
    '/usr/share/fonts/TTF/DejaVuSansMono.ttf',
    '/System/Library/Fonts/Menlo.ttc',
    'C:/Windows/Fonts/consola.ttf',
]


def load_monospace_font(
    size: int,
    preferred_paths: Optional[list[str]] = None,
) -> 'ImageFont.FreeTypeFont':
    """Load a monospace font, trying paths in order with a fallback.

    Attempts to load a TrueType monospace font by iterating through
    preferred paths first, then the default cross-platform paths.
    Falls back to PIL's built-in default font if no TrueType font
    is found.

    Args:
        size: Font size in points.
        preferred_paths: Optional list of font file paths to try before
            the defaults.

    Returns:
        A PIL ImageFont instance. May be the built-in bitmap font if
        no TrueType fonts were found.
    """
    candidates = list(preferred_paths or []) + DEFAULT_FONT_PATHS

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue

    logger.warning(
        "No monospace TrueType font found; falling back to PIL default. "
        "Text rendering may not be monospaced."
    )
    return ImageFont.load_default()
