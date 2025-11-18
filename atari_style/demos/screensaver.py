"""Parametric animation screen saver."""

import math
import time
import random
from ..core.renderer import Renderer, Color
from ..core.input_handler import InputHandler, InputType


class ParametricAnimation:
    """Base class for parametric animations."""

    def __init__(self, renderer: Renderer):
        self.renderer = renderer
        self.t = 0.0

    def draw(self, t: float):
        """Override this method to implement the animation."""
        pass

    def update(self, dt: float):
        """Update animation time."""
        self.t += dt


class LissajousCurve(ParametricAnimation):
    """Lissajous curve animation."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.a = 3.0  # Frequency X (param 1)
        self.b = 4.0  # Frequency Y (param 2)
        self.delta = math.pi / 2  # Phase offset (param 3)
        self.points = 500  # Resolution (param 4)

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters. param 1-4, delta is +/- change."""
        if param == 1:
            self.a = max(1.0, min(10.0, self.a + delta))
        elif param == 2:
            self.b = max(1.0, min(10.0, self.b + delta))
        elif param == 3:
            self.delta = (self.delta + delta) % (2 * math.pi)
        elif param == 4:
            self.points = int(max(100, min(1000, self.points + delta * 50)))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Freq X: {self.a:.1f}",
            f"Freq Y: {self.b:.1f}",
            f"Phase: {self.delta:.2f}",
            f"Points: {self.points}"
        ]

    def draw(self, t: float):
        """Draw Lissajous curve."""
        cx = self.renderer.width // 2
        cy = self.renderer.height // 2
        scale_x = self.renderer.width // 3
        scale_y = self.renderer.height // 3

        # Draw the curve
        points = self.points
        for i in range(points):
            angle = (i / points) * 2 * math.pi
            x = int(cx + scale_x * math.sin(self.a * angle + t))
            y = int(cy + scale_y * math.sin(self.b * angle + self.delta + t * 0.5))

            # Color based on position
            color_idx = int((i / points) * 6)
            colors = [Color.RED, Color.YELLOW, Color.GREEN, Color.CYAN, Color.BLUE, Color.MAGENTA]
            self.renderer.set_pixel(x, y, '●', colors[color_idx])


class SpiralAnimation(ParametricAnimation):
    """Spiral pattern animation."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.num_spirals = 3  # Number of spirals (param 1)
        self.rotation_speed = 1.0  # Rotation speed multiplier (param 2)
        self.tightness = 6.0  # How many rotations (param 3)
        self.radius_scale = 0.4  # Size of spirals (param 4)

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters."""
        if param == 1:
            self.num_spirals = int(max(1, min(8, self.num_spirals + delta)))
        elif param == 2:
            self.rotation_speed = max(0.1, min(5.0, self.rotation_speed + delta * 0.1))
        elif param == 3:
            self.tightness = max(2.0, min(15.0, self.tightness + delta * 0.5))
        elif param == 4:
            self.radius_scale = max(0.2, min(0.8, self.radius_scale + delta * 0.05))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Spirals: {self.num_spirals}",
            f"Speed: {self.rotation_speed:.1f}x",
            f"Tight: {self.tightness:.1f}",
            f"Scale: {self.radius_scale:.2f}"
        ]

    def draw(self, t: float):
        """Draw animated spiral."""
        cx = self.renderer.width // 2
        cy = self.renderer.height // 2

        num_spirals = self.num_spirals
        for spiral in range(num_spirals):
            offset = (spiral / num_spirals) * 2 * math.pi
            points = 200

            for i in range(points):
                angle = (i / points) * self.tightness * math.pi + t * self.rotation_speed + offset
                radius = (i / points) * min(self.renderer.width, self.renderer.height) * self.radius_scale

                x = int(cx + radius * math.cos(angle))
                y = int(cy + radius * math.sin(angle) * 0.5)  # Squash Y for terminal aspect

                if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                    brightness = i / points
                    if brightness > 0.7:
                        color = Color.BRIGHT_CYAN
                    elif brightness > 0.4:
                        color = Color.CYAN
                    else:
                        color = Color.BLUE
                    self.renderer.set_pixel(x, y, '●', color)


