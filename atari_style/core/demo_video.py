#!/usr/bin/env python3
"""Terminal demo video export CLI.

Renders terminal-based demos to video using scripted input and
headless rendering.

Usage:
    python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json -o output.mp4
    python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json --preview

Supported demos:
    joystick_test - Joystick verification interface
    (more to be added)
"""

import os
import sys
import argparse
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

from .scripted_input import ScriptedInputHandler, InputScript
from .headless_renderer import HeadlessRenderer, HeadlessRendererFactory


# Registry of demos that support video export
DEMO_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_demo(name: str, factory: Callable, description: str = ""):
    """Register a demo for video export.

    Args:
        name: Demo identifier (used in CLI)
        factory: Function(renderer, input_handler) -> demo instance
        description: Human-readable description
    """
    DEMO_REGISTRY[name] = {
        'factory': factory,
        'description': description,
    }


class JoystickTestDemo:
    """Headless-compatible joystick test demo."""

    def __init__(self, renderer: HeadlessRenderer, input_handler: ScriptedInputHandler):
        self.renderer = renderer
        self.input_handler = input_handler

    def draw_crosshair(self, cx: int, cy: int, x: float, y: float):
        """Draw joystick position crosshair."""
        # Draw center reference
        self.renderer.draw_text(cx - 1, cy, '┼', 'yellow')

        # Draw axes
        for i in range(-20, 21):
            if 0 <= cx + i < self.renderer.width:
                self.renderer.set_pixel(cx + i, cy, '─', 'cyan')
            if 0 <= cy + i // 2 < self.renderer.height:
                self.renderer.set_pixel(cx, cy + i // 2, '│', 'cyan')

        # Draw current position
        pos_x = int(cx + x * 20)
        pos_y = int(cy + y * 10)
        if 0 <= pos_x < self.renderer.width and 0 <= pos_y < self.renderer.height:
            self.renderer.set_pixel(pos_x, pos_y, '●', 'bright_green')

            # Draw line from center to position
            steps = 20
            for i in range(steps):
                t = i / steps
                lx = int(cx + x * 20 * t)
                ly = int(cy + y * 10 * t)
                if 0 <= lx < self.renderer.width and 0 <= ly < self.renderer.height:
                    self.renderer.set_pixel(lx, ly, '·', 'green')

    def draw_button_indicator(self, x: int, y: int, button_num: int, pressed: bool):
        """Draw a button state indicator."""
        color = 'bright_green' if pressed else 'white'
        char = '█' if pressed else '□'
        self.renderer.draw_text(x, y, f"BTN {button_num}: {char}", color)

    def draw(self):
        """Render the joystick test interface."""
        self.renderer.clear_buffer()

        # Draw title
        title = "JOYSTICK VERIFICATION"
        self.renderer.draw_text((self.renderer.width - len(title)) // 2, 2, title, 'bright_cyan')

        # Get joystick info
        info = self.input_handler.verify_joystick()

        # Connection status
        status = f"CONNECTED: {info['name']}"
        self.renderer.draw_text((self.renderer.width - len(status)) // 2, 4, status, 'bright_green')

        # Draw joystick state
        cx = self.renderer.width // 2
        cy = self.renderer.height // 2

        # Get current axis values
        x, y = self.input_handler.get_joystick_state()

        # Draw crosshair
        self.draw_crosshair(cx, cy, x, y)

        # Draw axis values
        self.renderer.draw_text(5, 8, f"X Axis: {x:+.2f}", 'yellow')
        self.renderer.draw_text(5, 9, f"Y Axis: {y:+.2f}", 'yellow')

        # Draw button states (Hyperkin Trooper V2 has 6 buttons)
        buttons = self.input_handler.get_joystick_buttons()
        button_y = 11
        for i in range(6):  # Only 6 buttons on Hyperkin Trooper V2
            self.draw_button_indicator(5, button_y + i, i, buttons.get(i, False))

        # Draw info
        self.renderer.draw_text(5, 6, f"Axes: {info['axes']}", 'cyan')
        self.renderer.draw_text(5, 7, f"Buttons: 6", 'cyan')  # Hyperkin has 6 buttons

        # Draw visual button panel on right - Hyperkin Trooper V2 layout
        if buttons:
            panel_x = self.renderer.width - 28
            panel_y = 8
            self.renderer.draw_text(panel_x, panel_y, "BUTTON PANEL", 'magenta')
            self.renderer.draw_text(panel_x, panel_y + 1, "(Hyperkin Trooper V2)", 'cyan')

            # Face buttons (0, 1) - circles ● ○
            self.renderer.draw_text(panel_x, panel_y + 3, "Face:", 'yellow')
            for i in range(2):
                pressed = buttons.get(i, False)
                color = 'bright_green' if pressed else 'white'
                char = '●' if pressed else '○'  # Circle buttons
                self.renderer.draw_text(panel_x + 6 + i * 4, panel_y + 3, f"{i}:{char}", color)

            # Shoulder buttons (2, 3, 4, 5) - rectangles ■ □
            # Front pair (2, 3)
            self.renderer.draw_text(panel_x, panel_y + 5, "Front:", 'yellow')
            for idx, i in enumerate([2, 3]):
                pressed = buttons.get(i, False)
                color = 'bright_green' if pressed else 'white'
                char = '■' if pressed else '□'  # Rectangle buttons
                self.renderer.draw_text(panel_x + 7 + idx * 4, panel_y + 5, f"{i}:{char}", color)

            # Rear pair (4, 5)
            self.renderer.draw_text(panel_x, panel_y + 7, "Rear:", 'yellow')
            for idx, i in enumerate([4, 5]):
                pressed = buttons.get(i, False)
                color = 'bright_green' if pressed else 'white'
                char = '■' if pressed else '□'  # Rectangle buttons
                self.renderer.draw_text(panel_x + 7 + idx * 4, panel_y + 7, f"{i}:{char}", color)

        # Draw instructions
        instructions = [
            "Move joystick to test axes",
            "Press ALL buttons to test",
            "Demo video - scripted input"
        ]
        for i, text in enumerate(instructions):
            self.renderer.draw_text((self.renderer.width - len(text)) // 2,
                                    self.renderer.height - 5 + i, text, 'cyan')


def create_joystick_test(renderer: HeadlessRenderer, input_handler: ScriptedInputHandler):
    """Factory for JoystickTestDemo."""
    return JoystickTestDemo(renderer, input_handler)


# Register built-in demos
register_demo('joystick_test', create_joystick_test, 'Joystick verification interface')


class StarfieldDemo:
    """Headless-compatible starfield demo.

    Renders a starfield animation in the terminal using headless rendering,
    suitable for automated demo video export. Supports multiple visual modes,
    color schemes, hyperspace jumps, and scripted input for video generation.
    """

    MODE_STARS = 0
    MODE_ASTEROIDS = 1

    # Hyperspace states
    HS_NONE = 0
    HS_PAUSE = 1
    HS_FLASH = 2
    HS_BURST = 3
    HS_RESUME = 4

    def __init__(self, renderer: HeadlessRenderer, input_handler: ScriptedInputHandler):
        self.renderer = renderer
        self.input_handler = input_handler
        import random
        self.random = random

        # Animation state
        self.base_speed = 2.0
        self.warp_speed = 1.0
        self.lateral_drift = 0.0
        self.color_mode = 0  # 0=white, 1=rainbow, 2=speed
        self.mode = self.MODE_STARS
        self.nebulae_visible = True  # Match original default
        self.time = 0

        # Button debounce tracking
        self.last_button_time = {0: 0, 1: 0, 2: 0, 3: 0}

        # Hyperspace state
        self.hyperspace_state = self.HS_NONE
        self.hyperspace_timer = 0

        # Stars: list of (x, y, z, layer)
        self.stars = []
        self._init_stars()

    def _init_stars(self):
        """Initialize star field."""
        width = self.renderer.width
        height = self.renderer.height
        for _ in range(150):
            layer = self.random.randint(0, 2)
            self.stars.append({
                'x': self.random.uniform(-width, width),
                'y': self.random.uniform(-height, height),
                'z': self.random.uniform(1, width),
                'layer': layer
            })

    def draw(self):
        """Render the starfield."""
        self.renderer.clear_buffer()
        width = self.renderer.width
        height = self.renderer.height

        # Get input state for speed/drift
        jx, jy = self.input_handler.get_joystick_state()
        buttons = self.input_handler.get_joystick_buttons()

        # Update speed from joystick Y
        if abs(jy) > 0.1:
            self.warp_speed = max(0.1, min(5.0, self.warp_speed - jy * 0.1))

        # Update drift from joystick X
        self.lateral_drift = jx * 10 if abs(jx) > 0.1 else self.lateral_drift * 0.9

        # Button handlers with proper debounce
        debounce_time = 0.3
        if buttons.get(0) and self.time - self.last_button_time[0] > debounce_time:
            self.color_mode = (self.color_mode + 1) % 3
            self.last_button_time[0] = self.time
        if buttons.get(1) and self.time - self.last_button_time[1] > debounce_time:
            self.mode = self.MODE_ASTEROIDS if self.mode == self.MODE_STARS else self.MODE_STARS
            self.last_button_time[1] = self.time
        if buttons.get(2) and self.time - self.last_button_time[2] > debounce_time:
            self.nebulae_visible = not self.nebulae_visible
            self.last_button_time[2] = self.time
        if buttons.get(3) and self.time - self.last_button_time[3] > debounce_time:
            # Trigger hyperspace jump
            if self.hyperspace_state == self.HS_NONE:
                self.hyperspace_state = self.HS_PAUSE
                self.hyperspace_timer = 0
            self.last_button_time[3] = self.time

        # Calculate current speed
        speed = self.base_speed * self.warp_speed

        # Draw title
        title = "STARFIELD"
        mode_text = "ASTEROIDS" if self.mode == self.MODE_ASTEROIDS else "STARS"
        self.renderer.draw_text((width - len(title)) // 2, 1, title, 'bright_cyan')
        self.renderer.draw_text(2, 1, f"Mode: {mode_text}", 'yellow')
        self.renderer.draw_text(width - 15, 1, f"Speed: {self.warp_speed:.1f}x", 'green')

        # Color mode names
        color_names = ['WHITE', 'RAINBOW', 'SPEED']
        self.renderer.draw_text(2, 2, f"Colors: {color_names[self.color_mode]}", 'cyan')

        if self.nebulae_visible:
            self.renderer.draw_text(width - 12, 2, "NEBULAE ON", 'magenta')

        # Update hyperspace state machine
        if self.hyperspace_state != self.HS_NONE:
            self.hyperspace_timer += 1/30
            if self.hyperspace_state == self.HS_PAUSE and self.hyperspace_timer > 0.5:
                self.hyperspace_state = self.HS_FLASH
                self.hyperspace_timer = 0
            elif self.hyperspace_state == self.HS_FLASH and self.hyperspace_timer > 0.2:
                self.hyperspace_state = self.HS_BURST
                self.hyperspace_timer = 0
            elif self.hyperspace_state == self.HS_BURST and self.hyperspace_timer > 0.5:
                self.hyperspace_state = self.HS_RESUME
                self.hyperspace_timer = 0
            elif self.hyperspace_state == self.HS_RESUME and self.hyperspace_timer > 0.3:
                self.hyperspace_state = self.HS_NONE
                self.hyperspace_timer = 0

        # Update and draw stars
        layer_speeds = [0.3, 0.7, 1.0]
        layer_colors = ['blue', 'white', 'bright_white']
        star_chars = '.·*'
        asteroid_chars = '◊◇◆⬖⬗'  # Full asteroid character set
        chars = star_chars if self.mode == self.MODE_STARS else asteroid_chars

        for star in self.stars:
            # Update position
            layer_speed = layer_speeds[star['layer']]
            star['z'] -= speed * layer_speed * 0.5
            star['x'] += self.lateral_drift * layer_speed * 0.1

            # Respawn if behind camera
            if star['z'] <= 0:
                star['x'] = self.random.uniform(-width, width)
                star['y'] = self.random.uniform(-height, height)
                star['z'] = width

            # Project to 2D (k=128 matches original implementation)
            if star['z'] > 0:
                k = 128 / star['z']
                sx = int(star['x'] * k + width / 2)
                sy = int(star['y'] * k * 0.5 + height / 2)

                # Hyperspace burst: push stars outward from center
                if self.hyperspace_state == self.HS_BURST:
                    cx, cy = width / 2, height / 2
                    dx, dy = sx - cx, sy - cy
                    dist = (dx**2 + dy**2)**0.5
                    if dist > 0:
                        burst_factor = 1 + self.hyperspace_timer * 3
                        sx = int(cx + dx * burst_factor)
                        sy = int(cy + dy * burst_factor)

                if 0 <= sx < width and 3 <= sy < height - 1:
                    # Choose color
                    if self.hyperspace_state == self.HS_FLASH:
                        color = 'bright_white'
                    elif self.color_mode == 0:
                        color = layer_colors[star['layer']]
                    elif self.color_mode == 1:
                        colors = ['red', 'yellow', 'green', 'cyan', 'blue', 'magenta']
                        color = colors[int(self.time * 2 + star['z']) % len(colors)]
                    else:
                        color = 'bright_white' if speed > 3 else 'white' if speed > 1.5 else 'cyan'

                    # Pick char based on layer, handling different char set lengths
                    char_idx = star['layer'] % len(chars)
                    char = chars[char_idx]
                    self.renderer.set_pixel(sx, sy, char, color)

        # Draw simple nebula effect
        if self.nebulae_visible and self.hyperspace_state == self.HS_NONE:
            for i in range(5):
                nx = int(width * 0.2 + i * width * 0.15 + self.time * 2) % width
                ny = int(height * 0.4 + i * 3) % height
                if 3 <= ny < height - 1:
                    self.renderer.set_pixel(nx, ny, '░', 'magenta')
                    self.renderer.set_pixel((nx + 1) % width, ny, '░', 'blue')

        # Hyperspace status display
        if self.hyperspace_state != self.HS_NONE:
            hs_text = ["", "CHARGING...", "JUMP!", "HYPERSPACE!", "EMERGING..."][self.hyperspace_state]
            self.renderer.draw_text((width - len(hs_text)) // 2, height // 2, hs_text, 'bright_cyan')

        # Increment time
        self.time += 1/30


def create_starfield(renderer: HeadlessRenderer, input_handler: ScriptedInputHandler):
    """Factory for StarfieldDemo."""
    return StarfieldDemo(renderer, input_handler)


register_demo('starfield', create_starfield, 'Enhanced 3D starfield with parallax')


class PlatonicSolidsDemo:
    """Headless-compatible platonic solids demo.

    Renders and animates the five platonic solids (Tetrahedron, Cube, Octahedron,
    Dodecahedron, Icosahedron) in a headless environment for video export.
    This class is a headless-compatible version of the interactive platonic solids demo,
    designed for scripted input and non-interactive rendering.
    """

    # Solid names list (data initialized in __init__)
    SOLID_NAMES = ['Tetrahedron', 'Cube', 'Octahedron', 'Dodecahedron', 'Icosahedron']

    @staticmethod
    def _dodeca_vertices():
        """Generate dodecahedron vertices matching original implementation."""
        phi = (1 + 5**0.5) / 2
        return [
            # Cube vertices scaled by phi
            (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
            (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1),
            # Golden rectangles in xy plane
            (0, phi, 1/phi), (0, phi, -1/phi), (0, -phi, 1/phi), (0, -phi, -1/phi),
            # Golden rectangles in xz plane
            (1/phi, 0, phi), (1/phi, 0, -phi), (-1/phi, 0, phi), (-1/phi, 0, -phi),
            # Golden rectangles in yz plane
            (phi, 1/phi, 0), (phi, -1/phi, 0), (-phi, 1/phi, 0), (-phi, -1/phi, 0)
        ]

    @staticmethod
    def _dodeca_edges():
        """Generate dodecahedron edges matching original implementation."""
        return [
            (0, 8), (0, 12), (0, 16), (1, 9), (1, 13), (1, 16),
            (2, 10), (2, 12), (2, 17), (3, 11), (3, 13), (3, 17),
            (4, 8), (4, 14), (4, 18), (5, 9), (5, 15), (5, 18),
            (6, 10), (6, 14), (6, 19), (7, 11), (7, 15), (7, 19),
            (8, 9), (10, 11), (12, 14), (13, 15), (16, 17), (18, 19)
        ]

    @staticmethod
    def _icosa_vertices():
        """Generate icosahedron vertices matching original implementation."""
        return [
            # Top vertex
            (0, 1, 0),
            # Upper pentagon
            (0.894, 0.447, 0), (0.276, 0.447, 0.851),
            (-0.724, 0.447, 0.526), (-0.724, 0.447, -0.526), (0.276, 0.447, -0.851),
            # Lower pentagon
            (0.724, -0.447, 0.526), (0.724, -0.447, -0.526),
            (-0.276, -0.447, -0.851), (-0.894, -0.447, 0), (-0.276, -0.447, 0.851),
            # Bottom vertex
            (0, -1, 0)
        ]

    @staticmethod
    def _icosa_edges():
        """Generate icosahedron edges matching original implementation."""
        return [
            # Top vertex to upper pentagon
            (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
            # Upper pentagon
            (1, 2), (2, 3), (3, 4), (4, 5), (5, 1),
            # Upper to lower
            (1, 6), (1, 7), (2, 6), (2, 10), (3, 10), (3, 9),
            (4, 9), (4, 8), (5, 8), (5, 7),
            # Lower pentagon
            (6, 7), (7, 8), (8, 9), (9, 10), (10, 6),
            # Lower pentagon to bottom
            (6, 11), (7, 11), (8, 11), (9, 11), (10, 11)
        ]

    def __init__(self, renderer: HeadlessRenderer, input_handler: ScriptedInputHandler):
        self.renderer = renderer
        self.input_handler = input_handler
        import math
        self.math = math

        # Build solids data (must be done in __init__ to call static methods)
        self.solids = {
            'Tetrahedron': {
                # Vertices match original implementation
                'vertices': [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)],
                'edges': [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
                'faces': 4, 'v': 4, 'e': 6
            },
            'Cube': {
                'vertices': [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
                'edges': [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
                         (0, 4), (1, 5), (2, 6), (3, 7)],
                'faces': 6, 'v': 8, 'e': 12
            },
            'Octahedron': {
                'vertices': [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
                'edges': [(0, 2), (0, 3), (0, 4), (0, 5), (1, 2), (1, 3), (1, 4), (1, 5),
                         (2, 4), (2, 5), (3, 4), (3, 5)],
                'faces': 8, 'v': 6, 'e': 12
            },
            'Dodecahedron': {
                'vertices': PlatonicSolidsDemo._dodeca_vertices(),
                'edges': PlatonicSolidsDemo._dodeca_edges(),
                'faces': 12, 'v': 20, 'e': 30
            },
            'Icosahedron': {
                'vertices': PlatonicSolidsDemo._icosa_vertices(),
                'edges': PlatonicSolidsDemo._icosa_edges(),
                'faces': 20, 'v': 12, 'e': 30
            }
        }

        self.solid_names = self.SOLID_NAMES
        self.current_index = 0
        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 0
        self.auto_rotate = True
        self.zoom = 15  # Match original implementation
        self.last_button_time = 0
        self.time = 0

    def _rotate_point(self, p, rx, ry, rz):
        """Rotate a 3D point."""
        x, y, z = p
        # Rotate X
        cos_rx, sin_rx = self.math.cos(rx), self.math.sin(rx)
        y, z = y * cos_rx - z * sin_rx, y * sin_rx + z * cos_rx
        # Rotate Y
        cos_ry, sin_ry = self.math.cos(ry), self.math.sin(ry)
        x, z = x * cos_ry + z * sin_ry, -x * sin_ry + z * cos_ry
        # Rotate Z
        cos_rz, sin_rz = self.math.cos(rz), self.math.sin(rz)
        x, y = x * cos_rz - y * sin_rz, x * sin_rz + y * cos_rz
        return (x, y, z)

    def _project(self, p, width, height):
        """Project 3D to 2D."""
        x, y, z = p
        # fov=200, distance=5 matches original implementation
        factor = 200 / (z + 5)
        sx = int(x * factor * self.zoom + width / 2)
        sy = int(y * factor * self.zoom * 0.5 + height / 2)
        return sx, sy

    def draw(self):
        """Render the platonic solid."""
        self.renderer.clear_buffer()
        width = self.renderer.width
        height = self.renderer.height

        # Get input
        jx, jy = self.input_handler.get_joystick_state()
        buttons = self.input_handler.get_joystick_buttons()

        # Manual rotation
        if abs(jx) > 0.1 or abs(jy) > 0.1:
            self.auto_rotate = False
            self.rotation_y += jx * 0.05
            self.rotation_x += jy * 0.05
        elif self.auto_rotate:
            self.rotation_y += 0.02
            self.rotation_x += 0.01

        # Cycle solids with button 0
        if buttons.get(0) and self.time - self.last_button_time > 0.3:
            self.current_index = (self.current_index + 1) % len(self.solid_names)
            self.last_button_time = self.time

        solid_name = self.solid_names[self.current_index]

        # Get solid data from pre-computed dict
        solid = self.solids[solid_name]
        vertices = solid['vertices']
        edges = solid['edges']
        info = f"{solid['faces']} faces, {solid['v']} vertices, {solid['e']} edges"

        # Draw title and info
        self.renderer.draw_text((width - len(solid_name)) // 2, 1, solid_name.upper(), 'bright_cyan')
        self.renderer.draw_text((width - len(info)) // 2, 2, info, 'yellow')

        # Transform and project vertices
        projected = []
        for v in vertices:
            rv = self._rotate_point(v, self.rotation_x, self.rotation_y, self.rotation_z)
            projected.append(self._project(rv, width, height))

        # Draw edges
        for e in edges:
            if e[0] < len(projected) and e[1] < len(projected):
                x1, y1 = projected[e[0]]
                x2, y2 = projected[e[1]]
                self._draw_line(x1, y1, x2, y2, 'green')

        # Draw vertices
        for sx, sy in projected:
            if 0 <= sx < width and 0 <= sy < height:
                self.renderer.set_pixel(sx, sy, '●', 'bright_white')

        # Controls hint
        self.renderer.draw_text(2, height - 2, "BTN0: Next solid  Joystick: Rotate", 'cyan')

        self.time += 1/30

    def _draw_line(self, x1, y1, x2, y2, color):
        """Draw a line using Bresenham's algorithm."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= x1 < self.renderer.width and 0 <= y1 < self.renderer.height:
                # Choose line character based on direction (matches original)
                if abs(dx) > abs(dy):
                    char = '─'
                elif abs(dy) > abs(dx):
                    char = '│'
                elif (sx > 0 and sy > 0) or (sx < 0 and sy < 0):
                    char = '\\'
                else:
                    char = '/'
                self.renderer.set_pixel(x1, y1, char, color)

            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy


def create_platonic_solids(renderer: HeadlessRenderer, input_handler: ScriptedInputHandler):
    """Factory for PlatonicSolidsDemo."""
    return PlatonicSolidsDemo(renderer, input_handler)


register_demo('platonic_solids', create_platonic_solids, 'Interactive 3D Platonic solids viewer')


class DemoVideoExporter:
    """Exports terminal demos to video using scripted input."""

    # Default GIF settings for small file sizes
    DEFAULT_GIF_FPS = 15
    DEFAULT_GIF_MAX_WIDTH = 480

    def __init__(
        self,
        demo_name: str,
        script_path: str,
        output_path: str,
        width: int = 1920,
        height: int = 1080,
        char_columns: int = 100,
        char_rows: int = 40,
        gif_mode: bool = False,
        gif_fps: Optional[int] = None,
        gif_scale: Optional[int] = None,
    ):
        """Initialize exporter.

        Args:
            demo_name: Name of demo to render (from registry)
            script_path: Path to input script JSON
            output_path: Output video file path
            width: Output video width in pixels
            height: Output video height in pixels
            char_columns: Terminal columns
            char_rows: Terminal rows
            gif_mode: If True, export as GIF instead of MP4
            gif_fps: GIF frame rate (default: 15)
            gif_scale: GIF max width in pixels (default: 480)
        """
        if demo_name not in DEMO_REGISTRY:
            available = ', '.join(DEMO_REGISTRY.keys())
            raise ValueError(f"Unknown demo '{demo_name}'. Available: {available}")

        self.demo_name = demo_name
        self.script_path = script_path
        self.output_path = output_path
        self.gif_mode = gif_mode
        self.gif_fps = gif_fps or self.DEFAULT_GIF_FPS
        self.gif_scale = gif_scale or self.DEFAULT_GIF_MAX_WIDTH

        # Load script
        self.script = InputScript.from_file(script_path)

        # Create renderer with target resolution
        self.renderer = HeadlessRendererFactory.for_resolution(
            width, height, char_columns, char_rows
        )

        # Create scripted input handler
        self.input_handler = ScriptedInputHandler(script=self.script)

        # Create demo instance
        factory = DEMO_REGISTRY[demo_name]['factory']
        self.demo = factory(self.renderer, self.input_handler)

    def export(self, progress_callback: Optional[Callable[[int, int], None]] = None):
        """Export demo to video.

        Args:
            progress_callback: Optional callback(current_frame, total_frames)
        """
        total_frames = self.input_handler.get_frame_count()
        frame_time = 1.0 / self.script.fps

        # Create temp directory for frames
        temp_dir = tempfile.mkdtemp(prefix='atari_demo_')

        try:
            # Start script playback
            self.input_handler.start()

            # Render each frame
            for frame_num in range(total_frames):
                # Update input handler time
                self.input_handler.current_time = frame_num * frame_time

                # Render frame
                self.demo.draw()

                # Save frame
                frame_path = os.path.join(temp_dir, f'frame_{frame_num:05d}.png')
                self.renderer.save_frame(frame_path)

                if progress_callback:
                    progress_callback(frame_num + 1, total_frames)

            # Encode output with ffmpeg
            if self.gif_mode:
                self._encode_gif(temp_dir)
            else:
                self._encode_video(temp_dir)

        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _encode_video(self, frames_dir: str):
        """Encode frames to video using ffmpeg."""
        # Check for ffmpeg
        if not shutil.which('ffmpeg'):
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        frame_pattern = os.path.join(frames_dir, 'frame_%05d.png')

        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-framerate', str(self.script.fps),
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            self.output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    def _encode_gif(self, frames_dir: str):
        """Encode frames to GIF using ffmpeg two-pass palette approach.

        Uses palette generation for high-quality GIF output with small file sizes.
        """
        # Check for ffmpeg
        if not shutil.which('ffmpeg'):
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        frame_pattern = os.path.join(frames_dir, 'frame_%05d.png')
        palette_path = os.path.join(frames_dir, 'palette.png')

        # Build filter string for scaling and fps
        filters = f"fps={self.gif_fps},scale={self.gif_scale}:-1:flags=lanczos"

        # Pass 1: Generate optimized palette
        palette_cmd = [
            'ffmpeg',
            '-y',
            '-framerate', str(self.script.fps),
            '-i', frame_pattern,
            '-vf', f"{filters},palettegen=stats_mode=diff",
            palette_path
        ]

        result = subprocess.run(palette_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg palette generation failed: {result.stderr}")

        # Pass 2: Generate GIF using palette
        gif_cmd = [
            'ffmpeg',
            '-y',
            '-framerate', str(self.script.fps),
            '-i', frame_pattern,
            '-i', palette_path,
            '-lavfi', f"{filters}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
            self.output_path
        ]

        result = subprocess.run(gif_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg GIF encoding failed: {result.stderr}")

    def preview_frame(self, time: float) -> 'Image.Image':
        """Render a single frame at the given time.

        Args:
            time: Time in seconds

        Returns:
            PIL Image of the frame
        """
        self.input_handler.current_time = time
        self.demo.draw()
        return self.renderer.to_image()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Export terminal demos to video or GIF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s joystick_test scripts/demos/joystick-demo.json -o joystick-demo.mp4
  %(prog)s joystick_test scripts/demos/joystick-demo.json --gif -o demo.gif
  %(prog)s joystick_test scripts/demos/joystick-demo.json --gif --gif-fps 20 --gif-scale 640
  %(prog)s joystick_test scripts/demos/joystick-demo.json --preview
  %(prog)s --list

Available demos:
""" + '\n'.join(f"  {name}: {info['description']}" for name, info in DEMO_REGISTRY.items())
    )

    parser.add_argument('demo', nargs='?', help='Demo name to render')
    parser.add_argument('script', nargs='?', help='Path to input script JSON')
    parser.add_argument('-o', '--output', help='Output video file path')
    parser.add_argument('--width', type=int, default=1920, help='Output width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Output height (default: 1080)')
    parser.add_argument('--columns', type=int, default=100, help='Terminal columns (default: 100)')
    parser.add_argument('--rows', type=int, default=40, help='Terminal rows (default: 40)')
    parser.add_argument('--preview', action='store_true', help='Show preview of middle frame')
    parser.add_argument('--list', action='store_true', help='List available demos')

    # GIF export options
    parser.add_argument('--gif', action='store_true',
                        help='Export as GIF instead of MP4 (smaller, for docs/README)')
    parser.add_argument('--gif-fps', type=int, default=15,
                        help='GIF frame rate (default: 15)')
    parser.add_argument('--gif-scale', type=int, default=480,
                        help='GIF max width in pixels (default: 480)')

    args = parser.parse_args()

    if args.list:
        print("Available demos:")
        for name, info in DEMO_REGISTRY.items():
            print(f"  {name}: {info['description']}")
        return

    if not args.demo or not args.script:
        parser.error("demo and script arguments are required")

    # Determine output path
    output_path = args.output
    if not output_path:
        script_stem = Path(args.script).stem
        ext = '.gif' if args.gif else '.mp4'
        output_path = f"{args.demo}-{script_stem}{ext}"

    try:
        exporter = DemoVideoExporter(
            demo_name=args.demo,
            script_path=args.script,
            output_path=output_path,
            width=args.width,
            height=args.height,
            char_columns=args.columns,
            char_rows=args.rows,
            gif_mode=args.gif,
            gif_fps=args.gif_fps,
            gif_scale=args.gif_scale,
        )

        if args.preview:
            # Show preview of middle frame
            duration = exporter.script.duration
            img = exporter.preview_frame(duration / 2)
            preview_path = f"{args.demo}-preview.png"
            img.save(preview_path)
            print(f"Preview saved to: {preview_path}")
            return

        # Export with progress
        def show_progress(current, total):
            pct = current * 100 // total
            bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
            print(f"\rRendering: [{bar}] {pct}% ({current}/{total} frames)", end='', flush=True)

        output_type = "GIF" if args.gif else "video"
        print(f"Exporting {args.demo} demo as {output_type}...")
        print(f"Script: {args.script}")
        print(f"Output: {output_path}")
        print(f"Duration: {exporter.script.duration}s @ {exporter.script.fps}fps")
        if args.gif:
            print(f"GIF settings: {args.gif_fps}fps, max {args.gif_scale}px width")
        print()

        exporter.export(progress_callback=show_progress)

        print()
        print(f"✓ {output_type.capitalize()} exported to: {output_path}")

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
