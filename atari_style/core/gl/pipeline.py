"""Post-processing pipeline for multi-pass GPU rendering.

This module provides infrastructure for chaining multiple shader passes,
enabling effects like CRT simulation, color grading, and bloom.

Example:
    renderer = GLRenderer(1920, 1080, headless=True)
    pipeline = PostProcessPipeline(renderer)

    # Add CRT effect
    pipeline.add_pass('atari_style/shaders/post/crt.frag', {
        'scanlineIntensity': 0.5,
        'curvature': 0.1,
    })

    # Render effect with post-processing
    pixels = pipeline.render(effect_program, effect_uniforms)
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path

import moderngl
import numpy as np

from .renderer import GLRenderer


@dataclass
class CRTPreset:
    """Preset configuration for CRT effects."""
    name: str
    scanlineIntensity: float = 0.5
    curvature: float = 0.1
    vignetteStrength: float = 0.3
    rgbOffset: float = 0.002
    brightness: float = 1.0
    shadowMask: float = 0.3
    flickerAmount: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to uniform dictionary."""
        return {
            'scanlineIntensity': self.scanlineIntensity,
            'curvature': self.curvature,
            'vignetteStrength': self.vignetteStrength,
            'rgbOffset': self.rgbOffset,
            'brightness': self.brightness,
            'shadowMask': self.shadowMask,
            'flickerAmount': self.flickerAmount,
        }


# Predefined CRT presets
CRT_PRESETS = {
    'off': CRTPreset(
        name='Off',
        scanlineIntensity=0.0,
        curvature=0.0,
        vignetteStrength=0.0,
        rgbOffset=0.0,
        brightness=1.0,
        shadowMask=0.0,
        flickerAmount=0.0,
    ),
    'subtle': CRTPreset(
        name='Subtle',
        scanlineIntensity=0.2,
        curvature=0.03,
        vignetteStrength=0.2,
        rgbOffset=0.001,
        brightness=1.05,
        shadowMask=0.15,
        flickerAmount=0.0,
    ),
    'classic': CRTPreset(
        name='Classic',
        scanlineIntensity=0.5,
        curvature=0.08,
        vignetteStrength=0.4,
        rgbOffset=0.002,
        brightness=1.1,
        shadowMask=0.3,
        flickerAmount=0.02,
    ),
    'heavy': CRTPreset(
        name='Heavy',
        scanlineIntensity=0.8,
        curvature=0.15,
        vignetteStrength=0.6,
        rgbOffset=0.004,
        brightness=1.2,
        shadowMask=0.5,
        flickerAmount=0.05,
    ),
    'arcade': CRTPreset(
        name='Arcade',
        scanlineIntensity=0.6,
        curvature=0.12,
        vignetteStrength=0.35,
        rgbOffset=0.003,
        brightness=1.15,
        shadowMask=0.4,
        flickerAmount=0.03,
    ),
    'monitor': CRTPreset(
        name='Monitor',
        scanlineIntensity=0.3,
        curvature=0.05,
        vignetteStrength=0.25,
        rgbOffset=0.0015,
        brightness=1.0,
        shadowMask=0.2,
        flickerAmount=0.01,
    ),
}


@dataclass
class PalettePreset:
    """Preset configuration for color palette reduction."""
    name: str
    colorLevels: float = 16.0  # Colors per channel
    dithering: int = 1  # 0 = off, 1 = on
    ditherScale: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'colorLevels': self.colorLevels,
            'dithering': self.dithering,
            'ditherScale': self.ditherScale,
        }


# Predefined palette presets
PALETTE_PRESETS = {
    'off': PalettePreset(name='Off', colorLevels=256.0, dithering=0),
    'atari': PalettePreset(name='Atari 2600', colorLevels=4.0, dithering=1),
    'nes': PalettePreset(name='NES', colorLevels=8.0, dithering=1),
    'cga': PalettePreset(name='CGA', colorLevels=4.0, dithering=1),
    'ega': PalettePreset(name='EGA', colorLevels=8.0, dithering=1),
    'vga': PalettePreset(name='VGA', colorLevels=16.0, dithering=1),
    'retro': PalettePreset(name='Retro', colorLevels=8.0, dithering=1),
}