class CircleWaveAnimation(ParametricAnimation):
    """Concentric circles with wave effect."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.num_circles = 15  # Number of circles (param 1)
        self.wave_amplitude = 2.0  # Wave size (param 2)
        self.wave_frequency = 0.5  # Wave frequency (param 3)
        self.spacing = 3.0  # Circle spacing (param 4)

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters."""
        if param == 1:
            self.num_circles = int(max(5, min(30, self.num_circles + delta)))
        elif param == 2:
            self.wave_amplitude = max(0.5, min(8.0, self.wave_amplitude + delta * 0.2))
        elif param == 3:
            self.wave_frequency = max(0.1, min(2.0, self.wave_frequency + delta * 0.1))
        elif param == 4:
            self.spacing = max(1.0, min(6.0, self.spacing + delta * 0.2))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Circles: {self.num_circles}",
            f"Amplitude: {self.wave_amplitude:.1f}",
            f"Wave Freq: {self.wave_frequency:.1f}",
            f"Spacing: {self.spacing:.1f}"
        ]

    def draw(self, t: float):
        """Draw wave circles."""
        cx = self.renderer.width // 2
        cy = self.renderer.height // 2

        num_circles = self.num_circles
        for i in range(num_circles):
            radius = (i + 1) * self.spacing + math.sin(t + i * self.wave_frequency) * self.wave_amplitude
            points = int(radius * 6)

            # Color based on circle index
            colors = [Color.RED, Color.YELLOW, Color.GREEN, Color.CYAN, Color.BLUE, Color.MAGENTA]
            color = colors[i % len(colors)]

            for p in range(points):
                angle = (p / points) * 2 * math.pi
                x = int(cx + radius * math.cos(angle))
                y = int(cy + radius * math.sin(angle) * 0.5)  # Aspect ratio correction

                if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                    self.renderer.set_pixel(x, y, '○', color)


class PlasmaAnimation(ParametricAnimation):
    """Plasma effect."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.freq_x = 0.1  # X frequency (param 1)
        self.freq_y = 0.1  # Y frequency (param 2)
        self.freq_diag = 0.08  # Diagonal frequency (param 3)
        self.freq_radial = 0.1  # Radial frequency (param 4)

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters."""
        if param == 1:
            self.freq_x = max(0.01, min(0.3, self.freq_x + delta * 0.01))
        elif param == 2:
            self.freq_y = max(0.01, min(0.3, self.freq_y + delta * 0.01))
        elif param == 3:
            self.freq_diag = max(0.01, min(0.3, self.freq_diag + delta * 0.01))
        elif param == 4:
            self.freq_radial = max(0.01, min(0.3, self.freq_radial + delta * 0.01))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Freq X: {self.freq_x:.2f}",
            f"Freq Y: {self.freq_y:.2f}",
            f"Freq Diag: {self.freq_diag:.2f}",
            f"Freq Rad: {self.freq_radial:.2f}"
        ]

    def draw(self, t: float):
        """Draw plasma effect."""
        for y in range(0, self.renderer.height, 2):
            for x in range(0, self.renderer.width, 2):
                # Multiple sine waves
                value = math.sin(x * self.freq_x + t)
                value += math.sin(y * self.freq_y + t * 1.2)
                value += math.sin((x + y) * self.freq_diag + t * 0.8)
                value += math.sin(math.sqrt(x * x + y * y) * self.freq_radial + t * 1.5)
                value = value / 4.0

                # Map value to color
                colors = [
                    Color.BLUE, Color.CYAN, Color.GREEN,
                    Color.YELLOW, Color.RED, Color.MAGENTA
                ]
                color_idx = int((value + 1) * 3) % len(colors)
                color = colors[color_idx]

                # Choose character based on value
                if value > 0.5:
                    char = '█'
                elif value > 0:
                    char = '▓'
                elif value > -0.5:
                    char = '▒'
                else:
                    char = '░'

                self.renderer.set_pixel(x, y, char, color)


