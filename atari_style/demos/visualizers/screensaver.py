"""Parametric animation screen saver."""

import math
import time
import random
import pygame
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType
from .screensaver_presets import ANIMATION_PRESETS, get_preset_names, get_preset


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

    def get_value_at(self, x: int, y: int, t: float) -> float:
        """Get normalized value (-1.0 to 1.0) at screen position (x, y) and time t.
        
        This method allows animations to be used as modulation sources.
        Override in subclasses to provide meaningful values.
        
        Args:
            x: Screen X coordinate
            y: Screen Y coordinate
            t: Current time
            
        Returns:
            float: Normalized value representing animation state at this point
        """
        return 0.0

    def get_global_value(self, t: float) -> float:
        """Get global scalar value for the entire animation at time t.
        
        This provides a single value representing the overall state of the animation,
        useful for modulating parameters of other animations.
        
        Args:
            t: Current time
            
        Returns:
            float: Normalized value (-1.0 to 1.0) representing overall animation state
        """
        return 0.0


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

    def get_value_at(self, x: int, y: int, t: float) -> float:
        """Get normalized distance to nearest curve point.
        
        Returns a value based on how close (x, y) is to the Lissajous curve.
        Closer points return values closer to 1.0.
        """
        cx = self.renderer.width // 2
        cy = self.renderer.height // 2
        scale_x = self.renderer.width // 3
        scale_y = self.renderer.height // 3
        
        # Sample a few points on the curve and find minimum distance
        min_dist_sq = float('inf')
        # Note: 50 samples is a reasonable compromise between accuracy and performance
        # This method is typically called infrequently in current composites
        # For heavy use cases, consider caching or adaptive sampling
        samples = 50
        
        for i in range(samples):
            angle = (i / samples) * 2 * math.pi
            curve_x = cx + scale_x * math.sin(self.a * angle + t)
            curve_y = cy + scale_y * math.sin(self.b * angle + self.delta + t * 0.5)
            
            dx = x - curve_x
            dy = y - curve_y
            dist_sq = dx * dx + dy * dy
            min_dist_sq = min(min_dist_sq, dist_sq)
        
        # Convert distance to normalized value (closer = higher value)
        # Use exponential decay for smoother falloff
        max_dist = 50.0  # Maximum meaningful distance
        normalized_dist = min(math.sqrt(min_dist_sq) / max_dist, 1.0)
        return 1.0 - normalized_dist  # Invert so close = high value

    def get_global_value(self, t: float) -> float:
        """Get current phase angle of the curve.
        
        Returns the sine of the current time, providing a smooth oscillation
        that can drive other parameters.
        """
        return math.sin(t)


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

    def get_value_at(self, x: int, y: int, t: float) -> float:
        """Get plasma value at specific position.
        
        Returns the normalized plasma value at the given screen coordinate.
        """
        # Calculate plasma value using same formula as draw()
        value = math.sin(x * self.freq_x + t)
        value += math.sin(y * self.freq_y + t * 1.2)
        value += math.sin((x + y) * self.freq_diag + t * 0.8)
        value += math.sin(math.sqrt(x * x + y * y) * self.freq_radial + t * 1.5)
        value = value / 4.0  # Normalize to [-1, 1] range
        return value

    def get_global_value(self, t: float) -> float:
        """Get average plasma value across center region.
        
        Samples a few points near the center and returns their average.
        This is more efficient than sampling the entire screen.
        """
        cx = self.renderer.width // 2
        cy = self.renderer.height // 2
        
        # Sample 9 points in a 3x3 grid around center
        total = 0.0
        samples = 0
        for dy in [-5, 0, 5]:
            for dx in [-5, 0, 5]:
                x = cx + dx
                y = cy + dy
                if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                    total += self.get_value_at(x, y, t)
                    samples += 1
        
        return total / samples if samples > 0 else 0.0


