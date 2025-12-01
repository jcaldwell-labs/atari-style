"""GLRenderer - GPU-accelerated rendering with moderngl.

This module provides the base class for all GPU-accelerated effects,
using OpenGL 3.3+ via moderngl for cross-platform shader rendering.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import moderngl
import numpy as np


# Standard vertex shader for fullscreen quad rendering
STANDARD_VERTEX_SHADER = '''
#version 330 core

in vec2 in_position;
out vec2 fragCoord;

void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    // Convert from [-1, 1] to [0, 1] for fragment shader
    fragCoord = (in_position + 1.0) / 2.0;
}
'''


class GLRenderer:
    """Base class for GPU-accelerated rendering using moderngl.

    Provides:
    - OpenGL context management (windowed or headless)
    - Fullscreen quad rendering for fragment shaders
    - Framebuffer management for offscreen rendering
    - Shader loading with error handling
    - Uniform management for Shadertoy-compatible shaders

    Example:
        renderer = GLRenderer(width=1920, height=1080, headless=True)
        program = renderer.load_shader('shaders/effects/plasma.frag')
        pixels = renderer.render(program, {'iTime': 1.5, 'iResolution': (1920, 1080)})
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        headless: bool = True
    ):
        """Initialize the GL renderer.

        Args:
            width: Framebuffer width in pixels
            height: Framebuffer height in pixels
            headless: If True, create standalone context (no window)
                     If False, requires existing OpenGL context (e.g., pygame)
        """
        self.width = width
        self.height = height
        self.headless = headless

        # Create OpenGL context
        try:
            if headless:
                self.ctx = moderngl.create_context(standalone=True)
            else:
                # Use existing context (must be created by pygame/glfw first)
                self.ctx = moderngl.create_context()
        except Exception as e:
            raise RuntimeError(f"Failed to create OpenGL context: {e}")

        # Store context info
        self.gl_version = self.ctx.version_code
        self.vendor = self.ctx.info.get('GL_VENDOR', 'Unknown')
        self.renderer_name = self.ctx.info.get('GL_RENDERER', 'Unknown')

        # Setup rendering infrastructure
        self._setup_quad()
        self._setup_framebuffer()

        # Cache for loaded programs
        self._program_cache: Dict[str, moderngl.Program] = {}

    def _setup_quad(self):
        """Create fullscreen quad for fragment shader rendering.

        The quad covers the entire NDC space [-1, 1] and will be
        rendered as a triangle strip.
        """
        # Fullscreen quad vertices (triangle strip)
        vertices = np.array([
            -1.0, -1.0,  # Bottom-left
             1.0, -1.0,  # Bottom-right
            -1.0,  1.0,  # Top-left
             1.0,  1.0,  # Top-right
        ], dtype='f4')

        self.quad_vbo = self.ctx.buffer(vertices)

    def _setup_framebuffer(self):
        """Create offscreen framebuffer for rendering."""
        # RGBA texture for color output
        self.texture = self.ctx.texture(
            (self.width, self.height),
            4,  # RGBA components
            dtype='f1'  # Unsigned byte per component
        )
        self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)

        # Framebuffer with color attachment
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.texture]
        )

    def resize(self, width: int, height: int):
        """Resize the framebuffer.

        Args:
            width: New width in pixels
            height: New height in pixels
        """
        if width == self.width and height == self.height:
            return

        self.width = width
        self.height = height

        # Release old resources
        self.texture.release()
        self.fbo.release()

        # Create new framebuffer
        self._setup_framebuffer()

    def load_shader(
        self,
        frag_path: str,
        vertex_shader: Optional[str] = None,
        cache: bool = True
    ) -> moderngl.Program:
        """Load and compile a fragment shader.

        Args:
            frag_path: Path to fragment shader file (.frag)
            vertex_shader: Custom vertex shader source (uses standard if None)
            cache: If True, cache compiled program for reuse

        Returns:
            Compiled moderngl.Program

        Raises:
            FileNotFoundError: If shader file doesn't exist
            RuntimeError: If shader compilation fails
        """
        # Check cache first
        if cache and frag_path in self._program_cache:
            return self._program_cache[frag_path]

        # Resolve path
        shader_path = Path(frag_path)
        if not shader_path.is_absolute():
            # Look relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            shader_path = project_root / frag_path

        if not shader_path.exists():
            raise FileNotFoundError(f"Shader not found: {shader_path}")

        # Read shader source
        frag_src = shader_path.read_text()
        vert_src = vertex_shader or STANDARD_VERTEX_SHADER

        # Compile program
        try:
            program = self.ctx.program(
                vertex_shader=vert_src,
                fragment_shader=frag_src
            )
        except Exception as e:
            raise RuntimeError(f"Shader compilation failed for {frag_path}: {e}")

        # Cache if requested
        if cache:
            self._program_cache[frag_path] = program

        return program

    def load_shader_source(
        self,
        frag_source: str,
        vertex_shader: Optional[str] = None
    ) -> moderngl.Program:
        """Compile a shader from source strings.

        Args:
            frag_source: Fragment shader GLSL source code
            vertex_shader: Custom vertex shader source (uses standard if None)

        Returns:
            Compiled moderngl.Program
        """
        vert_src = vertex_shader or STANDARD_VERTEX_SHADER

        try:
            return self.ctx.program(
                vertex_shader=vert_src,
                fragment_shader=frag_source
            )
        except Exception as e:
            raise RuntimeError(f"Shader compilation failed: {e}")

    def render(
        self,
        program: moderngl.Program,
        uniforms: Dict[str, Any]
    ) -> bytes:
        """Render shader to framebuffer and return pixel data.

        Args:
            program: Compiled shader program
            uniforms: Dictionary of uniform name -> value pairs
                     Supported types: float, int, tuple (vec2/3/4)

        Returns:
            Raw RGBA pixel data as bytes (width * height * 4)
        """
        # Bind framebuffer
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        # Set uniforms
        for name, value in uniforms.items():
            if name in program:
                program[name].value = value

        # Create VAO and render
        vao = self.ctx.vertex_array(
            program,
            [(self.quad_vbo, '2f', 'in_position')]
        )
        vao.render(moderngl.TRIANGLE_STRIP)
        vao.release()

        # Read pixels (RGBA, bottom-to-top)
        return self.fbo.read(components=4)

    def render_to_array(
        self,
        program: moderngl.Program,
        uniforms: Dict[str, Any]
    ) -> np.ndarray:
        """Render shader and return as numpy array.

        Args:
            program: Compiled shader program
            uniforms: Dictionary of uniform values

        Returns:
            numpy array of shape (height, width, 4) with dtype uint8
        """
        pixels = self.render(program, uniforms)
        arr = np.frombuffer(pixels, dtype=np.uint8)
        arr = arr.reshape((self.height, self.width, 4))
        # Flip vertically (OpenGL has origin at bottom-left)
        return np.flip(arr, axis=0)

    def get_info(self) -> Dict[str, Any]:
        """Get OpenGL context information.

        Returns:
            Dictionary with GL version, vendor, renderer info
        """
        return {
            'version': self.gl_version,
            'vendor': self.vendor,
            'renderer': self.renderer_name,
            'max_texture_size': self.ctx.info.get('GL_MAX_TEXTURE_SIZE', 0),
            'framebuffer_size': (self.width, self.height),
        }

    def release(self):
        """Release all OpenGL resources."""
        self._program_cache.clear()
        self.quad_vbo.release()
        self.texture.release()
        self.fbo.release()
        if self.headless:
            self.ctx.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False