class MandelbrotZoomer(ParametricAnimation):
    """Mandelbrot set infinite zoom animation."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.zoom = 1.0  # Zoom level (param 1)
        self.center_x = -0.5  # Center X coordinate (param 2)
        self.center_y = 0.0  # Center Y coordinate (param 3)
        self.max_iterations = 50  # Detail level (param 4)

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters."""
        if param == 1:
            self.zoom = max(0.1, min(1000.0, self.zoom * (1.1 if delta > 0 else 0.9)))
        elif param == 2:
            self.center_x = max(-2.0, min(1.0, self.center_x + delta * 0.05))
        elif param == 3:
            self.center_y = max(-1.5, min(1.5, self.center_y + delta * 0.05))
        elif param == 4:
            self.max_iterations = int(max(10, min(200, self.max_iterations + delta * 5)))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Zoom: {self.zoom:.1f}x",
            f"Center X: {self.center_x:.3f}",
            f"Center Y: {self.center_y:.3f}",
            f"Detail: {self.max_iterations}"
        ]

    def mandelbrot(self, c_real: float, c_imag: float) -> int:
        """Calculate Mandelbrot iterations for a point."""
        z_real, z_imag = 0.0, 0.0
        for i in range(self.max_iterations):
            if z_real * z_real + z_imag * z_imag > 4.0:
                return i
            z_real, z_imag = z_real * z_real - z_imag * z_imag + c_real, 2 * z_real * z_imag + c_imag
        return self.max_iterations

    def draw(self, t: float):
        """Draw Mandelbrot set."""
        # Auto-zoom over time
        auto_zoom = self.zoom * (1.0 + math.sin(t * 0.2) * 0.1)

        # Calculate view bounds
        aspect_ratio = self.renderer.width / (self.renderer.height * 2)
        range_x = 3.0 / auto_zoom
        range_y = 2.0 / auto_zoom

        # Render every other pixel for performance
        for y in range(0, self.renderer.height, 2):
            for x in range(0, self.renderer.width, 2):
                # Map pixel to complex plane
                c_real = self.center_x + (x / self.renderer.width - 0.5) * range_x
                c_imag = self.center_y + (y / self.renderer.height - 0.5) * range_y

                # Calculate iterations
                iterations = self.mandelbrot(c_real, c_imag)

                # Color based on iterations
                if iterations == self.max_iterations:
                    color = Color.BLUE
                    char = '█'
                else:
                    ratio = iterations / self.max_iterations
                    if ratio > 0.8:
                        color = Color.BRIGHT_CYAN
                        char = '●'
                    elif ratio > 0.6:
                        color = Color.CYAN
                        char = '○'
                    elif ratio > 0.4:
                        color = Color.GREEN
                        char = '·'
                    elif ratio > 0.2:
                        color = Color.YELLOW
                        char = '.'
                    else:
                        color = Color.RED
                        char = ','

                self.renderer.set_pixel(x, y, char, color)


class FluidLattice(ParametricAnimation):
    """Fluid lattice simulation with rain drops."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.wave_speed = 0.5  # Wave propagation speed (param 1)
        self.damping = 0.95  # Damping factor (param 2)
        self.rain_rate = 0.1  # Rain drop frequency (param 3)
        self.drop_strength = 5.0  # Drop impact strength (param 4)

        # Initialize lattice
        self.width = self.renderer.width // 2
        self.height = self.renderer.height
        self.current = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.previous = [[0.0 for _ in range(self.width)] for _ in range(self.height)]

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters."""
        if param == 1:
            self.wave_speed = max(0.1, min(2.0, self.wave_speed + delta * 0.05))
        elif param == 2:
            self.damping = max(0.8, min(0.99, self.damping + delta * 0.01))
        elif param == 3:
            self.rain_rate = max(0.0, min(1.0, self.rain_rate + delta * 0.05))
        elif param == 4:
            self.drop_strength = max(1.0, min(15.0, self.drop_strength + delta * 0.5))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Wave Speed: {self.wave_speed:.2f}",
            f"Damping: {self.damping:.2f}",
            f"Rain Rate: {self.rain_rate:.2f}",
            f"Drop Power: {self.drop_strength:.1f}"
        ]

    def update(self, dt: float):
        """Update lattice simulation."""
        super().update(dt)

        # Add random rain drops
        if random.random() < self.rain_rate * dt:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            self.current[y][x] += self.drop_strength

        # Wave equation simulation
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                # Calculate Laplacian (neighbors)
                laplacian = (
                    self.current[y - 1][x] + self.current[y + 1][x] +
                    self.current[y][x - 1] + self.current[y][x + 1] -
                    4 * self.current[y][x]
                )

                # Wave equation: d²u/dt² = c² ∇²u
                new_value = (
                    2 * self.current[y][x] - self.previous[y][x] +
                    self.wave_speed * self.wave_speed * laplacian
                )

                # Apply damping
                new_value *= self.damping

                # Update
                self.previous[y][x] = self.current[y][x]
                self.current[y][x] = new_value

    def draw(self, t: float):
        """Draw fluid lattice."""
        for y in range(self.height):
            for x in range(self.width):
                value = self.current[y][x]

                # Map value to character and color
                if abs(value) < 0.5:
                    char = ' '
                    color = None
                elif abs(value) < 2.0:
                    char = '·'
                    color = Color.BLUE if value > 0 else Color.CYAN
                elif abs(value) < 4.0:
                    char = '○'
                    color = Color.CYAN if value > 0 else Color.GREEN
                elif abs(value) < 6.0:
                    char = '●'
                    color = Color.BRIGHT_CYAN if value > 0 else Color.BRIGHT_BLUE
                else:
                    char = '█'
                    color = Color.BRIGHT_WHITE if value > 0 else Color.BRIGHT_CYAN

                if color:
                    self.renderer.set_pixel(x * 2, y, char, color)


