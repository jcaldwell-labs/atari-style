"""OpenGL rendering module for GPU-accelerated effects.

This module provides:
- GLRenderer: Base class for OpenGL rendering with moderngl
- ShaderUniforms: Shadertoy-compatible uniform management
- PostProcessPipeline: Multi-pass post-processing chain
- CRT and palette reduction presets
- Fullscreen quad rendering utilities
- Framebuffer management for offscreen rendering

See docs/shader-roadmap.md for implementation details.
"""

from .renderer import GLRenderer
from .uniforms import ShaderUniforms, EffectPreset
from .pipeline import (
    PostProcessPipeline,
    CRTPreset,
    PalettePreset,
    CRT_PRESETS,
    PALETTE_PRESETS,
    get_crt_preset_names,
    get_palette_preset_names,
)

__all__ = [
    'GLRenderer',
    'ShaderUniforms',
    'EffectPreset',
    'PostProcessPipeline',
    'CRTPreset',
    'PalettePreset',
    'CRT_PRESETS',
    'PALETTE_PRESETS',
    'get_crt_preset_names',
    'get_palette_preset_names',
]