class MandelbrotZoomer(ParametricAnimation):
    """Mandelbrot set infinite zoom animation."""

    def __init__(self, renderer: Renderer):
        super().__init__(renderer)
        self.zoom = 1.0  # Zoom level (param 1)
        self.center_x = -0.5  # Center X coordinate (param 2)
        self.center_y = 0.0  # Center Y coordinate (param 3)
        self.max_iterations = 50  # Detail level (param 4)
        self.zoom_mode = False  # Toggle for zoom mode (button 2)

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters.

        When zoom_mode is True:
        - UP/DOWN controls zoom (param 1)
        - LEFT/RIGHT/DIAGONALS control panning (params 2 & 3)

        When zoom_mode is False:
        - Standard 4-parameter diagonal control
        """
        if self.zoom_mode:
            # Zoom mode: UP/DOWN = zoom, X/Y axis = pan
            if param == 1:  # UP/DOWN
                self.zoom = max(0.1, min(1000.0, self.zoom * (1.1 if delta > 0 else 0.9)))
            elif param == 2:  # LEFT/RIGHT
                self.center_x = max(-2.0, min(1.0, self.center_x + delta * 0.05))
            elif param == 3:  # UP-RIGHT/DOWN-LEFT (diagonal treated as Y-pan)
                self.center_y = max(-1.5, min(1.5, self.center_y + delta * 0.05))
            elif param == 4:  # UP-LEFT/DOWN-RIGHT (diagonal treated as Y-pan)
                self.center_y = max(-1.5, min(1.5, self.center_y + delta * 0.05))
        else:
            # Standard mode: all 4 parameters
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
        mode_str = "[ZOOM MODE]" if self.zoom_mode else ""
        return [
            f"Zoom: {self.zoom:.1f}x {mode_str}",
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
        # Remapped parameters for better intuitiveness:
        # UP/DOWN: Rain frequency (most visible effect)
        # LEFT/RIGHT: Wave speed (horizontal = speed)
        # UP-RIGHT/DOWN-LEFT: Drop strength (splash size)
        # UP-LEFT/DOWN-RIGHT: Damping (wave persistence)
        self.rain_rate = 0.35  # Rain drop frequency (param 1) - MORE RAIN!
        self.wave_speed = 0.3  # Wave propagation speed (param 2) - SLOWER for visibility
        self.drop_strength = 8.0  # Drop impact strength (param 3) - STRONGER!
        self.damping = 0.97  # Damping factor (param 4) - LESS damping (waves last longer)

        # Initialize lattice
        self.width = self.renderer.width // 2
        self.height = self.renderer.height
        self.current = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.previous = [[0.0 for _ in range(self.width)] for _ in range(self.height)]

    def adjust_params(self, param: int, delta: float):
        """Adjust parameters."""
        if param == 1:  # UP/DOWN: Rain frequency
            self.rain_rate = max(0.0, min(1.5, self.rain_rate + delta * 0.05))
        elif param == 2:  # LEFT/RIGHT: Wave speed
            self.wave_speed = max(0.05, min(1.0, self.wave_speed + delta * 0.02))
        elif param == 3:  # UP-RIGHT/DOWN-LEFT: Drop strength
            self.drop_strength = max(3.0, min(20.0, self.drop_strength + delta * 0.5))
        elif param == 4:  # UP-LEFT/DOWN-RIGHT: Damping
            self.damping = max(0.85, min(0.995, self.damping + delta * 0.005))

    def get_param_info(self) -> list:
        """Return current parameter values for display."""
        return [
            f"Rain Rate: {self.rain_rate:.2f}",
            f"Wave Speed: {self.wave_speed:.2f}",
            f"Drop Power: {self.drop_strength:.1f}",
            f"Damping: {self.damping:.3f}"
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

                # Zero out small values to prevent accumulation
                if abs(new_value) < 0.2:
                    new_value = 0.0

                # Update
                self.previous[y][x] = self.current[y][x]
                self.current[y][x] = new_value

    def draw(self, t: float):
        """Draw fluid lattice."""
        for y in range(self.height):
            for x in range(self.width):
                value = self.current[y][x]

                # Map value to character and color - ADJUSTED THRESHOLDS
                if abs(value) < 0.3:  # Lowered from 0.5
                    char = ' '
                    color = None
                elif abs(value) < 1.5:  # Lowered from 2.0
                    char = '·'
                    color = Color.BLUE if value > 0 else Color.CYAN
                elif abs(value) < 3.0:  # Lowered from 4.0
                    char = '○'
                    color = Color.CYAN if value > 0 else Color.GREEN
                elif abs(value) < 5.0:  # Lowered from 6.0
                    char = '●'
                    color = Color.BRIGHT_CYAN if value > 0 else Color.BRIGHT_BLUE
                else:
                    char = '█'
                    color = Color.BRIGHT_WHITE if value > 0 else Color.BRIGHT_CYAN

                if color:
                    self.renderer.set_pixel(x * 2, y, char, color)

    def get_value_at(self, x: int, y: int, t: float) -> float:
        """Get fluid height at specific lattice position.
        
        Returns the normalized wave amplitude at the given position.
        """
        # Convert screen coordinates to lattice coordinates
        lx = x // 2
        ly = y
        
        if 0 <= lx < self.width and 0 <= ly < self.height:
            # Normalize to [-1, 1] range
            # Fluid values typically range from -10 to +10
            value = self.current[ly][lx]
            return max(-1.0, min(1.0, value / 10.0))
        return 0.0

    def get_global_value(self, t: float) -> float:
        """Get average wave energy across the lattice.
        
        Returns the average absolute value of all wave heights,
        representing overall fluid activity.
        """
        total = 0.0
        count = 0
        
        # Adaptive sampling based on lattice size
        # Aim for ~100-200 samples regardless of lattice size
        step = max(1, min(self.width, self.height) // 15)
        
        for y in range(0, self.height, step):
            for x in range(0, self.width, step):
                total += abs(self.current[y][x])
                count += 1
        
        if count == 0:
            return 0.0
        
        # Normalize average to [-1, 1] range
        avg = total / count
        return max(-1.0, min(1.0, avg / 5.0))


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


class CompositeAnimation(ParametricAnimation):
    """Base class for composite animations that combine multiple animations.
    
    Composites use one animation as a modulation source to drive the parameters
    of another animation, creating emergent visual behaviors.
    """
    
    def __init__(self, renderer: Renderer, source: ParametricAnimation, target: ParametricAnimation):
        """Initialize composite animation.
        
        Args:
            renderer: The renderer instance
            source: Animation that provides modulation values
            target: Animation that receives modulation
        """
        super().__init__(renderer)
        self.source = source
        self.target = target
        self.modulation_strength = 1.0  # 0.0 = no modulation, 1.0 = full modulation
        self.modulation_mapping = "linear"  # linear, quadratic, sine
        
    def map_value(self, value: float, min_out: float, max_out: float) -> float:
        """Map normalized value from source to target parameter range.
        
        Args:
            value: Input value in range [-1.0, 1.0]
            min_out: Minimum output value
            max_out: Maximum output value
            
        Returns:
            Mapped value in range [min_out, max_out]
        """
        # Apply modulation strength and clamp to valid range
        value = value * self.modulation_strength
        value = max(-1.0, min(1.0, value))  # Clamp to [-1, 1]
        
        # Apply mapping function
        if self.modulation_mapping == "linear":
            # Linear mapping from [-1, 1] to [min_out, max_out]
            normalized = (value + 1.0) * 0.5  # Convert to [0, 1]
            return min_out + normalized * (max_out - min_out)
        elif self.modulation_mapping == "quadratic":
            # Quadratic easing for smoother transitions
            normalized = (value + 1.0) * 0.5
            eased = normalized * normalized
            return min_out + eased * (max_out - min_out)
        elif self.modulation_mapping == "sine":
            # Sinusoidal mapping for smooth oscillation
            normalized = (value + 1.0) * 0.5
            eased = math.sin(normalized * math.pi - math.pi / 2) * 0.5 + 0.5
            return min_out + eased * (max_out - min_out)
        else:
            # Default to linear
            normalized = (value + 1.0) * 0.5
            return min_out + normalized * (max_out - min_out)
    
    def adjust_params(self, param: int, delta: float):
        """Adjust composite-specific parameters."""
        if param == 1:
            # Modulation strength
            self.modulation_strength = max(0.0, min(2.0, self.modulation_strength + delta * 0.1))
        else:
            # Pass through to target animation
            self.target.adjust_params(param, delta)
    
    def get_param_info(self) -> list:
        """Return parameter info for composite."""
        target_info = self.target.get_param_info()
        return [f"Mod: {self.modulation_strength:.1f}x"] + target_info
    
    def update(self, dt: float):
        """Update both source and target animations."""
        super().update(dt)
        self.source.update(dt)
        self.target.update(dt)


class PlasmaLissajous(CompositeAnimation):
    """Lissajous curve with frequencies driven by plasma field.
    
    The plasma animation's global value modulates the Lissajous curve's
    X and Y frequencies, causing the curve to morph as the plasma undulates.
    """
    
    def __init__(self, renderer: Renderer):
        """Initialize PlasmaLissajous composite."""
        plasma = PlasmaAnimation(renderer)
        lissajous = LissajousCurve(renderer)
        super().__init__(renderer, plasma, lissajous)
        
        # Configure source plasma for interesting modulation
        self.source.freq_x = 0.08
        self.source.freq_y = 0.08
        self.source.freq_diag = 0.06
        
    def draw(self, t: float):
        """Draw Lissajous modulated by plasma."""
        # Sample plasma at center to get modulation value
        plasma_value = self.source.get_global_value(t)
        
        # Modulate Lissajous frequencies based on plasma
        self.target.a = self.map_value(plasma_value, 2.0, 6.0)
        self.target.b = self.map_value(-plasma_value, 2.0, 6.0)  # Inverse for contrast
        
        # Draw the modulated Lissajous
        self.target.draw(t)
        
    def get_param_info(self) -> list:
        """Return parameter info showing both animations."""
        return [
            f"Mod: {self.modulation_strength:.1f}x",
            f"Plasma→Liss",
            f"Freq X: {self.target.a:.1f}",
            f"Freq Y: {self.target.b:.1f}"
        ]


class FluxSpiral(CompositeAnimation):
    """Spiral with rotation driven by fluid wave energy.
    
    The fluid lattice animation's average wave height modulates the spiral's
    rotation speed, causing it to pulse with the rhythm of the waves.
    """
    
    def __init__(self, renderer: Renderer):
        """Initialize FluxSpiral composite."""
        flux = FluidLattice(renderer)
        spiral = SpiralAnimation(renderer)
        super().__init__(renderer, flux, spiral)
        
        # Configure flux for good wave action
        self.source.rain_rate = 0.5
        self.source.wave_speed = 0.4
        self.source.drop_strength = 10.0
        
        # Configure spiral for nice visual
        self.target.num_spirals = 3
        self.target.tightness = 8.0
        
    def draw(self, t: float):
        """Draw spiral modulated by fluid lattice."""
        # Get average fluid energy
        flux_value = self.source.get_global_value(t)
        
        # Modulate rotation speed based on wave energy
        self.target.rotation_speed = self.map_value(flux_value, 0.5, 3.0)
        
        # Also modulate tightness slightly for extra effect
        self.target.tightness = self.map_value(math.sin(t * 0.5), 6.0, 10.0)
        
        # Draw the modulated spiral
        self.target.draw(t)
        
    def get_param_info(self) -> list:
        """Return parameter info showing both animations."""
        return [
            f"Mod: {self.modulation_strength:.1f}x",
            f"Flux→Spiral",
            f"Speed: {self.target.rotation_speed:.1f}x",
            f"Tight: {self.target.tightness:.1f}"
        ]


class LissajousPlasma(CompositeAnimation):
    """Plasma with frequencies driven by Lissajous motion.
    
    The Lissajous curve's phase angle modulates the plasma's frequency
    parameters, causing the plasma colors to dance with the curve's motion.
    """
    
    def __init__(self, renderer: Renderer):
        """Initialize LissajousPlasma composite."""
        lissajous = LissajousCurve(renderer)
        plasma = PlasmaAnimation(renderer)
        super().__init__(renderer, lissajous, plasma)
        
        # Configure Lissajous for smooth motion
        self.source.a = 3.0
        self.source.b = 4.0
        self.source.delta = math.pi / 4
        
    def draw(self, t: float):
        """Draw plasma modulated by Lissajous."""
        # Get Lissajous phase value
        liss_value = self.source.get_global_value(t)
        
        # Modulate plasma frequencies based on Lissajous motion
        self.target.freq_x = self.map_value(liss_value, 0.05, 0.15)
        self.target.freq_y = self.map_value(-liss_value, 0.05, 0.15)
        self.target.freq_diag = self.map_value(math.cos(t), 0.04, 0.12)
        
        # Draw the modulated plasma
        self.target.draw(t)
        
    def get_param_info(self) -> list:
        """Return parameter info showing both animations."""
        return [
            f"Mod: {self.modulation_strength:.1f}x",
            f"Liss→Plasma",
            f"Freq X: {self.target.freq_x:.2f}",
            f"Freq Y: {self.target.freq_y:.2f}"
        ]


class ScreenSaver:
    """Screen saver with multiple parametric animations."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True
        self.show_params = True  # Show parameter values
        self.show_help = False  # Help modal state

        # Save slot system (buttons 2-5 = slots 0-3)
        self.save_slots = {0: None, 1: None, 2: None, 3: None}
        self.button_press_times = {}  # Track when buttons were pressed
        self.previous_save_buttons = {2: False, 3: False, 4: False, 5: False}  # Track button states
        self.hold_threshold = 0.5  # Seconds to hold for save
        self.save_feedback = None  # Message to show when saving/loading
        self.save_feedback_time = 0  # Time when feedback was set

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
            # Composite animations (8-10)
            PlasmaLissajous(self.renderer),
            FluxSpiral(self.renderer),
            LissajousPlasma(self.renderer),
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
            # Composite animation names
            "Plasma → Lissajous",
            "Flux → Spiral",
            "Lissajous → Plasma",
        ]
        self.current_animation = 0
        self.speed_multiplier = 2.0  # Increased animation speed

    def get_param_descriptions(self):
        """Get parameter descriptions for current animation."""
        descriptions = {
            "Lissajous Curve": [
                "Freq X: Horizontal frequency (1-10)",
                "Freq Y: Vertical frequency (1-10)",
                "Phase: Curve shape offset (0-2π)",
                "Points: Smoothness/detail (100-1000)"
            ],
            "Spiral": [
                "Spirals: Number of arms (1-8)",
                "Speed: Rotation speed (0.1-5.0x)",
                "Tightness: Coil density (2-15)",
                "Scale: Overall size (0.2-0.8)"
            ],
            "Wave Circles": [
                "Circles: Number of rings (5-30)",
                "Amplitude: Wave height (0.5-8.0)",
                "Wave Freq: Oscillation rate (0.1-2.0)",
                "Spacing: Ring distance (1-6)"
            ],
            "Plasma": [
                "Freq X: Horizontal pattern (0.01-0.3)",
                "Freq Y: Vertical pattern (0.01-0.3)",
                "Freq Diag: Diagonal waves (0.01-0.3)",
                "Freq Rad: Radial pulses (0.01-0.3)"
            ],
            "Mandelbrot Zoomer": [
                "Zoom: Magnification level (0.1-1000x)",
                "Center X: Horizontal position (-2 to 1)",
                "Center Y: Vertical position (-1.5 to 1.5)",
                "Detail: Calculation depth (10-200)"
            ],
            "Fluid Lattice": [
                "Rain Rate: Drop frequency (0-1.5)",
                "Wave Speed: Propagation rate (0.05-1.0)",
                "Drop Power: Impact strength (3-20)",
                "Damping: Wave persistence (0.85-0.995)"
            ],
            "Particle Swarm": [
                "Particles: Swarm size (10-100)",
                "Speed: Movement rate (0.5-5.0)",
                "Cohesion: Attraction force (0-2.0)",
                "Separation: Repulsion force (0-3.0)"
            ],
            "Tunnel Vision": [
                "Depth Speed: Forward motion (0.1-5.0)",
                "Rotation: Spin rate (-2 to 2)",
                "Size: Tunnel diameter (0.3-3.0)",
                "Color Speed: Rainbow cycle (0.1-3.0)"
            ],
            "Plasma → Lissajous": [
                "Modulation: Strength (0.0-2.0)",
                "Plasma drives Lissajous frequencies",
                "Curve morphs with plasma waves",
                "Creates evolving patterns"
            ],
            "Flux → Spiral": [
                "Modulation: Strength (0.0-2.0)",
                "Fluid waves drive spiral rotation",
                "Spiral pulses with wave rhythm",
                "Energy-based motion"
            ],
            "Lissajous → Plasma": [
                "Modulation: Strength (0.0-2.0)",
                "Curve motion drives plasma colors",
                "Synchronized wave patterns",
                "Harmonic color shifts"
            ]
        }
        return descriptions.get(self.animation_names[self.current_animation], [])

    def save_parameters(self, slot: int):
        """Save current animation parameters to slot."""
        anim = self.animations[self.current_animation]
        if hasattr(anim, 'get_param_info'):
            # Store animation index and parameters
            param_values = {}
            # Extract actual values from the animation
            if hasattr(anim, 'a'):  # Lissajous
                param_values = {'a': anim.a, 'b': anim.b, 'delta': anim.delta, 'points': anim.points}
            elif hasattr(anim, 'num_spirals'):  # Spiral
                param_values = {'num_spirals': anim.num_spirals, 'rotation_speed': anim.rotation_speed,
                               'tightness': anim.tightness, 'radius_scale': anim.radius_scale}
            elif hasattr(anim, 'num_circles'):  # Wave Circles
                param_values = {'num_circles': anim.num_circles, 'wave_amplitude': anim.wave_amplitude,
                               'wave_frequency': anim.wave_frequency, 'spacing': anim.spacing}
            elif hasattr(anim, 'freq_x'):  # Plasma
                param_values = {'freq_x': anim.freq_x, 'freq_y': anim.freq_y,
                               'freq_diag': anim.freq_diag, 'freq_radial': anim.freq_radial}
            elif hasattr(anim, 'zoom'):  # Mandelbrot
                param_values = {'zoom': anim.zoom, 'center_x': anim.center_x,
                               'center_y': anim.center_y, 'max_iterations': anim.max_iterations}
            elif hasattr(anim, 'rain_rate'):  # Fluid Lattice
                param_values = {'rain_rate': anim.rain_rate, 'wave_speed': anim.wave_speed,
                               'drop_strength': anim.drop_strength, 'damping': anim.damping}
            elif hasattr(anim, 'num_particles'):  # Particle Swarm
                param_values = {'num_particles': anim.num_particles, 'speed': anim.speed,
                               'cohesion': anim.cohesion, 'separation': anim.separation}
            elif hasattr(anim, 'depth_speed'):  # Tunnel
                param_values = {'depth_speed': anim.depth_speed, 'rotation_speed': anim.rotation_speed,
                               'tunnel_size': anim.tunnel_size, 'color_cycle_speed': anim.color_cycle_speed}

            self.save_slots[slot] = {
                'animation_index': self.current_animation,
                'parameters': param_values
            }
            self.save_feedback = f"Saved to Slot {slot + 2}"
            self.save_feedback_time = time.time()

    def load_parameters(self, slot: int):
        """Load parameters from slot."""
        if self.save_slots[slot] is None:
            self.save_feedback = f"Slot {slot + 2} empty"
            self.save_feedback_time = time.time()
            return

        saved = self.save_slots[slot]
        # Switch to saved animation if different
        if saved['animation_index'] != self.current_animation:
            self.current_animation = saved['animation_index']

        # Restore parameters
        anim = self.animations[self.current_animation]
        params = saved['parameters']
        for key, value in params.items():
            if hasattr(anim, key):
                setattr(anim, key, value)

        self.save_feedback = f"Loaded Slot {slot + 2}"
        self.save_feedback_time = time.time()

    def apply_preset(self, animation_index: int, preset_name: str):
        """Apply a preset configuration to a specific animation mode.

        Args:
            animation_index: Index of the animation (0-7)
            preset_name: Name of the preset to apply

        Returns:
            bool: True if preset was applied successfully, False otherwise
        """
        preset_params = get_preset(animation_index, preset_name)
        if preset_params is None:
            return False

        # Switch to the animation if not already active
        if self.current_animation != animation_index:
            self.current_animation = animation_index

        # Apply parameters to the animation
        anim = self.animations[animation_index]
        for key, value in preset_params.items():
            if hasattr(anim, key):
                setattr(anim, key, value)

        self.save_feedback = f"Applied preset: {preset_name}"
        self.save_feedback_time = time.time()
        return True

    def run_preset_tour(self, mode: int, seconds_per_preset: int = 10):
        """Cycle through all presets for a single animation mode.

        Args:
            mode: Animation mode index (0-7)
            seconds_per_preset: How long to display each preset (default: 10 seconds)
        """
        if mode < 0 or mode >= len(self.animations):
            print(f"Invalid animation mode: {mode}. Must be 0-{len(self.animations)-1}")
            return

        preset_names = get_preset_names(mode)
        if not preset_names:
            print(f"No presets available for animation mode {mode}")
            return

        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            for preset_name in preset_names:
                # Apply the preset
                self.apply_preset(mode, preset_name)

                # Display the preset for the specified duration
                start_time = time.time()
                last_time = start_time

                while time.time() - start_time < seconds_per_preset:
                    current_time = time.time()
                    dt = current_time - last_time
                    last_time = current_time

                    # Draw and update
                    self.renderer.clear_buffer()
                    anim = self.animations[self.current_animation]
                    anim.draw(anim.t)

                    # Draw preset tour info
                    name = self.animation_names[self.current_animation]
                    self.renderer.draw_text(2, 1, f"Preset Tour: {name}", Color.BRIGHT_YELLOW)
                    self.renderer.draw_text(2, 2, f"Preset: {preset_name}", Color.BRIGHT_CYAN)

                    # Draw parameters
                    if hasattr(anim, 'get_param_info'):
                        param_info = anim.get_param_info()
                        for i, param in enumerate(param_info):
                            self.renderer.draw_text(2, 4 + i, param, Color.BRIGHT_GREEN)

                    # Draw progress bar
                    elapsed = time.time() - start_time
                    progress = elapsed / seconds_per_preset
                    bar_width = 40
                    filled = int(progress * bar_width)
                    bar = "[" + "=" * filled + " " * (bar_width - filled) + "]"
                    self.renderer.draw_text(2, 10, bar, Color.CYAN)

                    # Draw time remaining
                    remaining = seconds_per_preset - elapsed
                    time_text = f"Next preset in: {remaining:.1f}s"
                    self.renderer.draw_text(2, 11, time_text, Color.YELLOW)

                    # Draw exit info
                    self.renderer.draw_text(2, 13, "Press ESC/Q to exit tour", Color.RED)

                    self.renderer.render()
                    anim.update(dt * self.speed_multiplier)

                    # Check for exit
                    input_type = self.input_handler.get_input(timeout=0.01)
                    if input_type == InputType.QUIT:
                        return

                    time.sleep(0.016)  # ~60 FPS

        finally:
            self.renderer.exit_fullscreen()

    def draw_help_modal(self):
        """Draw help modal overlay."""
        # Calculate modal dimensions
        modal_width = 60
        modal_height = 14
        modal_x = (self.renderer.width - modal_width) // 2
        modal_y = (self.renderer.height - modal_height) // 2

        # Draw background box
        for y in range(modal_height):
            for x in range(modal_width):
                self.renderer.set_pixel(modal_x + x, modal_y + y, ' ' if y > 0 and y < modal_height-1 and x > 0 and x < modal_width-1 else '█', Color.BLUE)

        # Draw border
        self.renderer.draw_border(modal_x, modal_y, modal_width, modal_height, Color.BRIGHT_CYAN)

        # Draw title
        title = f" {self.animation_names[self.current_animation]} - Parameters "
        title_x = modal_x + (modal_width - len(title)) // 2
        self.renderer.draw_text(title_x, modal_y, title, Color.BRIGHT_YELLOW)

        # Draw parameter descriptions
        descriptions = self.get_param_descriptions()
        for i, desc in enumerate(descriptions):
            # Show which joystick direction controls this param
            controls = ["UP/DOWN", "LEFT/RIGHT", "UP-RIGHT/DOWN-LEFT", "UP-LEFT/DOWN-RIGHT"]
            control_text = f"{controls[i]}: {desc}"
            self.renderer.draw_text(modal_x + 2, modal_y + 3 + i * 2, control_text, Color.WHITE)

        # Draw instructions
        instructions = [
            "Press H again to close",
            "BTN0/1: Next/Prev | BTN2-5: Save/Load"
        ]
        for i, inst in enumerate(instructions):
            self.renderer.draw_text(modal_x + 2, modal_y + modal_height - 3 + i, inst, Color.CYAN)

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
        self.renderer.draw_text(self.renderer.width - 32, control_y, "H: Help", Color.BRIGHT_YELLOW)
        self.renderer.draw_text(self.renderer.width - 32, control_y + 1, "BTN0: Next  BTN1: Prev", Color.CYAN)
        self.renderer.draw_text(self.renderer.width - 32, control_y + 2, "BTN2-5: Save/Load (Hold/Tap)", Color.CYAN)
        self.renderer.draw_text(self.renderer.width - 32, control_y + 3, "ESC/Q/X: Exit", Color.CYAN)

        # Draw legend for slot colors
        legend_y = self.renderer.height - 3
        legend = "Green=Saved Yellow=Pressing Red=Saving"
        self.renderer.draw_text(self.renderer.width - len(legend) - 2, legend_y, legend, Color.WHITE)

        # Draw save slot indicators at bottom with press and hold states
        slot_y = self.renderer.height - 2
        slot_text = "Slots: "
        self.renderer.draw_text(2, slot_y, slot_text, Color.YELLOW)
        x_offset = 2 + len(slot_text)

        # Check current button states
        current_time = time.time()
        if self.input_handler.joystick_initialized:
            buttons = self.input_handler.get_joystick_buttons()
        else:
            buttons = {}

        for i in range(4):
            btn_id = i + 2
            slot_label = f"[{btn_id}]"

            # Determine color based on state
            is_pressed = buttons.get(btn_id, False)
            has_save = self.save_slots[i] is not None
            is_holding = btn_id in self.button_press_times

            # Color logic:
            # - Pressing (no hold yet): YELLOW
            # - Holding (progress to save): BRIGHT_YELLOW + progress bar
            # - Has save: BRIGHT_GREEN
            # - Empty: WHITE
            if is_pressed and is_holding:
                hold_duration = current_time - self.button_press_times[btn_id]
                if hold_duration >= self.hold_threshold:
                    # About to save (or just saved)
                    color = Color.BRIGHT_RED
                else:
                    # Holding, not there yet
                    color = Color.BRIGHT_YELLOW
                    # Draw progress bar
                    progress = int((hold_duration / self.hold_threshold) * 3)
                    progress_bar = "=" * progress
                    self.renderer.draw_text(x_offset + len(slot_label) + 1, slot_y, progress_bar, Color.YELLOW)
            elif has_save:
                color = Color.BRIGHT_GREEN
            else:
                color = Color.WHITE

            self.renderer.draw_text(x_offset, slot_y, slot_label, color)
            x_offset += len(slot_label) + 5  # Extra space for progress bar

        # Draw save/load feedback
        if self.save_feedback and time.time() - self.save_feedback_time < 2.0:
            feedback_x = (self.renderer.width - len(self.save_feedback)) // 2
            self.renderer.draw_text(feedback_x, self.renderer.height - 4, self.save_feedback, Color.BRIGHT_YELLOW)

        # Draw button press debug info (second row for status)
        if self.input_handler.joystick_initialized:
            status_y = self.renderer.height - 3
            status_parts = []
            for btn_id in [2, 3, 4, 5]:
                if btn_id in self.button_press_times:
                    hold_time = current_time - self.button_press_times[btn_id]
                    status_parts.append(f"BTN{btn_id}:{hold_time:.1f}s")
            if status_parts:
                status_text = " ".join(status_parts)
                self.renderer.draw_text(2, status_y, status_text, Color.CYAN)

        # Draw help modal (on top of everything)
        if self.show_help:
            self.draw_help_modal()

        self.renderer.render()

    def update(self, dt: float):
        """Update animation."""
        self.animations[self.current_animation].update(dt * self.speed_multiplier)

    def handle_input(self):
        """Handle user input and joystick directions for parameter control."""
        # Check for H key (help) and D key (drain for Fluid Lattice)
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)
            if key and key.lower() == 'h':
                self.show_help = not self.show_help
                time.sleep(0.2)  # Debounce
            elif key and key.lower() == 'd' and self.current_animation == 5:
                # Drain: multiply all values toward zero (like a global damping pulse)
                anim = self.animations[5]
                for y in range(anim.height):
                    for x in range(anim.width):
                        anim.current[y][x] *= 0.3  # Reduce all values by 70%
                        anim.previous[y][x] *= 0.3
            elif key and key.lower() == 'c' and self.current_animation == 5:
                # Full clear: reset the entire lattice
                anim = self.animations[5]
                for y in range(anim.height):
                    for x in range(anim.width):
                        anim.current[y][x] = 0.0
                        anim.previous[y][x] = 0.0

        input_type = self.input_handler.get_input(timeout=0.01)

        # Mode switching with buttons
        if input_type == InputType.SELECT:
            # Button 0: Next animation (forward)
            self.current_animation = (self.current_animation + 1) % len(self.animations)
            time.sleep(0.2)  # Debounce
        elif input_type == InputType.BACK:
            # Button 1: Previous animation (back)
            self.current_animation = (self.current_animation - 1) % len(self.animations)
            time.sleep(0.2)  # Debounce
        elif input_type == InputType.QUIT:
            # Keyboard ESC/Q or X: Exit
            self.running = False

        # Special handling for Mandelbrot zoom mode toggle (button 2)
        if self.input_handler.joystick_initialized and self.current_animation == 4:  # Mandelbrot is index 4
            pygame.event.pump()
            buttons = self.input_handler.get_joystick_buttons()

            # Check button 2 for zoom mode toggle (only for Mandelbrot)
            if not hasattr(self, '_last_btn2_state'):
                self._last_btn2_state = False

            btn2_pressed = buttons.get(2, False)
            if btn2_pressed and not self._last_btn2_state:
                # Toggle zoom mode on button press
                anim = self.animations[self.current_animation]
                if hasattr(anim, 'zoom_mode'):
                    anim.zoom_mode = not anim.zoom_mode
                    self.save_feedback = f"Zoom Mode: {'ON' if anim.zoom_mode else 'OFF'}"
                    self.save_feedback_time = time.time()
                    time.sleep(0.2)  # Debounce

            self._last_btn2_state = btn2_pressed

        # Save/Load system with buttons 2-5 (separate from main input to avoid conflicts)
        # Skip button 2 for Mandelbrot (used for zoom mode toggle)
        if self.input_handler.joystick_initialized:
            pygame.event.pump()  # Update joystick state
            buttons = self.input_handler.get_joystick_buttons()
            current_time = time.time()

            # Check buttons 2-5 (slots 0-3), but skip button 2 for Mandelbrot
            button_range = [3, 4, 5] if self.current_animation == 4 else [2, 3, 4, 5]
            for btn_id in button_range:
                if btn_id >= len(buttons):
                    continue

                slot = btn_id - 2
                is_pressed = buttons.get(btn_id, False)
                was_pressed = self.previous_save_buttons[btn_id]

                # Button just pressed - start tracking
                if is_pressed and not was_pressed:
                    self.button_press_times[btn_id] = current_time
                    self.save_feedback = f"Button {btn_id} pressed..."
                    self.save_feedback_time = current_time

                # Button just released - check if hold or tap
                elif not is_pressed and was_pressed:
                    if btn_id in self.button_press_times:
                        press_duration = current_time - self.button_press_times[btn_id]

                        if press_duration >= self.hold_threshold:
                            # Hold = Save
                            self.save_parameters(slot)
                        else:
                            # Quick tap = Load
                            self.load_parameters(slot)

                        del self.button_press_times[btn_id]
                        time.sleep(0.1)  # Debounce

                # Update previous state
                self.previous_save_buttons[btn_id] = is_pressed

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