class ParticleSwarm(ParametricAnimation):
    """Particle swarm with boid-like behavior."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.num_particles = 50  # Number of particles (param 1)
        self.speed = 2.0  # Movement speed (param 2)
        self.cohesion = 0.5  # Attraction to center (param 3)
        self.separation = 1.0  # Repulsion from neighbors (param 4)

        # Initialize particles
        self.particles = []
        for _ in range(100):  # Max capacity
            self.particles.append({
                'x': random.uniform(0, self.renderer.width),
                'y': random.uniform(0, self.renderer.height),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'active': False
            })

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters."""
        if param == 1:
            self.num_particles = int(max(10, min(100, self.num_particles + delta * 5)))
        elif param == 2:
            self.speed = max(0.5, min(5.0, self.speed + delta * 0.2))
        elif param == 3:
            self.cohesion = max(0.0, min(2.0, self.cohesion + delta * 0.1))
        elif param == 4:
            self.separation = max(0.0, min(3.0, self.separation + delta * 0.1))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Particles: {self.num_particles}",
            f"Speed: {self.speed:.1f}",
            f"Cohesion: {self.cohesion:.1f}",
            f"Separation: {self.separation:.1f}"
        ]

    def update(self, dt: float):
        """Update particle positions."""
        super().update(dt)

        # Activate/deactivate particles based on count
        for i, p in enumerate(self.particles):
            p['active'] = i < self.num_particles

        # Update active particles
        active = [p for p in self.particles if p['active']]

        for p in active:
            # Calculate center of mass
            cx = sum(other['x'] for other in active) / len(active)
            cy = sum(other['y'] for other in active) / len(active)

            # Cohesion: move toward center
            p['vx'] += (cx - p['x']) * self.cohesion * 0.01
            p['vy'] += (cy - p['y']) * self.cohesion * 0.01

            # Separation: avoid crowding
            for other in active:
                if other is p:
                    continue
                dx = p['x'] - other['x']
                dy = p['y'] - other['y']
                dist = math.sqrt(dx * dx + dy * dy) + 0.1
                if dist < 10:
                    p['vx'] += dx / dist * self.separation * 0.1
                    p['vy'] += dy / dist * self.separation * 0.1

            # Limit speed
            speed = math.sqrt(p['vx'] * p['vx'] + p['vy'] * p['vy'])
            if speed > self.speed:
                p['vx'] = p['vx'] / speed * self.speed
                p['vy'] = p['vy'] / speed * self.speed

            # Update position
            p['x'] += p['vx']
            p['y'] += p['vy'] * 0.5  # Aspect ratio

            # Wrap around edges
            p['x'] = p['x'] % self.renderer.width
            p['y'] = p['y'] % self.renderer.height

    def draw(self, t: float):
        """Draw particles."""
        colors = [Color.RED, Color.YELLOW, Color.GREEN, Color.CYAN, Color.BLUE, Color.MAGENTA]

        for i, p in enumerate(self.particles):
            if not p['active']:
                continue

            x = int(p['x'])
            y = int(p['y'])

            if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                color = colors[i % len(colors)]
                # Draw particle with tail
                self.renderer.set_pixel(x, y, '●', color)
                # Draw velocity vector
                tail_x = int(x - p['vx'] * 2)
                tail_y = int(y - p['vy'])
                if 0 <= tail_x < self.renderer.width and 0 <= tail_y < self.renderer.height:
                    self.renderer.set_pixel(tail_x, tail_y, '·', color)


