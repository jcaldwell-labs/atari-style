"""Shader uniform management for Shadertoy-compatible rendering.

This module provides a structured way to manage shader uniforms,
following Shadertoy conventions for easy shader porting.
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any


@dataclass
class ShaderUniforms:
    """Shadertoy-compatible uniform container.

    Standard uniforms follow Shadertoy naming conventions:
    - iTime: Elapsed time in seconds
    - iResolution: Viewport resolution (width, height)
    - iMouse: Mouse/joystick position in normalized coords
    - iParams: 4 custom parameters for effect control

    Example:
        uniforms = ShaderUniforms(iTime=1.5, iResolution=(1920, 1080))
        uniforms.iParams = (0.3, 0.7, 0.5, 0.2)
        renderer.render(program, uniforms.to_dict())
    """

    # Time in seconds since animation start
    iTime: float = 0.0

    # Viewport resolution (width, height)
    iResolution: Tuple[float, float] = (1920.0, 1080.0)

    # Mouse/joystick position, normalized to [-1, 1] or [0, 1]
    iMouse: Tuple[float, float] = (0.0, 0.0)

    # Four custom parameters for effect control
    # Typically mapped to joystick axes or sliders
    iParams: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 0.5)

    # Animation speed multiplier
    iSpeed: float = 1.0

    # Color mode selector (integer)
    iColorMode: int = 0

    # Frame number (for deterministic animations)
    iFrame: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for passing to renderer.

        Returns:
            Dictionary mapping uniform names to values
        """
        return {
            'iTime': self.iTime,
            'iResolution': self.iResolution,
            'iMouse': self.iMouse,
            'iParams': self.iParams,
            'iSpeed': self.iSpeed,
            'iColorMode': self.iColorMode,
            'iFrame': self.iFrame,
        }

    def update_time(self, dt: float):
        """Advance time by delta.

        Args:
            dt: Time delta in seconds
        """
        self.iTime += dt * self.iSpeed
        self.iFrame += 1

    def set_resolution(self, width: int, height: int):
        """Set viewport resolution.

        Args:
            width: Width in pixels
            height: Height in pixels
        """
        self.iResolution = (float(width), float(height))

    def set_param(self, index: int, value: float):
        """Set a single parameter by index.

        Args:
            index: Parameter index (0-3)
            value: Parameter value (typically 0.0-1.0)
        """
        params = list(self.iParams)
        params[index] = max(0.0, min(1.0, value))
        self.iParams = tuple(params)

    def reset(self):
        """Reset all uniforms to defaults."""
        self.iTime = 0.0
        self.iMouse = (0.0, 0.0)
        self.iParams = (0.5, 0.5, 0.5, 0.5)
        self.iSpeed = 1.0
        self.iColorMode = 0
        self.iFrame = 0


@dataclass
class EffectPreset:
    """Stores a preset configuration for an effect.

    Used for save/load functionality and preset tours.
    """

    name: str
    params: Tuple[float, float, float, float]
    speed: float = 1.0
    color_mode: int = 0
    description: str = ""

    def apply_to(self, uniforms: ShaderUniforms):
        """Apply this preset to a uniforms object.

        Args:
            uniforms: ShaderUniforms instance to modify
        """
        uniforms.iParams = self.params
        uniforms.iSpeed = self.speed
        uniforms.iColorMode = self.color_mode

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'params': list(self.params),
            'speed': self.speed,
            'color_mode': self.color_mode,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EffectPreset':
        """Create preset from dictionary."""
        return cls(
            name=data['name'],
            params=tuple(data['params']),
            speed=data.get('speed', 1.0),
            color_mode=data.get('color_mode', 0),
            description=data.get('description', ''),
        )
