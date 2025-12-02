"""Interactive joystick controller for GPU shader visualizers.

Control composite shader parameters in real-time with a joystick.

Controls:
    Left Stick X/Y:  param[0], param[1]
    Right Stick X/Y: param[2], param[3] (or triggers/shoulder buttons)
    A / Button 0:    Cycle color mode (0-3)
    B / Button 1:    Save current params to slot
    X / Button 2:    Load saved params
    Y / Button 3:    Reset to defaults
    D-Pad Up/Down:   Switch composite
    Start / Button 7: Toggle HUD

Usage:
    python -m atari_style.demos.visualizers.shader_controller
    python -m atari_style.demos.visualizers.shader_controller --composite flux_spiral
"""

import sys
import time
import json
import os
from typing import Optional, Tuple, List
from dataclasses import dataclass, field

try:
    import pygame
    from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_SPACE, K_h
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from atari_style.core.gl.renderer import GLRenderer
from atari_style.core.gl.uniforms import ShaderUniforms
from atari_style.core.gl.composites import COMPOSITES, CompositeConfig


@dataclass
class ControllerState:
    """Current state of the shader controller."""
    composite_name: str = 'plasma_lissajous'
    params: List[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 0.5])
    color_mode: int = 0
    time_val: float = 0.0
    paused: bool = False
    show_hud: bool = True
    preset_slot: int = 0
    presets: List[Optional[List[float]]] = field(default_factory=lambda: [None] * 4)


