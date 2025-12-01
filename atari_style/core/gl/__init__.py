"""OpenGL rendering module for GPU-accelerated effects.

This module provides:
- GLRenderer: Base class for OpenGL rendering with moderngl
- ShaderUniforms: Shadertoy-compatible uniform management
- Fullscreen quad rendering utilities
- Framebuffer management for offscreen rendering

See docs/shader-roadmap.md for implementation details.
"""

from .renderer import GLRenderer
from .uniforms import ShaderUniforms, EffectPreset

__all__ = ['GLRenderer', 'ShaderUniforms', 'EffectPreset']
