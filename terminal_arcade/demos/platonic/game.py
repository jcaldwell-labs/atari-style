"""Platonic Solids 3D viewer with rotation and wireframe rendering."""

import time
import math
from ...engine.renderer import Renderer, Color
import signal
from ...engine.input_handler import InputHandler, InputType


class Vector3:
    """3D vector."""

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def rotate_x(self, angle):
        """Rotate around X axis."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        y = self.y * cos_a - self.z * sin_a
        z = self.y * sin_a + self.z * cos_a
        return Vector3(self.x, y, z)

    def rotate_y(self, angle):
        """Rotate around Y axis."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        x = self.x * cos_a + self.z * sin_a
        z = -self.x * sin_a + self.z * cos_a
        return Vector3(x, self.y, z)

    def rotate_z(self, angle):
        """Rotate around Z axis."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        x = self.x * cos_a - self.y * sin_a
        y = self.x * sin_a + self.y * cos_a
        return Vector3(x, y, self.z)

    def project(self, width, height, fov, distance):
        """Project 3D point to 2D screen coordinates."""
        factor = fov / (distance + self.z)
        x = self.x * factor + width / 2
        y = self.y * factor * 0.5 + height / 2  # Aspect ratio correction
        return int(x), int(y)


class PlatonicSolid:
    """Base class for Platonic solids."""

    def __init__(self, name, vertices, edges, faces, color):
        self.name = name
        self.vertices = [Vector3(v[0], v[1], v[2]) for v in vertices]
        self.edges = edges
        self.faces = faces
        self.color = color


# Define the five Platonic solids
def get_solids():
    """Get all five Platonic solids."""

    # Tetrahedron (4 vertices, 6 edges, 4 faces)
    tetrahedron = PlatonicSolid(
        "Tetrahedron",
        [
            (1, 1, 1),
            (1, -1, -1),
            (-1, 1, -1),
            (-1, -1, 1)
        ],
        [
            (0, 1), (0, 2), (0, 3),
            (1, 2), (1, 3), (2, 3)
        ],
        [
            (0, 1, 2),
            (0, 1, 3),
            (0, 2, 3),
            (1, 2, 3)
        ],
        Color.BRIGHT_RED
    )

    # Cube (8 vertices, 12 edges, 6 faces)
    cube = PlatonicSolid(
        "Cube",
        [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ],
        [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Back face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Front face
            (0, 4), (1, 5), (2, 6), (3, 7)   # Connecting edges
        ],
        [
            (0, 1, 2, 3),  # Back
            (4, 5, 6, 7),  # Front
            (0, 1, 5, 4),  # Bottom
            (2, 3, 7, 6),  # Top
            (0, 3, 7, 4),  # Left
            (1, 2, 6, 5)   # Right
        ],
        Color.BRIGHT_GREEN
    )

    # Octahedron (6 vertices, 12 edges, 8 faces)
    octahedron = PlatonicSolid(
        "Octahedron",
        [
            (1, 0, 0), (-1, 0, 0),
            (0, 1, 0), (0, -1, 0),
            (0, 0, 1), (0, 0, -1)
        ],
        [
            (0, 2), (0, 3), (0, 4), (0, 5),
            (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 4), (2, 5), (3, 4), (3, 5)
        ],
        [
            (0, 2, 4), (0, 2, 5), (0, 3, 4), (0, 3, 5),
            (1, 2, 4), (1, 2, 5), (1, 3, 4), (1, 3, 5)
        ],
        Color.BRIGHT_BLUE
    )

    # Dodecahedron (20 vertices, 30 edges, 12 faces)
    phi = (1 + math.sqrt(5)) / 2  # Golden ratio

    dodecahedron = PlatonicSolid(
        "Dodecahedron",
        [
            # Cube vertices scaled by phi
            (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
            (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1),
            # Golden rectangles in xy plane
            (0, phi, 1/phi), (0, phi, -1/phi), (0, -phi, 1/phi), (0, -phi, -1/phi),
            # Golden rectangles in xz plane
            (1/phi, 0, phi), (1/phi, 0, -phi), (-1/phi, 0, phi), (-1/phi, 0, -phi),
            # Golden rectangles in yz plane
            (phi, 1/phi, 0), (phi, -1/phi, 0), (-phi, 1/phi, 0), (-phi, -1/phi, 0)
        ],
        [
            # Generate edges (simplified - connecting nearby vertices)
            (0, 8), (0, 12), (0, 16), (1, 9), (1, 13), (1, 16),
            (2, 10), (2, 12), (2, 17), (3, 11), (3, 13), (3, 17),
            (4, 8), (4, 14), (4, 18), (5, 9), (5, 15), (5, 18),
            (6, 10), (6, 14), (6, 19), (7, 11), (7, 15), (7, 19),
            (8, 9), (10, 11), (12, 14), (13, 15), (16, 17), (18, 19)
        ],
        [
            # 12 pentagonal faces (simplified representation)
            (0, 8, 4, 14, 12),
            (0, 12, 2, 17, 16),
            (0, 16, 1, 9, 8),
        ],
        Color.BRIGHT_YELLOW
    )

    # Icosahedron (12 vertices, 30 edges, 20 faces)
    icosahedron = PlatonicSolid(
        "Icosahedron",
        [
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
        ],
        [
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
        ],
        [
            # 20 triangular faces
            (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5), (0, 5, 1),
        ],
        Color.BRIGHT_MAGENTA
    )

    return [tetrahedron, cube, octahedron, dodecahedron, icosahedron]


class PlatonicSolidsViewer:
    """Interactive 3D viewer for Platonic solids."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.width = self.renderer.width
        self.height = self.renderer.height

        # Solids
        self.solids = get_solids()
        self.current_solid_index = 0
        self.current_solid = self.solids[self.current_solid_index]

        # Rotation angles
        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 0

        # Rotation speeds
        self.rotation_speed_x = 0
        self.rotation_speed_y = 0.5  # Default slow rotation
        self.rotation_speed_z = 0

        # Auto-rotate
        self.auto_rotate = True

        # Zoom
        self.zoom = 15

        # Face fill
        self.show_faces = False

        # Camera
        self.fov = 200
        self.distance = 5

        # Frame timing
        self.last_time = time.time()

    def handle_input(self, dt):
        """Handle user input."""
        # Get joystick state
        jx, jy = self.input_handler.get_joystick_state()

        # Manual rotation with joystick
        if abs(jx) > 0 or abs(jy) > 0:
            self.auto_rotate = False
            self.rotation_y += jx * dt * 2
            self.rotation_x += jy * dt * 2
        else:
            # Keyboard rotation
            with self.input_handler.term.cbreak():
                key = self.input_handler.term.inkey(timeout=0.001)

                if key:
                    if key.name == 'KEY_LEFT' or key.lower() == 'a':
                        self.auto_rotate = False
                        self.rotation_y -= dt * 2
                    elif key.name == 'KEY_RIGHT' or key.lower() == 'd':
                        self.auto_rotate = False
                        self.rotation_y += dt * 2
                    elif key.name == 'KEY_UP' or key.lower() == 'w':
                        self.auto_rotate = False
                        self.rotation_x -= dt * 2
                    elif key.name == 'KEY_DOWN' or key.lower() == 's':
                        self.auto_rotate = False
                        self.rotation_x += dt * 2

                    # Z-axis rotation with Q/E
                    elif key.lower() == 'q':
                        self.auto_rotate = False
                        self.rotation_z -= dt * 2
                    elif key.lower() == 'e':
                        self.auto_rotate = False
                        self.rotation_z += dt * 2

                    # Cycle solids
                    elif key == ' ' or key.name == 'KEY_ENTER':
                        self.current_solid_index = (self.current_solid_index + 1) % len(self.solids)
                        self.current_solid = self.solids[self.current_solid_index]

                    # Toggle auto-rotate
                    elif key.lower() == 'r':
                        self.auto_rotate = not self.auto_rotate

                    # Toggle face fill
                    elif key.lower() == 'f':
                        self.show_faces = not self.show_faces

                    # Reset rotation
                    elif key.lower() == 'c':
                        self.rotation_x = 0
                        self.rotation_y = 0
                        self.rotation_z = 0

                    # Zoom
                    elif key == '+' or key == '=':
                        self.zoom = min(30, self.zoom + 1)
                    elif key == '-':
                        self.zoom = max(5, self.zoom - 1)

        # Check buttons for solid cycling
        buttons = self.input_handler.get_joystick_buttons()
        if buttons.get(0):  # Button 0
            # Debounce
            time.sleep(0.2)
            self.current_solid_index = (self.current_solid_index + 1) % len(self.solids)
            self.current_solid = self.solids[self.current_solid_index]

    def update(self, dt):
        """Update viewer state."""
        if self.auto_rotate:
            self.rotation_y += self.rotation_speed_y * dt
            self.rotation_x += self.rotation_speed_x * dt
            self.rotation_z += self.rotation_speed_z * dt

        # Wrap angles
        self.rotation_x %= (2 * math.pi)
        self.rotation_y %= (2 * math.pi)
        self.rotation_z %= (2 * math.pi)

    def draw(self):
        """Draw the viewer."""
        self.renderer.clear_buffer()

        # Transform and project vertices
        projected_vertices = []

        for vertex in self.current_solid.vertices:
            # Apply rotations
            v = vertex.rotate_x(self.rotation_x)
            v = v.rotate_y(self.rotation_y)
            v = v.rotate_z(self.rotation_z)

            # Scale
            v = Vector3(v.x * self.zoom, v.y * self.zoom, v.z * self.zoom)

            # Project to 2D
            x, y = v.project(self.width, self.height, self.fov, self.distance)
            projected_vertices.append((x, y, v.z))

        # Draw edges
        for edge in self.current_solid.edges:
            v1_idx, v2_idx = edge
            x1, y1, z1 = projected_vertices[v1_idx]
            x2, y2, z2 = projected_vertices[v2_idx]

            self._draw_line(x1, y1, x2, y2, self.current_solid.color)

        # Draw vertices (highlight)
        for x, y, z in projected_vertices:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.renderer.set_pixel(x, y, '●', Color.BRIGHT_WHITE)

        # Draw HUD
        self._draw_hud()

        self.renderer.render()

    def _draw_line(self, x0, y0, x1, y1, color):
        """Draw a line using Bresenham's algorithm."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                # Determine line character based on direction
                if abs(dx) > abs(dy):
                    char = '─'
                elif abs(dy) > abs(dx):
                    char = '│'
                else:
                    char = '/' if (sx > 0 and sy > 0) or (sx < 0 and sy < 0) else '\\'

                self.renderer.set_pixel(x0, y0, char, color)

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def _draw_hud(self):
        """Draw heads-up display."""
        # Title
        title = f"PLATONIC SOLIDS - {self.current_solid.name}"
        self.renderer.draw_text(self.width // 2 - len(title) // 2, 1,
                                title, Color.BRIGHT_CYAN)

        # Info
        info = f"Vertices: {len(self.current_solid.vertices)}  Edges: {len(self.current_solid.edges)}  Faces: {len(self.current_solid.faces)}"
        self.renderer.draw_text(self.width // 2 - len(info) // 2, 2,
                                info, Color.WHITE)

        # Rotation angles
        rot_text = f"Rotation: X={math.degrees(self.rotation_x):.1f}°  Y={math.degrees(self.rotation_y):.1f}°  Z={math.degrees(self.rotation_z):.1f}°"
        self.renderer.draw_text(2, self.height - 4, rot_text, Color.YELLOW)

        # Auto-rotate status
        auto_text = f"Auto-rotate: {'ON' if self.auto_rotate else 'OFF'}"
        self.renderer.draw_text(2, self.height - 3, auto_text,
                                Color.BRIGHT_GREEN if self.auto_rotate else Color.RED)

        # Zoom
        zoom_text = f"Zoom: {self.zoom}"
        self.renderer.draw_text(2, self.height - 2, zoom_text, Color.CYAN)

        # Controls
        controls = "SPACE:Next  R:Auto-rotate  C:Reset  Q/E:Roll  +/-:Zoom  ESC:Exit"
        self.renderer.draw_text(2, self.height - 1, controls, Color.WHITE)

    def run(self):
        """Main viewer loop."""
        # Set up signal handler for clean Ctrl+C exit
        def signal_handler(sig, frame):
            pass  # Will exit naturally via the running flag

        old_handler = signal.signal(signal.SIGINT, signal_handler)

        try:
            self.renderer.enter_fullscreen()
            running = True

            while running:
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time

                # Cap dt
                dt = min(dt, 0.1)

                # Handle input
                input_type = self.input_handler.get_input(timeout=0.001)

                if input_type == InputType.BACK or input_type == InputType.QUIT:
                    running = False

                # Continuous input
                self.handle_input(dt)

                # Update
                self.update(dt)

                # Draw
                self.draw()

                # Frame rate (30-60 FPS)
                time.sleep(0.016)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()
            signal.signal(signal.SIGINT, old_handler)


def run_platonic_solids():
    """Entry point for Platonic Solids viewer."""
    viewer = PlatonicSolidsViewer()
    viewer.run()


if __name__ == "__main__":
    run_platonic_solids()