class ShaderController:
    """Interactive joystick controller for GPU shaders.

    Renders GPU shaders to a pygame window and allows real-time
    parameter control via joystick.
    """

    def __init__(self, width: int = 800, height: int = 600,
                 composite_name: str = 'plasma_lissajous'):
        """Initialize the shader controller.

        Args:
            width: Window width
            height: Window height
            composite_name: Starting composite name
        """
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame required: pip install pygame")
        if not PIL_AVAILABLE:
            raise ImportError("Pillow required: pip install Pillow")

        self.width = width
        self.height = height
        self.running = True

        # Controller state
        self.state = ControllerState(composite_name=composite_name)
        self._load_defaults()

        # Joystick state
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.prev_buttons = {}
        self.prev_hat = (0, 0)  # Track previous hat state for debouncing

        # Composite list for cycling
        self.composite_names = list(COMPOSITES.keys())
        self.composite_index = self.composite_names.index(composite_name)

        # GL renderer (headless - we'll blit to pygame)
        self.gl_renderer: Optional[GLRenderer] = None
        self.current_program = None

        # Presets file
        self.presets_file = os.path.expanduser('~/.atari-style/shader_presets.json')
        self._load_presets()

    def _load_defaults(self):
        """Load default params from composite config.
        
        Resets parameters to the composite's default values and color mode.
        """
        config = COMPOSITES[self.state.composite_name]
        self.state.params = list(config.default_params)
        self.state.color_mode = config.default_color_mode

    def _load_presets(self):
        """Load saved presets from file.
        
        Attempts to load presets from ~/.atari-style/shader_presets.json.
        Silently fails if file doesn't exist or is corrupted.
        """
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r') as f:
                    data = json.load(f)
                    self.state.presets = data.get('presets', [None] * 4)
        except Exception:
            pass

    def _save_presets(self):
        """Save presets to file.
        
        Saves current presets to ~/.atari-style/shader_presets.json,
        creating the directory if it doesn't exist.
        """
        try:
            os.makedirs(os.path.dirname(self.presets_file), exist_ok=True)
            with open(self.presets_file, 'w') as f:
                json.dump({'presets': self.state.presets}, f)
        except Exception:
            pass

    def _init_pygame(self):
        """Initialize pygame window and joystick.
        
        Sets up the pygame display, initializes connected joystick (if any),
        and loads fonts for HUD rendering.
        """
        pygame.init()
        pygame.joystick.init()

        # Create window
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(f'Shader Controller - {self.state.composite_name}')

        # Initialize joystick
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick: {self.joystick.get_name()}")

            # Init button state
            for i in range(self.joystick.get_numbuttons()):
                self.prev_buttons[i] = False
        else:
            print("No joystick detected. Using keyboard only.")

        # Font for HUD
        pygame.font.init()
        self.font = pygame.font.SysFont('monospace', 16)
        self.font_large = pygame.font.SysFont('monospace', 24)

    def _init_gl(self):
        """Initialize GL renderer and load shader.
        
        Raises:
            RuntimeError: If GL initialization or shader loading fails
        """
        try:
            self.gl_renderer = GLRenderer(self.width, self.height, headless=True)
            self._load_shader()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize GL renderer: {e}") from e

    def _load_shader(self):
        """Load current composite shader.
        
        Loads the shader program for the currently selected composite
        and updates the window caption.
        """
        config = COMPOSITES[self.state.composite_name]
        self.current_program = self.gl_renderer.load_shader(config.shader_path)
        pygame.display.set_caption(f'Shader Controller - {self.state.composite_name}')

    def _get_joystick_axes(self) -> Tuple[float, float, float, float]:
        """Get all joystick axes normalized to 0-1 range.
        
        Returns:
            Tuple of (left_x, left_y, right_x, right_y) in range [0, 1]
        """
        if not self.joystick:
            return (0.5, 0.5, 0.5, 0.5)

        pygame.event.pump()

        # Get raw axis values (-1 to 1)
        num_axes = self.joystick.get_numaxes()

        # Left stick
        lx = self.joystick.get_axis(0) if num_axes > 0 else 0
        ly = self.joystick.get_axis(1) if num_axes > 1 else 0

        # Right stick (axis 2,3) or fallback to axis 4,5 for some controllers
        if num_axes >= 4:
            rx = self.joystick.get_axis(2)
            ry = self.joystick.get_axis(3)
        elif num_axes >= 6:
            rx = self.joystick.get_axis(4)
            ry = self.joystick.get_axis(5)
        else:
            rx, ry = 0, 0

        # Apply deadzone
        deadzone = 0.15
        lx = lx if abs(lx) > deadzone else 0
        ly = ly if abs(ly) > deadzone else 0
        rx = rx if abs(rx) > deadzone else 0
        ry = ry if abs(ry) > deadzone else 0

        # Normalize to 0-1 range (with center at 0.5)
        return (
            (lx + 1) / 2,  # 0-1
            (ly + 1) / 2,
            (rx + 1) / 2,
            (ry + 1) / 2,
        )

    def _check_button_press(self, button: int) -> bool:
        """Check if button was just pressed (rising edge).
        
        Args:
            button: Button index to check
            
        Returns:
            True if button was just pressed, False otherwise
        """
        if not self.joystick:
            return False

        current = self.joystick.get_button(button)
        prev = self.prev_buttons.get(button, False)

        return current and not prev

    def _update_button_state(self):
        """Update previous button states for edge detection."""
        if not self.joystick:
            return

        for i in range(self.joystick.get_numbuttons()):
            self.prev_buttons[i] = self.joystick.get_button(i)

    def _handle_input(self):
        """Handle pygame events and joystick input.
        
        Processes keyboard events, joystick buttons, and D-pad input.
        """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_SPACE:
                    self.state.paused = not self.state.paused
                elif event.key == K_h:
                    self.state.show_hud = not self.state.show_hud
                elif event.key == pygame.K_c:
                    # Cycle color mode
                    self.state.color_mode = (self.state.color_mode + 1) % 4
                elif event.key == pygame.K_r:
                    # Reset to defaults
                    self._load_defaults()
                elif event.key == pygame.K_LEFT:
                    # Previous composite
                    self.composite_index = (self.composite_index - 1) % len(self.composite_names)
                    self.state.composite_name = self.composite_names[self.composite_index]
                    self._load_defaults()
                    self._load_shader()
                elif event.key == pygame.K_RIGHT:
                    # Next composite
                    self.composite_index = (self.composite_index + 1) % len(self.composite_names)
                    self.state.composite_name = self.composite_names[self.composite_index]
                    self._load_defaults()
                    self._load_shader()

        # Joystick buttons
        if self.joystick:
            pygame.event.pump()

            # Button 0 (A): Cycle color mode
            if self._check_button_press(0):
                self.state.color_mode = (self.state.color_mode + 1) % 4

            # Button 1 (B): Save preset
            if self._check_button_press(1):
                self.state.presets[self.state.preset_slot] = list(self.state.params)
                self._save_presets()
                print(f"Saved to slot {self.state.preset_slot}")

            # Button 2 (X): Load preset
            if self._check_button_press(2):
                if self.state.presets[self.state.preset_slot]:
                    self.state.params = list(self.state.presets[self.state.preset_slot])
                    print(f"Loaded from slot {self.state.preset_slot}")

            # Button 3 (Y): Reset to defaults
            if self._check_button_press(3):
                self._load_defaults()

            # Button 4/5 (LB/RB): Cycle preset slot
            if self._check_button_press(4):
                self.state.preset_slot = (self.state.preset_slot - 1) % 4
            if self._check_button_press(5):
                self.state.preset_slot = (self.state.preset_slot + 1) % 4

            # Button 6 (Back): Toggle HUD
            if self._check_button_press(6):
                self.state.show_hud = not self.state.show_hud

            # Button 7 (Start): Pause
            if self._check_button_press(7):
                self.state.paused = not self.state.paused

            # D-Pad for composite switching (hat) - with debouncing
            if self.joystick.get_numhats() > 0:
                hat = self.joystick.get_hat(0)
                # Only trigger on rising edge (not pressed -> pressed)
                if hat[0] < 0 and self.prev_hat[0] >= 0:  # Left
                    self.composite_index = (self.composite_index - 1) % len(self.composite_names)
                    self.state.composite_name = self.composite_names[self.composite_index]
                    self._load_defaults()
                    self._load_shader()
                elif hat[0] > 0 and self.prev_hat[0] <= 0:  # Right
                    self.composite_index = (self.composite_index + 1) % len(self.composite_names)
                    self.state.composite_name = self.composite_names[self.composite_index]
                    self._load_defaults()
                    self._load_shader()
                self.prev_hat = hat

            self._update_button_state()

    def _update_params_from_joystick(self):
        """Update shader params from joystick position.
        
        Maps joystick axes to shader parameter ranges based on
        the current composite's configuration.
        """
        if not self.joystick:
            return

        axes = self._get_joystick_axes()

        # Get param ranges from config
        config = COMPOSITES[self.state.composite_name]
        ranges = config.param_ranges

        # Map normalized joystick (0-1) to param range
        for i, (norm_val, (min_val, max_val)) in enumerate(zip(axes, ranges)):
            self.state.params[i] = min_val + norm_val * (max_val - min_val)

    def _render_frame(self) -> pygame.Surface:
        """Render shader to pygame surface.
        
        Returns:
            pygame.Surface containing the rendered frame
        """
        config = COMPOSITES[self.state.composite_name]

        # Set up uniforms
        uniforms = ShaderUniforms()
        uniforms.set_resolution(self.width, self.height)
        uniforms.iTime = self.state.time_val
        uniforms.iParams = tuple(self.state.params)
        uniforms.iColorMode = self.state.color_mode

        # Render to numpy array
        arr = self.gl_renderer.render_to_array(self.current_program, uniforms.to_dict())

        # Convert RGBA to pygame surface
        # Need to flip vertically and convert to RGB
        arr = np.flipud(arr)
        arr_rgb = arr[:, :, :3]  # Drop alpha

        surface = pygame.surfarray.make_surface(arr_rgb.swapaxes(0, 1))
        return surface

    def _draw_hud(self):
        """Draw HUD overlay.
        
        Displays current parameters, color mode, preset slot,
        and control hints on screen.
        """
        if not self.state.show_hud:
            return

        config = COMPOSITES[self.state.composite_name]

        # Background for HUD
        hud_surface = pygame.Surface((300, 200), pygame.SRCALPHA)
        hud_surface.fill((0, 0, 0, 180))

        # Title
        title = self.font_large.render(config.name, True, (255, 255, 255))
        hud_surface.blit(title, (10, 5))

        # Parameters
        y = 35
        for i, (name, value) in enumerate(zip(config.param_names, self.state.params)):
            text = f"{name}: {value:.3f}"
            label = self.font.render(text, True, (200, 255, 200))
            hud_surface.blit(label, (10, y))
            y += 20

        # Color mode
        color_names = ['Aurora', 'Fire', 'Electric', 'Grayscale']
        color_text = f"Color: {color_names[self.state.color_mode]}"
        color_label = self.font.render(color_text, True, (255, 200, 100))
        hud_surface.blit(color_label, (10, y))
        y += 20

        # Preset slot
        preset_text = f"Preset: {self.state.preset_slot} {'[saved]' if self.state.presets[self.state.preset_slot] else '[empty]'}"
        preset_label = self.font.render(preset_text, True, (100, 200, 255))
        hud_surface.blit(preset_label, (10, y))
        y += 20

        # Paused indicator
        if self.state.paused:
            paused_label = self.font.render("PAUSED", True, (255, 100, 100))
            hud_surface.blit(paused_label, (10, y))

        # Controls hint at bottom
        controls_surface = pygame.Surface((self.width, 30), pygame.SRCALPHA)
        controls_surface.fill((0, 0, 0, 150))
        controls = "A:Color  B:Save  X:Load  Y:Reset  LB/RB:Slot  D-Pad:Composite  H:HUD"
        controls_label = self.font.render(controls, True, (150, 150, 150))
        controls_surface.blit(controls_label, (10, 5))

        self.screen.blit(hud_surface, (10, 10))
        self.screen.blit(controls_surface, (0, self.height - 30))

    def run(self):
        """Main loop.
        
        Initializes pygame and GL, then enters the main render loop
        handling input, updating parameters, and rendering frames.
        """
        try:
            self._init_pygame()
            self._init_gl()

            clock = pygame.time.Clock()
            last_time = time.time()

            print("\nShader Controller Started!")
            print("Controls:")
            print("  Left Stick: Params 0-1")
            print("  Right Stick: Params 2-3")
            print("  A: Cycle color mode")
            print("  B: Save preset")
            print("  X: Load preset")
            print("  Y: Reset to defaults")
            print("  D-Pad: Switch composite")
            print("  H: Toggle HUD")
            print("  ESC: Exit\n")

            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                # Handle input
                self._handle_input()

                # Update params from joystick
                self._update_params_from_joystick()

                # Update time
                if not self.state.paused:
                    self.state.time_val += dt

                # Render shader
                shader_surface = self._render_frame()
                self.screen.blit(shader_surface, (0, 0))

                # Draw HUD
                self._draw_hud()

                # Update display
                pygame.display.flip()

                # Cap at 60 FPS
                clock.tick(60)

        finally:
            if self.gl_renderer:
                self.gl_renderer.release()
            pygame.quit()


def run_shader_controller(composite: str = 'plasma_lissajous',
                          width: int = 800, height: int = 600):
    """Entry point for shader controller.

    Args:
        composite: Starting composite name
        width: Window width
        height: Window height
    """
    controller = ShaderController(width, height, composite)
    controller.run()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Interactive joystick controller for GPU shaders'
    )
    parser.add_argument('--composite', '-c',
                        choices=list(COMPOSITES.keys()),
                        default='plasma_lissajous',
                        help='Starting composite')
    parser.add_argument('--width', '-W', type=int, default=800)
    parser.add_argument('--height', '-H', type=int, default=600)
    parser.add_argument('--fullscreen', '-f', action='store_true',
                        help='Run in fullscreen mode')
    args = parser.parse_args()

    if args.fullscreen:
        # Get display info for fullscreen
        pygame.init()
        info = pygame.display.Info()
        args.width = info.current_w
        args.height = info.current_h
        pygame.quit()

    run_shader_controller(args.composite, args.width, args.height)


if __name__ == '__main__':
    main()