class TunnelVision(ParametricAnimation):
    """Classic demo-scene tunnel effect."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.depth_speed = 1.0  # How fast we move through tunnel (param 1)
        self.rotation_speed = 0.5  # Tunnel rotation (param 2)
        self.tunnel_size = 1.0  # Tunnel diameter (param 3)
        self.color_cycle_speed = 1.0  # Color animation speed (param 4)

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters."""
        if param == 1:
            self.depth_speed = max(0.1, min(5.0, self.depth_speed + delta * 0.1))
        elif param == 2:
            self.rotation_speed = max(-2.0, min(2.0, self.rotation_speed + delta * 0.1))
        elif param == 3:
            self.tunnel_size = max(0.3, min(3.0, self.tunnel_size + delta * 0.1))
        elif param == 4:
            self.color_cycle_speed = max(0.1, min(3.0, self.color_cycle_speed + delta * 0.1))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Depth Speed: {self.depth_speed:.1f}",
            f"Rotation: {self.rotation_speed:.1f}",
            f"Size: {self.tunnel_size:.1f}",
            f"Color Speed: {self.color_cycle_speed:.1f}"
        ]

    def draw(self, t: float):
        """Draw tunnel effect."""
        cx = self.renderer.width // 2
        cy = self.renderer.height // 2

        for y in range(self.renderer.height):
            for x in range(0, self.renderer.width, 2):
                # Calculate distance from center
                dx = x - cx
                dy = (y - cy) * 2  # Aspect ratio
                dist = math.sqrt(dx * dx + dy * dy) + 0.1

                # Calculate angle
                angle = math.atan2(dy, dx)

                # Tunnel depth based on distance
                depth = (1.0 / dist) * self.tunnel_size * 100 + t * self.depth_speed

                # Rotation
                rotated_angle = angle + t * self.rotation_speed + depth * 0.1

                # Create tunnel pattern
                tunnel_u = int(depth) % 10
                tunnel_v = int(rotated_angle * 5) % 10

                # Color based on depth and time
                color_phase = (depth * 0.1 + t * self.color_cycle_speed) % 6
                colors = [Color.RED, Color.YELLOW, Color.GREEN, Color.CYAN, Color.BLUE, Color.MAGENTA]
                color = colors[int(color_phase)]

                # Character based on pattern
                if (tunnel_u + tunnel_v) % 3 == 0:
                    char = '█'
                elif (tunnel_u + tunnel_v) % 3 == 1:
                    char = '▓'
                else:
                    char = '▒'

                self.renderer.set_pixel(x, y, char, color)


