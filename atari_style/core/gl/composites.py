"""Composite animation management module (Phase 5).

Provides configuration and rendering for composite shader animations
that combine multiple effects with cross-modulation.

Composite Types:
    - plasma_lissajous: Plasma modulates Lissajous curve frequencies
    - flux_spiral: Fluid wave energy modulates spiral rotation
    - lissajous_plasma: Lissajous dynamics modulate plasma field

Usage:
    from atari_style.core.gl.composites import CompositeManager, COMPOSITES

    # List available composites
    print(list(COMPOSITES.keys()))

    # Render a single frame
    manager = CompositeManager()
    img = manager.render_frame('plasma_lissajous', time=2.0)

    # Render animation frames
    frames = manager.render_animation('flux_spiral', duration=5.0, fps=30)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time as time_module

try:
    from PIL import Image
except ImportError:
    Image = None

from .renderer import GLRenderer
from .uniforms import ShaderUniforms


@dataclass
class CompositeConfig:
    """Configuration for a composite shader animation."""
    name: str
    shader_path: str
    description: str
    default_params: Tuple[float, float, float, float]
    param_names: Tuple[str, str, str, str]
    param_ranges: Tuple[Tuple[float, float], ...]  # (min, max) for each param
    recommended_duration: float = 10.0
    default_color_mode: int = 0


# Composite animation configurations
COMPOSITES: Dict[str, CompositeConfig] = {
    'plasma_lissajous': CompositeConfig(
        name='Plasma-Lissajous',
        shader_path='atari_style/shaders/effects/plasma_lissajous.frag',
        description='Plasma field modulates Lissajous curve frequencies, creating organic morphing patterns',
        default_params=(0.1, 0.3, 0.5, 0.7),
        param_names=('plasma_freq', 'liss_base_freq', 'modulation', 'trail'),
        param_ranges=((0.05, 0.3), (0.1, 0.8), (0.0, 1.0), (0.0, 1.0)),
        recommended_duration=12.0,
        default_color_mode=0
    ),
    'flux_spiral': CompositeConfig(
        name='Flux-Spiral',
        shader_path='atari_style/shaders/effects/flux_spiral.frag',
        description='Fluid wave energy modulates spiral rotation speed and intensity',
        default_params=(0.3, 1.0, 0.5, 0.3),
        param_names=('wave_freq', 'base_rotation', 'modulation', 'num_spirals'),
        param_ranges=((0.1, 0.5), (0.5, 2.0), (0.0, 1.0), (0.1, 0.8)),
        recommended_duration=10.0,
        default_color_mode=0
    ),
    'lissajous_plasma': CompositeConfig(
        name='Lissajous-Plasma',
        shader_path='atari_style/shaders/effects/lissajous_plasma.frag',
        description='Lissajous curve dynamics modulate plasma field frequencies and colors',
        default_params=(0.5, 0.7, 0.6, 0.3),
        param_names=('liss_speed', 'plasma_intensity', 'curve_influence', 'color_shift'),
        param_ranges=((0.1, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0)),
        recommended_duration=15.0,
        default_color_mode=0
    ),
}


class CompositeManager:
    """Manager for composite shader animations.

    Handles rendering of composite effects with automatic resource management.
    """

    def __init__(self, width: int = 800, height: int = 600):
        """Initialize composite manager.

        Args:
            width: Default render width
            height: Default render height
        """
        self.width = width
        self.height = height
        self._renderer: Optional[GLRenderer] = None
        self._cached_programs: Dict[str, object] = {}

    def _get_renderer(self) -> GLRenderer:
        """Get or create renderer instance."""
        if self._renderer is None:
            self._renderer = GLRenderer(self.width, self.height, headless=True)
        return self._renderer

    def _get_program(self, composite_name: str):
        """Get or load shader program for a composite."""
        if composite_name not in self._cached_programs:
            config = COMPOSITES[composite_name]
            renderer = self._get_renderer()
            self._cached_programs[composite_name] = renderer.load_shader(config.shader_path)
        return self._cached_programs[composite_name]

    def render_frame(self, composite_name: str, time_val: float = 0.0,
                     params: Optional[Tuple[float, float, float, float]] = None,
                     color_mode: Optional[int] = None,
                     width: Optional[int] = None,
                     height: Optional[int] = None) -> 'Image.Image':
        """Render a single frame of a composite animation.

        Args:
            composite_name: Name of the composite (plasma_lissajous, flux_spiral, lissajous_plasma)
            time_val: Animation time in seconds
            params: Parameter tuple (overrides defaults if provided)
            color_mode: Color palette (0-3, uses default if None)
            width: Render width (uses default if None)
            height: Render height (uses default if None)

        Returns:
            PIL Image of the rendered frame

        Raises:
            ValueError: If composite_name is not recognized
            ImportError: If Pillow is not available
        """
        if Image is None:
            raise ImportError("Pillow required: pip install Pillow")

        if composite_name not in COMPOSITES:
            raise ValueError(f"Unknown composite: {composite_name}. Available: {list(COMPOSITES.keys())}")

        config = COMPOSITES[composite_name]
        w = width or self.width
        h = height or self.height

        # Use specific size renderer if different from default
        if w != self.width or h != self.height:
            renderer = GLRenderer(w, h, headless=True)
            program = renderer.load_shader(config.shader_path)
        else:
            renderer = self._get_renderer()
            program = self._get_program(composite_name)

        # Set up uniforms
        uniforms = ShaderUniforms()
        uniforms.set_resolution(w, h)
        uniforms.iTime = time_val
        uniforms.iParams = params or config.default_params
        uniforms.iColorMode = color_mode if color_mode is not None else config.default_color_mode

        # Render
        arr = renderer.render_to_array(program, uniforms.to_dict())
        return Image.fromarray(arr, 'RGBA')

    def render_animation(self, composite_name: str, duration: float = 5.0,
                         fps: int = 30, params: Optional[Tuple[float, float, float, float]] = None,
                         color_mode: Optional[int] = None) -> List['Image.Image']:
        """Render animation frames for a composite.

        Args:
            composite_name: Name of the composite
            duration: Animation duration in seconds
            fps: Frames per second
            params: Parameter tuple (optional)
            color_mode: Color palette (optional)

        Returns:
            List of PIL Images representing animation frames
        """
        frames = []
        total_frames = int(duration * fps)

        for i in range(total_frames):
            time_val = i / fps
            frame = self.render_frame(composite_name, time_val, params, color_mode)
            frames.append(frame)

        return frames

    def get_config(self, composite_name: str) -> CompositeConfig:
        """Get configuration for a composite.

        Args:
            composite_name: Name of the composite

        Returns:
            CompositeConfig with all configuration details
        """
        if composite_name not in COMPOSITES:
            raise ValueError(f"Unknown composite: {composite_name}")
        return COMPOSITES[composite_name]

    def benchmark(self, composite_name: str, frames: int = 60) -> Dict[str, float]:
        """Benchmark rendering performance for a composite.

        Args:
            composite_name: Name of the composite to benchmark
            frames: Number of frames to render

        Returns:
            Dict with timing statistics
        """
        config = COMPOSITES[composite_name]
        times = []

        for i in range(frames):
            time_val = i / 30.0
            start = time_module.time()
            self.render_frame(composite_name, time_val)
            elapsed = time_module.time() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        return {
            'composite': composite_name,
            'frames': frames,
            'total_time': sum(times),
            'avg_frame_time': avg_time,
            'fps': 1.0 / avg_time if avg_time > 0 else 0,
            'min_time': min(times),
            'max_time': max(times),
        }


def list_composites() -> List[str]:
    """Get list of available composite names."""
    return list(COMPOSITES.keys())


def get_composite_info(composite_name: str) -> Dict:
    """Get detailed information about a composite.

    Args:
        composite_name: Name of the composite

    Returns:
        Dict with composite details
    """
    config = COMPOSITES[composite_name]
    return {
        'name': config.name,
        'description': config.description,
        'shader': config.shader_path,
        'params': dict(zip(config.param_names, config.default_params)),
        'param_ranges': dict(zip(config.param_names, config.param_ranges)),
        'recommended_duration': config.recommended_duration,
        'default_color_mode': config.default_color_mode,
    }