@dataclass
class ASCIIPreset:
    """Preset configuration for ASCII art post-processing.

    Converts GL output to terminal-style ASCII art aesthetic.
    """
    name: str
    charWidth: float = 8.0       # Character cell width in pixels
    charHeight: float = 16.0     # Character cell height in pixels
    colorMode: int = 0           # 0=monochrome green, 1=colored, 2=neon
    bgBrightness: float = 0.02   # Background darkness

    def to_dict(self) -> Dict[str, Any]:
        return {
            'charWidth': self.charWidth,
            'charHeight': self.charHeight,
            'colorMode': self.colorMode,
            'bgBrightness': self.bgBrightness,
        }


# Predefined ASCII presets
ASCII_PRESETS = {
    'off': ASCIIPreset(name='Off', charWidth=1.0, charHeight=1.0, colorMode=1, bgBrightness=0.0),
    'terminal': ASCIIPreset(name='Terminal', charWidth=8.0, charHeight=16.0, colorMode=0, bgBrightness=0.02),
    'hires': ASCIIPreset(name='High-Res', charWidth=4.0, charHeight=8.0, colorMode=1, bgBrightness=0.01),
    'lores': ASCIIPreset(name='Low-Res', charWidth=16.0, charHeight=32.0, colorMode=0, bgBrightness=0.03),
    'neon': ASCIIPreset(name='Neon', charWidth=6.0, charHeight=12.0, colorMode=2, bgBrightness=0.0),
    'colored': ASCIIPreset(name='Colored', charWidth=8.0, charHeight=16.0, colorMode=1, bgBrightness=0.02),
}


@dataclass
class PhosphorPreset:
    """Preset configuration for phosphor persistence effects.

    Simulates the phosphor decay of CRT monitors where bright pixels
    leave a fading trail. This creates the characteristic "ghosting"
    effect visible on fast-moving content.
    """
    name: str
    persistence: float = 0.7     # How long glow persists (0.0 - 0.95)
    glowIntensity: float = 1.0   # Brightness of the trail (0.5 - 2.0)
    colorBleed: float = 0.2      # RGB decay difference (0.0 - 0.5)
    burnIn: float = 0.0          # Static element burn-in (0.0 - 0.3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'persistence': self.persistence,
            'glowIntensity': self.glowIntensity,
            'colorBleed': self.colorBleed,
            'burnIn': self.burnIn,
        }


# Predefined phosphor presets
PHOSPHOR_PRESETS = {
    'off': PhosphorPreset(
        name='Off',
        persistence=0.0,
        glowIntensity=0.0,
        colorBleed=0.0,
        burnIn=0.0,
    ),
    'subtle': PhosphorPreset(
        name='Subtle',
        persistence=0.5,
        glowIntensity=0.8,
        colorBleed=0.1,
        burnIn=0.0,
    ),
    'classic': PhosphorPreset(
        name='Classic',
        persistence=0.7,
        glowIntensity=1.0,
        colorBleed=0.2,
        burnIn=0.0,
    ),
    'heavy': PhosphorPreset(
        name='Heavy',
        persistence=0.85,
        glowIntensity=1.3,
        colorBleed=0.3,
        burnIn=0.05,
    ),
    'arcade': PhosphorPreset(
        name='Arcade',
        persistence=0.75,
        glowIntensity=1.2,
        colorBleed=0.25,
        burnIn=0.0,
    ),
    'green_terminal': PhosphorPreset(
        name='Green Terminal',
        persistence=0.8,
        glowIntensity=1.1,
        colorBleed=0.0,  # Monochrome, no color bleed
        burnIn=0.1,      # Terminals often had burn-in
    ),
    'motion_blur': PhosphorPreset(
        name='Motion Blur',
        persistence=0.9,
        glowIntensity=1.5,
        colorBleed=0.15,
        burnIn=0.0,
    ),
}