class ScreenSaver:
    """Screen saver with multiple parametric animations."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True
        self.show_params = True  # Show parameter values

        # Animation modes
        self.animations = [
            LissajousCurve(self.renderer),
            SpiralAnimation(self.renderer),
            CircleWaveAnimation(self.renderer),
            PlasmaAnimation(self.renderer),
            MandelbrotZoomer(self.renderer),
            FluidLattice(self.renderer),
            ParticleSwarm(self.renderer),
            TunnelVision(self.renderer),
        ]
        self.animation_names = [
            "Lissajous Curve",
            "Spiral",
            "Wave Circles",
            "Plasma",
            "Mandelbrot Zoomer",
            "Fluid Lattice",
            "Particle Swarm",
            "Tunnel Vision",
        ]
        self.current_animation = 0
        self.speed_multiplier = 2.0  # Increased animation speed

    def draw(self):
        """Render the current animation."""
        self.renderer.clear_buffer()

        # Draw current animation
        anim = self.animations[self.current_animation]
        anim.draw(anim.t)

        # Draw HUD
        name = self.animation_names[self.current_animation]
        self.renderer.draw_text(2, 1, f"Mode: {name}", Color.YELLOW)
        self.renderer.draw_text(2, 2, f"[{self.current_animation + 1}/{len(self.animations)}]", Color.YELLOW)

        # Draw parameter values if enabled
        if self.show_params and hasattr(anim, 'get_param_info'):
            param_info = anim.get_param_info()
            for i, param in enumerate(param_info):
                self.renderer.draw_text(2, 4 + i, param, Color.BRIGHT_GREEN)

        # Draw controls
        control_y = 1
        self.renderer.draw_text(self.renderer.width - 30, control_y, "SPACE/BTN0: Next Mode", Color.CYAN)
        self.renderer.draw_text(self.renderer.width - 30, control_y + 1, "Joystick: Adjust Params", Color.CYAN)
        self.renderer.draw_text(self.renderer.width - 30, control_y + 2, "ESC/Q/BTN1: Exit", Color.CYAN)

        self.renderer.render()

    def update(self, dt: float):
        """Update animation."""
        self.animations[self.current_animation].update(dt * self.speed_multiplier)

    def handle_input(self):
        """Handle user input and joystick directions for parameter control."""
        input_type = self.input_handler.get_input(timeout=0.01)

        # Mode switching with buttons only
        if input_type == InputType.SELECT:
            self.current_animation = (self.current_animation + 1) % len(self.animations)
            time.sleep(0.2)  # Debounce
        elif input_type == InputType.QUIT or input_type == InputType.BACK:
            self.running = False

        # Get joystick state for parameter control
        # Opposite directions control the same parameter (one increases, one decreases)
        if self.input_handler.joystick_initialized:
            x, y = self.input_handler.get_joystick_state()
            anim = self.animations[self.current_animation]

            # Determine which parameter to adjust based on 8 directions
            if hasattr(anim, 'adjust_params'):
                threshold = 0.3
                param_adjusted = False

                # UP ↔ DOWN (opposite pair) → Param 1
                if y < -threshold and abs(x) < threshold:
                    anim.adjust_params(1, 1.0)  # UP increases
                    param_adjusted = True
                elif y > threshold and abs(x) < threshold:
                    anim.adjust_params(1, -1.0)  # DOWN decreases
                    param_adjusted = True

                # RIGHT ↔ LEFT (opposite pair) → Param 2
                elif x > threshold and abs(y) < threshold:
                    anim.adjust_params(2, 1.0)  # RIGHT increases
                    param_adjusted = True
                elif x < -threshold and abs(y) < threshold:
                    anim.adjust_params(2, -1.0)  # LEFT decreases
                    param_adjusted = True

                # UP-RIGHT ↔ DOWN-LEFT (opposite diagonal pair) → Param 3
                elif y < -threshold and x > threshold:
                    anim.adjust_params(3, 1.0)  # UP-RIGHT increases
                    param_adjusted = True
                elif y > threshold and x < -threshold:
                    anim.adjust_params(3, -1.0)  # DOWN-LEFT decreases
                    param_adjusted = True

                # UP-LEFT ↔ DOWN-RIGHT (opposite diagonal pair) → Param 4
                elif y < -threshold and x < -threshold:
                    anim.adjust_params(4, 1.0)  # UP-LEFT increases
                    param_adjusted = True
                elif y > threshold and x > threshold:
                    anim.adjust_params(4, -1.0)  # DOWN-RIGHT decreases
                    param_adjusted = True

                # Small delay after parameter adjustment to prevent too rapid changes
                if param_adjusted:
                    time.sleep(0.05)

    def run(self):
        """Run the screen saver."""
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            last_time = time.time()
            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                self.draw()
                self.update(dt)
                self.handle_input()
                time.sleep(0.016)  # ~60 FPS

        finally:
            self.renderer.exit_fullscreen()


def run_screensaver():
    """Entry point for screen saver."""
    saver = ScreenSaver()
    saver.run()