class RenderPass:
    """A single render pass in the pipeline."""

    def __init__(
        self,
        ctx: moderngl.Context,
        program: moderngl.Program,
        width: int,
        height: int,
        uniforms: Dict[str, Any] = None
    ):
        self.ctx = ctx
        self.program = program
        self.uniforms = uniforms or {}

        # Create framebuffer for this pass
        self.texture = ctx.texture((width, height), 4, dtype='f1')
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.fbo = ctx.framebuffer(color_attachments=[self.texture])

    def set_uniforms(self, uniforms: Dict[str, Any]):
        """Update pass uniforms."""
        self.uniforms.update(uniforms)

    def release(self):
        """Release GPU resources."""
        self.texture.release()
        self.fbo.release()


class PostProcessPipeline:
    """Multi-pass post-processing pipeline.

    Chains multiple shader passes together, with each pass reading
    from the previous pass's output texture.

    Architecture:
        Effect Shader --> Pass 1 (CRT) --> Pass 2 (Palette) --> Output

    Example:
        pipeline = PostProcessPipeline(renderer)
        pipeline.add_crt_pass('classic')
        pipeline.add_palette_pass('nes')
        pixels = pipeline.render(effect_program, effect_uniforms)
    """

    def __init__(self, renderer: GLRenderer):
        """Initialize the pipeline.

        Args:
            renderer: GLRenderer instance for context and utilities
        """
        self.renderer = renderer
        self.ctx = renderer.ctx
        self.width = renderer.width
        self.height = renderer.height

        self.passes: List[RenderPass] = []

        # Create quad VBO for post-process rendering
        vertices = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
        ], dtype='f4')
        self.quad_vbo = self.ctx.buffer(vertices)

        # Track current CRT, palette, ASCII, and phosphor settings
        self.crt_preset: Optional[str] = None
        self.palette_preset: Optional[str] = None
        self.ascii_preset: Optional[str] = None
        self.phosphor_preset: Optional[str] = None

        # Phosphor persistence requires ping-pong buffers for temporal feedback
        self._phosphor_textures: Optional[tuple] = None
        self._phosphor_fbos: Optional[tuple] = None
        self._phosphor_frame: int = 0

    def _load_shader(self, shader_path: str) -> moderngl.Program:
        """Load a post-processing shader."""
        path = Path(shader_path)
        if not path.is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            path = project_root / shader_path

        if not path.exists():
            raise FileNotFoundError(f"Shader not found: {path}")

        frag_src = path.read_text()

        # Post-process shaders use texture sampling, need modified vertex shader
        vert_src = '''
#version 330 core
in vec2 in_position;
out vec2 fragCoord;

void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    fragCoord = (in_position + 1.0) / 2.0;
}
'''
        return self.ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)

    def add_pass(
        self,
        shader_path: str,
        uniforms: Dict[str, Any] = None
    ) -> int:
        """Add a custom render pass.

        Args:
            shader_path: Path to fragment shader
            uniforms: Initial uniform values

        Returns:
            Index of the added pass
        """
        program = self._load_shader(shader_path)
        render_pass = RenderPass(
            self.ctx, program, self.width, self.height, uniforms
        )
        self.passes.append(render_pass)
        return len(self.passes) - 1

    def add_crt_pass(self, preset: str = 'classic') -> int:
        """Add CRT post-processing pass.

        Args:
            preset: Preset name ('off', 'subtle', 'classic', 'heavy', 'arcade', 'monitor')

        Returns:
            Index of the CRT pass
        """
        if preset not in CRT_PRESETS:
            raise ValueError(f"Unknown CRT preset: {preset}. Available: {list(CRT_PRESETS.keys())}")

        self.crt_preset = preset
        uniforms = CRT_PRESETS[preset].to_dict()
        return self.add_pass('atari_style/shaders/post/crt.frag', uniforms)

    def add_palette_pass(self, preset: str = 'retro') -> int:
        """Add palette reduction pass.

        Args:
            preset: Preset name ('off', 'atari', 'nes', 'cga', 'ega', 'vga', 'retro')

        Returns:
            Index of the palette pass
        """
        if preset not in PALETTE_PRESETS:
            raise ValueError(f"Unknown palette preset: {preset}. Available: {list(PALETTE_PRESETS.keys())}")

        self.palette_preset = preset
        uniforms = PALETTE_PRESETS[preset].to_dict()
        return self.add_pass('atari_style/shaders/post/palette.frag', uniforms)

    def add_ascii_pass(self, preset: str = 'terminal') -> int:
        """Add ASCII art post-processing pass.

        Converts GL output to terminal-style ASCII aesthetic.
        Great for bridging GL quality with authentic terminal look.

        Args:
            preset: Preset name ('off', 'terminal', 'hires', 'lores', 'neon', 'colored')

        Returns:
            Index of the ASCII pass
        """
        if preset not in ASCII_PRESETS:
            raise ValueError(f"Unknown ASCII preset: {preset}. Available: {list(ASCII_PRESETS.keys())}")

        self.ascii_preset = preset
        uniforms = ASCII_PRESETS[preset].to_dict()
        return self.add_pass('atari_style/shaders/post/ascii.frag', uniforms)

    def set_crt_preset(self, preset: str):
        """Change CRT preset on existing pass."""
        if self.crt_preset is None:
            raise RuntimeError("No CRT pass added. Call add_crt_pass() first.")

        if preset not in CRT_PRESETS:
            raise ValueError(f"Unknown CRT preset: {preset}")

        self.crt_preset = preset
        # Find and update CRT pass
        for p in self.passes:
            if 'scanlineIntensity' in p.uniforms:
                p.set_uniforms(CRT_PRESETS[preset].to_dict())
                break

    def set_palette_preset(self, preset: str):
        """Change palette preset on existing pass."""
        if self.palette_preset is None:
            raise RuntimeError("No palette pass added. Call add_palette_pass() first.")

        if preset not in PALETTE_PRESETS:
            raise ValueError(f"Unknown palette preset: {preset}")

        self.palette_preset = preset
        # Find and update palette pass
        for p in self.passes:
            if 'colorLevels' in p.uniforms:
                p.set_uniforms(PALETTE_PRESETS[preset].to_dict())
                break

    def set_ascii_preset(self, preset: str):
        """Change ASCII preset on existing pass."""
        if self.ascii_preset is None:
            raise RuntimeError("No ASCII pass added. Call add_ascii_pass() first.")

        if preset not in ASCII_PRESETS:
            raise ValueError(f"Unknown ASCII preset: {preset}")

        self.ascii_preset = preset
        # Find and update ASCII pass
        for p in self.passes:
            if 'charWidth' in p.uniforms:
                p.set_uniforms(ASCII_PRESETS[preset].to_dict())
                break

    def add_phosphor_pass(self, preset: str = 'classic') -> int:
        """Add phosphor persistence post-processing pass.

        Simulates CRT phosphor decay where bright pixels leave a fading
        trail. This effect requires temporal feedback (previous frame data)
        and uses ping-pong framebuffers internally.

        Best applied early in the post-processing chain (before CRT/palette)
        for authentic results.

        Args:
            preset: Preset name ('off', 'subtle', 'classic', 'heavy',
                   'arcade', 'green_terminal', 'motion_blur')

        Returns:
            Index of the phosphor pass
        """
        if preset not in PHOSPHOR_PRESETS:
            raise ValueError(
                f"Unknown phosphor preset: {preset}. "
                f"Available: {list(PHOSPHOR_PRESETS.keys())}"
            )

        self.phosphor_preset = preset
        uniforms = PHOSPHOR_PRESETS[preset].to_dict()

        # Create ping-pong textures for temporal feedback
        if self._phosphor_textures is None:
            self._phosphor_textures = (
                self.ctx.texture((self.width, self.height), 4, dtype='f1'),
                self.ctx.texture((self.width, self.height), 4, dtype='f1'),
            )
            for tex in self._phosphor_textures:
                tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._phosphor_fbos = (
                self.ctx.framebuffer(color_attachments=[self._phosphor_textures[0]]),
                self.ctx.framebuffer(color_attachments=[self._phosphor_textures[1]]),
            )
            # Clear both buffers initially
            for fbo in self._phosphor_fbos:
                fbo.use()
                self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        return self.add_pass('atari_style/shaders/post/phosphor.frag', uniforms)

    def set_phosphor_preset(self, preset: str):
        """Change phosphor preset on existing pass."""
        if self.phosphor_preset is None:
            raise RuntimeError("No phosphor pass added. Call add_phosphor_pass() first.")

        if preset not in PHOSPHOR_PRESETS:
            raise ValueError(f"Unknown phosphor preset: {preset}")

        self.phosphor_preset = preset
        # Find and update phosphor pass
        for p in self.passes:
            if 'persistence' in p.uniforms:
                p.set_uniforms(PHOSPHOR_PRESETS[preset].to_dict())
                break

    def update_pass_uniforms(self, pass_index: int, uniforms: Dict[str, Any]):
        """Update uniforms for a specific pass.

        Args:
            pass_index: Index of the pass to update
            uniforms: Uniform values to set/update
        """
        if 0 <= pass_index < len(self.passes):
            self.passes[pass_index].set_uniforms(uniforms)

    def render(
        self,
        effect_program: moderngl.Program,
        effect_uniforms: Dict[str, Any],
        time: float = 0.0
    ) -> bytes:
        """Render effect with all post-processing passes.

        Args:
            effect_program: The main effect shader program
            effect_uniforms: Uniforms for the main effect
            time: Current time for animated effects

        Returns:
            Raw RGBA pixel data
        """
        # First pass: render main effect to renderer's FBO
        self.renderer.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        for name, value in effect_uniforms.items():
            if name in effect_program:
                effect_program[name].value = value

        vao = self.ctx.vertex_array(
            effect_program,
            [(self.renderer.quad_vbo, '2f', 'in_position')]
        )
        vao.render(moderngl.TRIANGLE_STRIP)
        vao.release()

        # If no post-process passes, return main effect output
        if not self.passes:
            return self.renderer.fbo.read(components=4)

        # Chain post-process passes
        input_texture = self.renderer.texture

        for i, render_pass in enumerate(self.passes):
            # Check if this is a phosphor pass (needs temporal feedback)
            is_phosphor = 'persistence' in render_pass.uniforms

            if is_phosphor and self._phosphor_textures is not None:
                # Phosphor pass uses ping-pong buffers
                current_idx = self._phosphor_frame % 2
                prev_idx = (self._phosphor_frame + 1) % 2

                # Render to current phosphor buffer
                self._phosphor_fbos[current_idx].use()
                self.ctx.clear(0.0, 0.0, 0.0, 1.0)

                # Bind current frame to iChannel0
                input_texture.use(location=0)
                # Bind previous frame to iChannel1 for persistence
                self._phosphor_textures[prev_idx].use(location=1)

                program = render_pass.program
                if 'iChannel0' in program:
                    program['iChannel0'].value = 0
                if 'iChannel1' in program:
                    program['iChannel1'].value = 1
                if 'iResolution' in program:
                    program['iResolution'].value = (float(self.width), float(self.height))
                if 'iTime' in program:
                    program['iTime'].value = time

                for name, value in render_pass.uniforms.items():
                    if name in program:
                        program[name].value = value

                # Render quad
                pass_vao = self.ctx.vertex_array(
                    program,
                    [(self.quad_vbo, '2f', 'in_position')]
                )
                pass_vao.render(moderngl.TRIANGLE_STRIP)
                pass_vao.release()

                # Swap buffers for next frame
                self._phosphor_frame += 1

                # Output for next pass is current phosphor texture
                input_texture = self._phosphor_textures[current_idx]

                # Also copy result to the regular pass texture for consistency
                render_pass.fbo.use()
                self._phosphor_textures[current_idx].use(location=0)
                # Simple blit by re-rendering (could optimize with direct copy)
                self.ctx.copy_framebuffer(
                    render_pass.fbo, self._phosphor_fbos[current_idx]
                )
            else:
                # Standard pass without temporal feedback
                render_pass.fbo.use()
                self.ctx.clear(0.0, 0.0, 0.0, 1.0)

                # Bind input texture
                input_texture.use(location=0)

                # Set uniforms
                program = render_pass.program
                if 'iChannel0' in program:
                    program['iChannel0'].value = 0
                if 'iResolution' in program:
                    program['iResolution'].value = (float(self.width), float(self.height))
                if 'iTime' in program:
                    program['iTime'].value = time

                for name, value in render_pass.uniforms.items():
                    if name in program:
                        program[name].value = value

                # Render quad
                pass_vao = self.ctx.vertex_array(
                    program,
                    [(self.quad_vbo, '2f', 'in_position')]
                )
                pass_vao.render(moderngl.TRIANGLE_STRIP)
                pass_vao.release()

                # Output becomes input for next pass
                input_texture = render_pass.texture

        # Read final output
        return self.passes[-1].fbo.read(components=4)

    def render_to_array(
        self,
        effect_program: moderngl.Program,
        effect_uniforms: Dict[str, Any],
        time: float = 0.0
    ) -> np.ndarray:
        """Render effect and return as numpy array.

        Args:
            effect_program: The main effect shader program
            effect_uniforms: Uniforms for the main effect
            time: Current time for animated effects

        Returns:
            numpy array of shape (height, width, 4) with dtype uint8
        """
        pixels = self.render(effect_program, effect_uniforms, time)
        arr = np.frombuffer(pixels, dtype=np.uint8)
        arr = arr.reshape((self.height, self.width, 4))
        return np.flip(arr, axis=0)

    def resize(self, width: int, height: int):
        """Resize all framebuffers in the pipeline.

        Args:
            width: New width
            height: New height
        """
        self.width = width
        self.height = height
        self.renderer.resize(width, height)

        # Recreate pass framebuffers
        for render_pass in self.passes:
            render_pass.texture.release()
            render_pass.fbo.release()
            render_pass.texture = self.ctx.texture((width, height), 4, dtype='f1')
            render_pass.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            render_pass.fbo = self.ctx.framebuffer(color_attachments=[render_pass.texture])

        # Recreate phosphor ping-pong buffers if active
        if self._phosphor_textures is not None:
            for tex in self._phosphor_textures:
                tex.release()
            for fbo in self._phosphor_fbos:
                fbo.release()
            self._phosphor_textures = (
                self.ctx.texture((width, height), 4, dtype='f1'),
                self.ctx.texture((width, height), 4, dtype='f1'),
            )
            for tex in self._phosphor_textures:
                tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._phosphor_fbos = (
                self.ctx.framebuffer(color_attachments=[self._phosphor_textures[0]]),
                self.ctx.framebuffer(color_attachments=[self._phosphor_textures[1]]),
            )
            # Clear both buffers
            for fbo in self._phosphor_fbos:
                fbo.use()
                self.ctx.clear(0.0, 0.0, 0.0, 1.0)

    def release(self):
        """Release all GPU resources."""
        for render_pass in self.passes:
            render_pass.release()
        self.passes.clear()
        self.quad_vbo.release()

        # Release phosphor buffers if active
        if self._phosphor_textures is not None:
            for tex in self._phosphor_textures:
                tex.release()
            for fbo in self._phosphor_fbos:
                fbo.release()
            self._phosphor_textures = None
            self._phosphor_fbos = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


def get_crt_preset_names() -> List[str]:
    """Get list of available CRT preset names."""
    return list(CRT_PRESETS.keys())


def get_palette_preset_names() -> List[str]:
    """Get list of available palette preset names."""
    return list(PALETTE_PRESETS.keys())


def get_ascii_preset_names() -> List[str]:
    """Get list of available ASCII preset names."""
    return list(ASCII_PRESETS.keys())


def get_phosphor_preset_names() -> List[str]:
    """Get list of available phosphor preset names."""
    return list(PHOSPHOR_PRESETS.keys())
