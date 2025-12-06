#!/usr/bin/env python3
"""Lissajous Particle Swarm - 3D Visualization.

A pure visual experience: particles following 3D Lissajous paths with
varying stability ratios. No text overlays - just mesmerizing motion.

Each particle orbits in 3D space where:
- X = sin(a·t + δx)
- Y = sin(b·t + δy)
- Z = sin(c·t + δz)

Stability varies from rational ratios (stable orbits) to irrational
ratios (chaotic, space-filling trajectories).

Usage:
    python -m atari_style.demos.visualizers.educational.lissajous_swarm -o swarm.gif
    python -m atari_style.demos.visualizers.educational.lissajous_swarm --duration 30 --fps 30 -o swarm_hq.gif
"""

import math
import random
from dataclasses import dataclass
from typing import Generator, List, Tuple

from PIL import Image

from .lissajous_terminal_gif import TerminalCanvas, render_gif


# =============================================================================
# PARTICLE SYSTEM
# =============================================================================

@dataclass
class Particle3D:
    """A particle following a 3D Lissajous trajectory."""
    # Frequency ratios (a:b:c)
    freq_x: float
    freq_y: float
    freq_z: float
    # Phase offsets
    phase_x: float
    phase_y: float
    phase_z: float
    # Visual properties
    color: str
    speed: float
    trail_length: int
    # Trail history (list of (x, y, z) tuples)
    trail: List[Tuple[float, float, float]] = None

    def __post_init__(self):
        if self.trail is None:
            self.trail = []

    def update(self, t: float) -> Tuple[float, float, float]:
        """Calculate position at time t and update trail."""
        x = math.sin(self.freq_x * t * self.speed + self.phase_x)
        y = math.sin(self.freq_y * t * self.speed + self.phase_y)
        z = math.sin(self.freq_z * t * self.speed + self.phase_z)

        self.trail.append((x, y, z))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        return x, y, z


# Stability presets: (freq_x, freq_y, freq_z, name)
STABLE_RATIOS = [
    (1.0, 1.0, 1.0),   # Sphere trace
    (1.0, 2.0, 1.0),   # Figure-8 in XY
    (1.0, 1.0, 2.0),   # Figure-8 in XZ
    (2.0, 3.0, 1.0),   # Trefoil variant
    (1.0, 2.0, 3.0),   # 3D knot
    (2.0, 3.0, 4.0),   # Complex stable
    (3.0, 4.0, 5.0),   # Higher harmonics
    (1.0, 2.0, 4.0),   # Octave stack
]

# Colors for the forest-desert palette
SWARM_COLORS = [
    'sage', 'moss', 'olive', 'sand', 'terracotta', 'amber', 'clay', 'dusk',
    'cyan', 'bright_cyan', 'white', 'bright_white',
]


def create_particle_swarm(num_particles: int = 60,
                          stability_bias: float = 0.5) -> List[Particle3D]:
    """Create a swarm of particles with varying stability.

    Args:
        num_particles: Number of particles in the swarm.
        stability_bias: 0.0 = all chaotic, 1.0 = all stable, 0.5 = mixed.

    Returns:
        List of Particle3D instances.
    """
    particles = []

    for i in range(num_particles):
        # Decide stability for this particle
        is_stable = random.random() < stability_bias

        if is_stable:
            # Pick a stable ratio
            base = random.choice(STABLE_RATIOS)
            # Add small perturbation for variety
            freq_x = base[0] + random.uniform(-0.05, 0.05)
            freq_y = base[1] + random.uniform(-0.05, 0.05)
            freq_z = base[2] + random.uniform(-0.05, 0.05)
        else:
            # Chaotic: use irrational-ish ratios
            freq_x = random.uniform(0.5, 4.0)
            freq_y = random.uniform(0.5, 4.0)
            freq_z = random.uniform(0.5, 4.0)
            # Ensure they're not accidentally rational
            if abs(freq_x - round(freq_x)) < 0.1:
                freq_x += 0.17
            if abs(freq_y - round(freq_y)) < 0.1:
                freq_y += 0.23

        # Random phases
        phase_x = random.uniform(0, 2 * math.pi)
        phase_y = random.uniform(0, 2 * math.pi)
        phase_z = random.uniform(0, 2 * math.pi)

        # Visual variety
        color = random.choice(SWARM_COLORS)
        speed = random.uniform(0.3, 1.5)
        trail_length = random.randint(15, 40)

        particles.append(Particle3D(
            freq_x=freq_x,
            freq_y=freq_y,
            freq_z=freq_z,
            phase_x=phase_x,
            phase_y=phase_y,
            phase_z=phase_z,
            color=color,
            speed=speed,
            trail_length=trail_length,
        ))

    return particles


# =============================================================================
# 3D PROJECTION
# =============================================================================

def project_3d_to_2d(x: float, y: float, z: float,
                     cx: int, cy: int,
                     scale_x: float, scale_y: float,
                     camera_distance: float = 3.0,
                     rotation_y: float = 0.0,
                     rotation_x: float = 0.0) -> Tuple[int, int, float]:
    """Project 3D point to 2D screen coordinates.

    Args:
        x, y, z: 3D coordinates in range [-1, 1].
        cx, cy: Screen center.
        scale_x, scale_y: Scale factors.
        camera_distance: Distance from camera (affects perspective).
        rotation_y: Y-axis rotation angle.
        rotation_x: X-axis rotation angle.

    Returns:
        (screen_x, screen_y, depth) tuple.
    """
    # Apply Y rotation (around vertical axis)
    cos_y = math.cos(rotation_y)
    sin_y = math.sin(rotation_y)
    x_rot = x * cos_y - z * sin_y
    z_rot = x * sin_y + z * cos_y

    # Apply X rotation (around horizontal axis)
    cos_x = math.cos(rotation_x)
    sin_x = math.sin(rotation_x)
    y_rot = y * cos_x - z_rot * sin_x
    z_final = y * sin_x + z_rot * cos_x

    # Perspective projection
    perspective = camera_distance / (camera_distance + z_final + 1.0)

    screen_x = int(cx + x_rot * scale_x * perspective)
    screen_y = int(cy + y_rot * scale_y * perspective)

    return screen_x, screen_y, z_final


# =============================================================================
# FRAME GENERATION
# =============================================================================

def generate_swarm_frames(canvas: TerminalCanvas, fps: int,
                          duration: float = 30.0,
                          num_particles: int = 60,
                          stability_bias: float = 0.6
                          ) -> Generator[Image.Image, None, None]:
    """Generate frames for the particle swarm visualization.

    Args:
        canvas: Terminal canvas for rendering.
        fps: Frames per second.
        duration: Total duration in seconds.
        num_particles: Number of particles.
        stability_bias: Ratio of stable to chaotic particles.

    Yields:
        PIL Image frames.
    """
    total_frames = int(duration * fps)

    # Create the swarm
    particles = create_particle_swarm(num_particles, stability_bias)

    # Scene parameters
    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale_x = canvas.cols // 3
    scale_y = canvas.rows // 3

    # Character set for depth
    chars_by_depth = ['·', '∘', '○', '●', '◉']

    for frame in range(total_frames):
        t = frame / fps

        canvas.clear()

        # Slowly rotate the view
        rotation_y = t * 0.3
        rotation_x = math.sin(t * 0.15) * 0.3

        # Collect all points with depth for z-sorting
        points = []

        for particle in particles:
            # Update particle position
            x, y, z = particle.update(t)

            # Project and add current position
            sx, sy, depth = project_3d_to_2d(
                x, y, z, cx, cy, scale_x, scale_y,
                camera_distance=2.5,
                rotation_y=rotation_y,
                rotation_x=rotation_x
            )
            points.append((depth, sx, sy, particle.color, 1.0, particle))

            # Add trail points
            for i, (tx, ty, tz) in enumerate(particle.trail[:-1]):
                trail_sx, trail_sy, trail_depth = project_3d_to_2d(
                    tx, ty, tz, cx, cy, scale_x, scale_y,
                    camera_distance=2.5,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )
                # Fade based on trail position
                intensity = (i + 1) / len(particle.trail)
                points.append((trail_depth, trail_sx, trail_sy,
                              particle.color, intensity * 0.7, None))

        # Sort by depth (far to near)
        points.sort(key=lambda p: p[0])

        # Render points
        for depth, sx, sy, color, intensity, particle in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            # Choose character based on depth and intensity
            depth_normalized = (depth + 1.5) / 3.0  # Normalize to 0-1
            depth_idx = int(depth_normalized * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if intensity > 0.8:
                char = chars_by_depth[-1]  # Brightest
            elif intensity > 0.5:
                char = chars_by_depth[max(depth_idx, 2)]
            elif intensity > 0.2:
                char = chars_by_depth[max(depth_idx, 1)]
            else:
                char = chars_by_depth[depth_idx]

            # Adjust color brightness based on depth
            if particle is not None:  # Current position - brightest
                render_color = 'bright_white' if depth > 0 else color
            else:
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


def generate_stability_journey_frames(canvas: TerminalCanvas, fps: int,
                                      duration: float = 45.0
                                      ) -> Generator[Image.Image, None, None]:
    """Generate a journey from chaos to stability and back.

    The visualization morphs between:
    - Chaotic swarm (irrational ratios)
    - Semi-stable (mixed)
    - Fully stable (harmonic ratios)

    Args:
        canvas: Terminal canvas.
        fps: Frames per second.
        duration: Total duration.

    Yields:
        PIL Image frames.
    """
    total_frames = int(duration * fps)

    # Create particles that will morph
    num_particles = 50

    # Base ratios for each particle (will interpolate to these)
    base_stable = []
    base_chaotic = []

    for _ in range(num_particles):
        # Stable target
        stable = random.choice(STABLE_RATIOS)
        base_stable.append((
            stable[0] + random.uniform(-0.02, 0.02),
            stable[1] + random.uniform(-0.02, 0.02),
            stable[2] + random.uniform(-0.02, 0.02),
        ))

        # Chaotic target
        base_chaotic.append((
            random.uniform(1.1, 3.7),
            random.uniform(1.3, 3.9),
            random.uniform(1.2, 3.5),
        ))

    # Particle properties
    phases = [(random.uniform(0, 2*math.pi),
               random.uniform(0, 2*math.pi),
               random.uniform(0, 2*math.pi)) for _ in range(num_particles)]
    speeds = [random.uniform(0.4, 1.2) for _ in range(num_particles)]
    colors = [random.choice(SWARM_COLORS) for _ in range(num_particles)]
    trail_lengths = [random.randint(20, 50) for _ in range(num_particles)]
    trails = [[] for _ in range(num_particles)]

    # Scene parameters
    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale_x = canvas.cols // 3
    scale_y = canvas.rows // 3

    chars_by_depth = ['·', '∘', '○', '●', '◉']

    for frame in range(total_frames):
        t = frame / fps
        progress = frame / total_frames

        # Stability oscillates: chaos → stable → chaos
        # Use a smooth wave that goes 0 → 1 → 0
        stability = math.sin(progress * math.pi) ** 2

        canvas.clear()

        # Slowly rotate
        rotation_y = t * 0.25
        rotation_x = math.sin(t * 0.12) * 0.25

        points = []

        for i in range(num_particles):
            # Interpolate frequencies based on stability
            fx = base_chaotic[i][0] + stability * (base_stable[i][0] - base_chaotic[i][0])
            fy = base_chaotic[i][1] + stability * (base_stable[i][1] - base_chaotic[i][1])
            fz = base_chaotic[i][2] + stability * (base_stable[i][2] - base_chaotic[i][2])

            # Calculate position
            anim_t = t * speeds[i]
            x = math.sin(fx * anim_t + phases[i][0])
            y = math.sin(fy * anim_t + phases[i][1])
            z = math.sin(fz * anim_t + phases[i][2])

            # Update trail
            trails[i].append((x, y, z))
            if len(trails[i]) > trail_lengths[i]:
                trails[i].pop(0)

            # Project current position
            sx, sy, depth = project_3d_to_2d(
                x, y, z, cx, cy, scale_x, scale_y,
                camera_distance=2.5,
                rotation_y=rotation_y,
                rotation_x=rotation_x
            )
            points.append((depth, sx, sy, colors[i], 1.0, True))

            # Project trail
            for j, (tx, ty, tz) in enumerate(trails[i][:-1]):
                tsx, tsy, tdepth = project_3d_to_2d(
                    tx, ty, tz, cx, cy, scale_x, scale_y,
                    camera_distance=2.5,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )
                intensity = (j + 1) / len(trails[i])
                points.append((tdepth, tsx, tsy, colors[i], intensity * 0.6, False))

        # Sort and render
        points.sort(key=lambda p: p[0])

        for depth, sx, sy, color, intensity, is_head in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            depth_norm = (depth + 1.5) / 3.0
            depth_idx = int(depth_norm * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if is_head:
                char = '●'
                render_color = 'bright_white' if depth > 0.3 else color
            elif intensity > 0.6:
                char = chars_by_depth[max(depth_idx, 2)]
                render_color = color
            elif intensity > 0.3:
                char = chars_by_depth[max(depth_idx, 1)]
                render_color = color
            else:
                char = chars_by_depth[depth_idx]
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


# =============================================================================
# SPHERICAL HARMONICS - Wave patterns on a sphere
# =============================================================================

def generate_sphere_harmonics_frames(canvas: TerminalCanvas, fps: int,
                                     duration: float = 45.0,
                                     num_particles: int = 80
                                     ) -> Generator[Image.Image, None, None]:
    """Generate particles on a sphere with harmonic wave distortions.

    Particles are distributed on a sphere surface, with the radius
    modulated by spherical harmonic-like functions.
    """
    total_frames = int(duration * fps)

    # Distribute particles on sphere using golden spiral
    particles = []
    golden_ratio = (1 + math.sqrt(5)) / 2

    for i in range(num_particles):
        # Golden spiral distribution
        theta = 2 * math.pi * i / golden_ratio
        phi = math.acos(1 - 2 * (i + 0.5) / num_particles)

        # Harmonic parameters for this particle
        l = random.randint(1, 4)  # degree
        m = random.randint(-l, l)  # order

        particles.append({
            'theta': theta,
            'phi': phi,
            'l': l,
            'm': m,
            'speed': random.uniform(0.5, 1.5),
            'color': random.choice(SWARM_COLORS),
            'trail': [],
            'trail_length': random.randint(15, 35),
        })

    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale = min(canvas.cols // 3, canvas.rows // 2)

    chars_by_depth = ['·', '∘', '○', '●', '◉']

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Slowly rotate view
        rotation_y = t * 0.2
        rotation_x = math.sin(t * 0.1) * 0.3

        # Wave amplitude oscillates
        wave_amp = 0.3 * math.sin(t * 0.5) + 0.2

        points = []

        for p in particles:
            # Spherical harmonic-like distortion
            # Y_l^m approximation: modulate radius based on theta, phi
            harmonic = math.cos(p['l'] * p['phi']) * math.cos(p['m'] * p['theta'] + t * p['speed'])
            radius = 1.0 + wave_amp * harmonic

            # Convert to Cartesian
            x = radius * math.sin(p['phi']) * math.cos(p['theta'] + t * 0.3 * p['speed'])
            y = radius * math.sin(p['phi']) * math.sin(p['theta'] + t * 0.3 * p['speed'])
            z = radius * math.cos(p['phi'])

            # Update trail
            p['trail'].append((x, y, z))
            if len(p['trail']) > p['trail_length']:
                p['trail'].pop(0)

            # Project
            sx, sy, depth = project_3d_to_2d(
                x, y, z, cx, cy, scale, scale * 0.6,
                camera_distance=3.0,
                rotation_y=rotation_y,
                rotation_x=rotation_x
            )
            points.append((depth, sx, sy, p['color'], 1.0, True))

            # Trail
            for j, (tx, ty, tz) in enumerate(p['trail'][:-1]):
                tsx, tsy, td = project_3d_to_2d(
                    tx, ty, tz, cx, cy, scale, scale * 0.6,
                    camera_distance=3.0,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )
                intensity = (j + 1) / len(p['trail'])
                points.append((td, tsx, tsy, p['color'], intensity * 0.5, False))

        # Sort and render
        points.sort(key=lambda pt: pt[0])

        for depth, sx, sy, color, intensity, is_head in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            depth_norm = (depth + 1.5) / 3.0
            depth_idx = int(depth_norm * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if is_head:
                char = '●'
                render_color = 'bright_white' if depth > 0.2 else color
            elif intensity > 0.5:
                char = chars_by_depth[max(depth_idx, 2)]
                render_color = color
            else:
                char = chars_by_depth[depth_idx]
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


# =============================================================================
# TORUS KNOTS - Particles following knot paths on a torus
# =============================================================================

def generate_torus_knots_frames(canvas: TerminalCanvas, fps: int,
                                duration: float = 45.0,
                                num_knots: int = 5
                                ) -> Generator[Image.Image, None, None]:
    """Generate torus knot patterns.

    A (p,q) torus knot winds p times around the torus hole and
    q times through the hole. Different p:q ratios create different knots.
    """
    total_frames = int(duration * fps)

    # Define several torus knots with different (p, q) parameters
    knot_params = [
        (2, 3),   # Trefoil knot
        (3, 5),   # Cinquefoil
        (2, 5),   # Solomon's seal
        (3, 7),   # 7-crossing knot
        (4, 5),   # Complex knot
        (2, 7),   # 7-turn knot
        (5, 7),   # High complexity
        (3, 4),   # (3,4) torus knot
    ]

    # Create particles for each knot
    knots = []
    for i in range(num_knots):
        p, q = knot_params[i % len(knot_params)]
        knots.append({
            'p': p,
            'q': q,
            'phase': random.uniform(0, 2 * math.pi),
            'speed': random.uniform(0.3, 0.8),
            'color': SWARM_COLORS[i % len(SWARM_COLORS)],
            'trail': [],
            'trail_length': 60,
            'R': 0.7,  # Major radius
            'r': 0.3,  # Minor radius
        })

    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale = min(canvas.cols // 3, canvas.rows // 2)

    chars_by_depth = ['·', '∘', '○', '●', '◉']

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        rotation_y = t * 0.15
        rotation_x = 0.4 + math.sin(t * 0.08) * 0.2

        points = []

        for knot in knots:
            p, q = knot['p'], knot['q']
            R, r = knot['R'], knot['r']

            # Parameter along the knot
            u = t * knot['speed'] + knot['phase']

            # Torus knot parametric equations
            x = (R + r * math.cos(q * u)) * math.cos(p * u)
            y = (R + r * math.cos(q * u)) * math.sin(p * u)
            z = r * math.sin(q * u)

            # Update trail
            knot['trail'].append((x, y, z))
            if len(knot['trail']) > knot['trail_length']:
                knot['trail'].pop(0)

            # Project head
            sx, sy, depth = project_3d_to_2d(
                x, y, z, cx, cy, scale, scale * 0.6,
                camera_distance=2.5,
                rotation_y=rotation_y,
                rotation_x=rotation_x
            )
            points.append((depth, sx, sy, knot['color'], 1.0, True))

            # Project trail with color gradient
            for j, (tx, ty, tz) in enumerate(knot['trail']):
                tsx, tsy, td = project_3d_to_2d(
                    tx, ty, tz, cx, cy, scale, scale * 0.6,
                    camera_distance=2.5,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )
                intensity = (j + 1) / len(knot['trail'])
                points.append((td, tsx, tsy, knot['color'], intensity * 0.8, False))

        # Sort and render
        points.sort(key=lambda pt: pt[0])

        for depth, sx, sy, color, intensity, is_head in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            depth_norm = (depth + 1.5) / 3.0
            depth_idx = int(depth_norm * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if is_head:
                char = '◉'
                render_color = 'bright_white'
            elif intensity > 0.7:
                char = '●'
                render_color = color
            elif intensity > 0.4:
                char = '○'
                render_color = color
            else:
                char = chars_by_depth[depth_idx]
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


# =============================================================================
# DOUBLE HELIX - DNA-like interweaving spirals
# =============================================================================

def generate_helix_frames(canvas: TerminalCanvas, fps: int,
                          duration: float = 45.0,
                          num_helices: int = 3
                          ) -> Generator[Image.Image, None, None]:
    """Generate interweaving helical patterns.

    Multiple helices spiral around a common axis, with connecting
    rungs like DNA structure.
    """
    total_frames = int(duration * fps)

    # Create helices
    helices = []
    for i in range(num_helices):
        # Each helix pair (like DNA double helix)
        phase_offset = (2 * math.pi / num_helices) * i
        helices.append({
            'phase': phase_offset,
            'color1': SWARM_COLORS[i * 2 % len(SWARM_COLORS)],
            'color2': SWARM_COLORS[(i * 2 + 1) % len(SWARM_COLORS)],
            'radius': 0.5 + i * 0.15,
            'pitch': 0.3 + i * 0.1,
            'speed': 0.8 - i * 0.1,
            'particles1': [],
            'particles2': [],
            'trail_length': 40,
        })

    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale_x = canvas.cols // 4
    scale_y = canvas.rows // 3

    chars_by_depth = ['·', '∘', '○', '●', '◉']

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        rotation_y = t * 0.2
        rotation_x = 0.3

        points = []

        for helix in helices:
            # Two strands per helix (like DNA)
            for strand_idx, (particles, color) in enumerate([
                (helix['particles1'], helix['color1']),
                (helix['particles2'], helix['color2'])
            ]):
                # Phase offset between the two strands
                strand_phase = strand_idx * math.pi + helix['phase']

                # Position along helix
                u = t * helix['speed']

                # Helix parametric equations
                x = helix['radius'] * math.cos(u * 4 + strand_phase)
                z = helix['radius'] * math.sin(u * 4 + strand_phase)
                y = math.sin(u * helix['pitch'] * 2) * 0.8  # Oscillate up/down

                # Store in trail
                particles.append((x, y, z))
                if len(particles) > helix['trail_length']:
                    particles.pop(0)

                # Project head
                sx, sy, depth = project_3d_to_2d(
                    x, y, z, cx, cy, scale_x, scale_y,
                    camera_distance=2.5,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )
                points.append((depth, sx, sy, color, 1.0, True))

                # Project trail
                for j, (tx, ty, tz) in enumerate(particles[:-1]):
                    tsx, tsy, td = project_3d_to_2d(
                        tx, ty, tz, cx, cy, scale_x, scale_y,
                        camera_distance=2.5,
                        rotation_y=rotation_y,
                        rotation_x=rotation_x
                    )
                    intensity = (j + 1) / len(particles)
                    points.append((td, tsx, tsy, color, intensity * 0.7, False))

            # Draw connecting rungs between strands (every few positions)
            if len(helix['particles1']) > 5 and len(helix['particles2']) > 5:
                for j in range(0, min(len(helix['particles1']), len(helix['particles2'])), 5):
                    p1 = helix['particles1'][j]
                    p2 = helix['particles2'][j]

                    # Interpolate between the two points
                    for k in range(3):
                        frac = k / 2
                        rx = p1[0] + frac * (p2[0] - p1[0])
                        ry = p1[1] + frac * (p2[1] - p1[1])
                        rz = p1[2] + frac * (p2[2] - p1[2])

                        rsx, rsy, rd = project_3d_to_2d(
                            rx, ry, rz, cx, cy, scale_x, scale_y,
                            camera_distance=2.5,
                            rotation_y=rotation_y,
                            rotation_x=rotation_x
                        )
                        points.append((rd, rsx, rsy, 'white', 0.3, False))

        # Sort and render
        points.sort(key=lambda pt: pt[0])

        for depth, sx, sy, color, intensity, is_head in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            depth_norm = (depth + 1.5) / 3.0
            depth_idx = int(depth_norm * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if is_head:
                char = '●'
                render_color = 'bright_white' if depth > 0.2 else color
            elif intensity > 0.5:
                char = chars_by_depth[max(depth_idx, 2)]
                render_color = color
            else:
                char = chars_by_depth[depth_idx]
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


# =============================================================================
# BREATHING SPHERE - Pulsating sphere with Lissajous surface waves
# =============================================================================

def generate_breathing_sphere_frames(canvas: TerminalCanvas, fps: int,
                                     duration: float = 45.0,
                                     num_particles: int = 120
                                     ) -> Generator[Image.Image, None, None]:
    """Generate a breathing sphere with surface wave patterns.

    Particles on sphere surface with radius modulated by
    multiple Lissajous-like wave patterns.
    """
    total_frames = int(duration * fps)

    # Distribute particles on sphere
    particles = []
    golden_ratio = (1 + math.sqrt(5)) / 2

    for i in range(num_particles):
        theta = 2 * math.pi * i / golden_ratio
        phi = math.acos(1 - 2 * (i + 0.5) / num_particles)

        particles.append({
            'base_theta': theta,
            'base_phi': phi,
            'color': random.choice(SWARM_COLORS),
            'trail': [],
            'trail_length': random.randint(10, 25),
        })

    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale = min(canvas.cols // 3, canvas.rows // 2)

    chars_by_depth = ['·', '∘', '○', '●', '◉']

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        rotation_y = t * 0.25
        rotation_x = 0.3 + math.sin(t * 0.15) * 0.2

        # Breathing amplitude
        breath = 0.15 * math.sin(t * 1.5) + 1.0

        # Wave patterns on surface
        wave1_amp = 0.1 * math.sin(t * 0.7)
        wave2_amp = 0.08 * math.sin(t * 1.1)

        points = []

        for p in particles:
            theta = p['base_theta']
            phi = p['base_phi']

            # Multiple wave distortions
            wave1 = wave1_amp * math.sin(3 * theta + 2 * phi + t * 2)
            wave2 = wave2_amp * math.sin(5 * theta - 3 * phi + t * 1.5)
            wave3 = 0.05 * math.sin(2 * theta + 4 * phi - t)

            radius = breath + wave1 + wave2 + wave3

            # Convert to Cartesian
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)

            # Update trail
            p['trail'].append((x, y, z))
            if len(p['trail']) > p['trail_length']:
                p['trail'].pop(0)

            # Project
            sx, sy, depth = project_3d_to_2d(
                x, y, z, cx, cy, scale, scale * 0.6,
                camera_distance=3.0,
                rotation_y=rotation_y,
                rotation_x=rotation_x
            )
            points.append((depth, sx, sy, p['color'], 1.0, True))

            # Trail
            for j, (tx, ty, tz) in enumerate(p['trail'][:-1]):
                tsx, tsy, td = project_3d_to_2d(
                    tx, ty, tz, cx, cy, scale, scale * 0.6,
                    camera_distance=3.0,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )
                intensity = (j + 1) / len(p['trail'])
                points.append((td, tsx, tsy, p['color'], intensity * 0.4, False))

        # Sort and render
        points.sort(key=lambda pt: pt[0])

        for depth, sx, sy, color, intensity, is_head in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            depth_norm = (depth + 1.5) / 3.0
            depth_idx = int(depth_norm * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if is_head:
                char = '●' if depth > 0 else '○'
                render_color = color
            elif intensity > 0.5:
                char = chars_by_depth[max(depth_idx, 1)]
                render_color = color
            else:
                char = chars_by_depth[depth_idx]
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


# =============================================================================
# TORUS KNOTS SHOWCASE - Deep dive into knot mathematics
# =============================================================================

# Named torus knots with their (p,q) parameters
NAMED_KNOTS = [
    (2, 3, 'trefoil', ['sage', 'moss', 'olive']),
    (2, 5, 'solomon', ['sand', 'amber', 'terracotta']),
    (3, 5, 'cinquefoil', ['cyan', 'bright_cyan', 'white']),
    (3, 7, 'septafoil', ['terracotta', 'clay', 'dusk']),
    (2, 7, 'seven_twist', ['moss', 'sage', 'sand']),
    (4, 5, 'complex', ['amber', 'sand', 'bright_white']),
    (5, 7, 'high_order', ['olive', 'moss', 'clay']),
    (3, 4, 'three_four', ['dusk', 'terracotta', 'amber']),
]


def generate_torus_showcase_frames(canvas: TerminalCanvas, fps: int,
                                   duration: float = 60.0
                                   ) -> Generator[Image.Image, None, None]:
    """Generate a showcase of torus knots, one at a time with full trails.

    Each knot is shown with enough time to trace its complete path,
    then morphs into the next.
    """
    total_frames = int(duration * fps)

    # Time per knot (with transition)
    num_knots = len(NAMED_KNOTS)
    time_per_knot = duration / num_knots
    frames_per_knot = int(time_per_knot * fps)
    transition_frames = int(fps * 1.5)  # 1.5 second transitions

    cx = canvas.cols // 2
    cy = canvas.rows // 2
    # Stretch wider in X, taller in Y
    scale_x = canvas.cols // 2.0  # Wider
    scale_y = canvas.rows // 1.8  # Taller

    # Torus parameters
    R = 0.7  # Major radius
    r = 0.28  # Minor radius

    chars_by_depth = ['·', '∘', '○', '●', '◉']

    # Track multiple points along each knot for fuller visualization
    num_tracers = 8  # More particles tracing the knot

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Determine current and next knot
        knot_idx = min(int(frame / frames_per_knot), num_knots - 1)
        next_knot_idx = min(knot_idx + 1, num_knots - 1)

        frame_in_knot = frame % frames_per_knot
        knot_progress = frame_in_knot / frames_per_knot

        # Current knot params
        p, q, name, colors = NAMED_KNOTS[knot_idx]

        # Check if we're in transition
        in_transition = frame_in_knot > (frames_per_knot - transition_frames) and knot_idx < num_knots - 1
        if in_transition:
            trans_progress = (frame_in_knot - (frames_per_knot - transition_frames)) / transition_frames
            trans_ease = 0.5 - 0.5 * math.cos(trans_progress * math.pi)

            next_p, next_q, next_name, next_colors = NAMED_KNOTS[next_knot_idx]
            # Interpolate p and q
            curr_p = p + (next_p - p) * trans_ease
            curr_q = q + (next_q - q) * trans_ease
        else:
            curr_p, curr_q = float(p), float(q)

        # Slow rotation
        rotation_y = t * 0.25
        rotation_x = 0.35 + math.sin(t * 0.1) * 0.15

        points = []

        # Draw the full knot path (static outline)
        path_points = 600
        for i in range(path_points):
            u = (i / path_points) * 2 * math.pi * max(curr_p, curr_q)

            x = (R + r * math.cos(curr_q * u)) * math.cos(curr_p * u)
            y = (R + r * math.cos(curr_q * u)) * math.sin(curr_p * u)
            z = r * math.sin(curr_q * u)

            sx, sy, depth = project_3d_to_2d(
                x, y, z, cx, cy, scale_x, scale_y,
                camera_distance=2.8,
                rotation_y=rotation_y,
                rotation_x=rotation_x
            )

            if 0 <= sx < canvas.cols and 0 <= sy < canvas.rows:
                # Color by position along knot
                color_idx = int((i / path_points) * len(colors)) % len(colors)
                points.append((depth, sx, sy, colors[color_idx], 0.4, False))

        # Draw multiple tracers with long trails
        for tracer in range(num_tracers):
            tracer_offset = (tracer / num_tracers) * 2 * math.pi * max(curr_p, curr_q)
            trail_length = 60  # Slightly shorter trails with more tracers

            for trail_i in range(trail_length):
                # Position along the knot
                u = t * 0.8 + tracer_offset - trail_i * 0.025

                x = (R + r * math.cos(curr_q * u)) * math.cos(curr_p * u)
                y = (R + r * math.cos(curr_q * u)) * math.sin(curr_p * u)
                z = r * math.sin(curr_q * u)

                sx, sy, depth = project_3d_to_2d(
                    x, y, z, cx, cy, scale_x, scale_y,
                    camera_distance=2.8,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )

                if 0 <= sx < canvas.cols and 0 <= sy < canvas.rows:
                    intensity = 1.0 - (trail_i / trail_length)
                    is_head = trail_i == 0
                    color = 'bright_white' if is_head else colors[tracer % len(colors)]
                    points.append((depth, sx, sy, color, intensity, is_head))

        # Sort by depth and render
        points.sort(key=lambda pt: pt[0])

        for depth, sx, sy, color, intensity, is_head in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            depth_norm = (depth + 1.5) / 3.0
            depth_idx = int(depth_norm * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if is_head:
                char = '◉'
                render_color = 'bright_white'
            elif intensity > 0.7:
                char = '●'
                render_color = color
            elif intensity > 0.4:
                char = '○'
                render_color = color
            elif intensity > 0.2:
                char = '∘'
                render_color = color
            else:
                char = '·'
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


# =============================================================================
# CHAOS COMPILATION - Dynamic morphing through all patterns
# =============================================================================

def generate_chaos_compilation_frames(canvas: TerminalCanvas, fps: int,
                                       duration: float = 120.0,
                                       num_particles: int = 80
                                       ) -> Generator[Image.Image, None, None]:
    """Generate a continuous journey through all 3D harmonic patterns.

    Smoothly morphs between patterns with chaotic interludes and
    random parameter explosions.
    """
    total_frames = int(duration * fps)

    # Initialize particles with all the properties we'll morph
    particles = []
    golden_ratio = (1 + math.sqrt(5)) / 2

    for i in range(num_particles):
        # Base spherical distribution
        theta = 2 * math.pi * i / golden_ratio
        phi = math.acos(1 - 2 * (i + 0.5) / num_particles)

        particles.append({
            # Position state
            'x': 0.0, 'y': 0.0, 'z': 0.0,
            # Spherical base
            'base_theta': theta,
            'base_phi': phi,
            # Lissajous frequencies (morphable)
            'freq_x': random.uniform(1.0, 3.0),
            'freq_y': random.uniform(1.0, 3.0),
            'freq_z': random.uniform(1.0, 3.0),
            # Phases
            'phase_x': random.uniform(0, 2 * math.pi),
            'phase_y': random.uniform(0, 2 * math.pi),
            'phase_z': random.uniform(0, 2 * math.pi),
            # Harmonic params
            'l': random.randint(1, 4),
            'm': random.randint(-3, 3),
            # Torus params
            'torus_p': random.choice([2, 3, 4, 5]),
            'torus_q': random.choice([3, 5, 7]),
            # Visual
            'color': random.choice(SWARM_COLORS),
            'speed': random.uniform(0.3, 1.2),
            'trail': [],
            'trail_length': random.randint(20, 50),
        })

    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale = min(canvas.cols // 3, canvas.rows // 2)

    chars_by_depth = ['·', '∘', '○', '●', '◉']

    # Define the journey phases (what pattern to emphasize)
    # Each phase: (start_time, end_time, pattern_type, chaos_level)
    phases = [
        (0.0, 0.08, 'sphere', 0.0),        # Start with sphere
        (0.08, 0.12, 'chaos', 0.8),        # Explode to chaos
        (0.12, 0.22, 'lissajous', 0.2),    # Settle into lissajous swarm
        (0.22, 0.26, 'chaos', 1.0),        # Full chaos burst
        (0.26, 0.36, 'torus', 0.1),        # Torus knots emerge
        (0.36, 0.40, 'random', 0.6),       # Random parameters
        (0.40, 0.50, 'helix', 0.15),       # Helix patterns
        (0.50, 0.54, 'chaos', 0.9),        # Chaos again
        (0.54, 0.64, 'breathing', 0.1),    # Breathing sphere
        (0.64, 0.68, 'random', 0.7),       # Random explosion
        (0.68, 0.78, 'sphere', 0.2),       # Back to sphere harmonics
        (0.78, 0.82, 'chaos', 1.0),        # Final chaos
        (0.82, 0.92, 'convergence', 0.0),  # Everything converges
        (0.92, 1.0, 'sphere', 0.0),        # Peaceful end
    ]

    # Random events that can trigger mid-phase
    last_random_event = 0
    random_event_cooldown = fps * 3  # 3 seconds between events

    for frame in range(total_frames):
        t = frame / fps
        progress = frame / total_frames

        canvas.clear()

        # Find current phase
        current_phase = phases[-1]
        for phase in phases:
            if phase[0] <= progress < phase[1]:
                current_phase = phase
                break

        phase_start, phase_end, pattern_type, base_chaos = current_phase
        phase_progress = (progress - phase_start) / (phase_end - phase_start)
        phase_progress = max(0, min(1, phase_progress))

        # Smooth transition easing
        ease = 0.5 - 0.5 * math.cos(phase_progress * math.pi)

        # Random events inject chaos
        chaos_boost = 0.0
        if frame - last_random_event > random_event_cooldown:
            if random.random() < 0.02:  # 2% chance per frame
                chaos_boost = random.uniform(0.3, 0.8)
                last_random_event = frame
                # Randomize some particle params
                for p in random.sample(particles, len(particles) // 3):
                    p['freq_x'] = random.uniform(0.5, 5.0)
                    p['freq_y'] = random.uniform(0.5, 5.0)
                    p['freq_z'] = random.uniform(0.5, 5.0)

        chaos_level = min(1.0, base_chaos + chaos_boost * math.exp(-(frame - last_random_event) / (fps * 0.5)))

        # Camera movement
        rotation_y = t * 0.2 + math.sin(t * 0.3) * 0.3
        rotation_x = 0.3 + math.sin(t * 0.15) * 0.25

        # Add camera shake during chaos
        if chaos_level > 0.5:
            rotation_y += random.uniform(-0.1, 0.1) * chaos_level
            rotation_x += random.uniform(-0.05, 0.05) * chaos_level

        points = []

        for p in particles:
            # Calculate position based on current pattern blend
            if pattern_type == 'sphere' or pattern_type == 'breathing':
                # Spherical harmonics / breathing
                theta = p['base_theta']
                phi = p['base_phi']

                # Harmonic distortion
                wave_amp = 0.25 * math.sin(t * 0.5)
                harmonic = math.cos(p['l'] * phi) * math.cos(p['m'] * theta + t * p['speed'])

                # Breathing
                breath = 0.15 * math.sin(t * 1.5) + 1.0 if pattern_type == 'breathing' else 1.0
                radius = breath + wave_amp * harmonic

                x = radius * math.sin(phi) * math.cos(theta + t * 0.2 * p['speed'])
                y = radius * math.sin(phi) * math.sin(theta + t * 0.2 * p['speed'])
                z = radius * math.cos(phi)

            elif pattern_type == 'lissajous':
                # 3D Lissajous
                anim_t = t * p['speed']
                x = math.sin(p['freq_x'] * anim_t + p['phase_x'])
                y = math.sin(p['freq_y'] * anim_t + p['phase_y'])
                z = math.sin(p['freq_z'] * anim_t + p['phase_z'])

            elif pattern_type == 'torus':
                # Torus knot
                u = t * p['speed'] * 0.5 + p['phase_x']
                R, r = 0.7, 0.3
                pp, qq = p['torus_p'], p['torus_q']
                x = (R + r * math.cos(qq * u)) * math.cos(pp * u)
                y = (R + r * math.cos(qq * u)) * math.sin(pp * u)
                z = r * math.sin(qq * u)

            elif pattern_type == 'helix':
                # Helix
                u = t * p['speed']
                helix_r = 0.5 + (p['l'] % 3) * 0.15
                x = helix_r * math.cos(u * 4 + p['phase_x'])
                z = helix_r * math.sin(u * 4 + p['phase_x'])
                y = math.sin(u * 0.5) * 0.8

            elif pattern_type == 'chaos' or pattern_type == 'random':
                # Chaotic movement - blend all patterns with noise
                anim_t = t * p['speed'] * 2
                noise_x = math.sin(anim_t * p['freq_x'] * 1.7 + p['phase_x'])
                noise_y = math.sin(anim_t * p['freq_y'] * 2.3 + p['phase_y'])
                noise_z = math.sin(anim_t * p['freq_z'] * 1.9 + p['phase_z'])

                # Add high-frequency jitter
                jitter = 0.3 * chaos_level
                x = noise_x + random.uniform(-jitter, jitter)
                y = noise_y + random.uniform(-jitter, jitter)
                z = noise_z + random.uniform(-jitter, jitter)

            elif pattern_type == 'convergence':
                # Everything slowly converges to center then expands to sphere
                target_theta = p['base_theta']
                target_phi = p['base_phi']

                # Converge then expand
                if phase_progress < 0.5:
                    # Converge to center
                    conv = 1.0 - (phase_progress * 2)
                    radius = conv * 0.1
                else:
                    # Expand to sphere
                    radius = (phase_progress - 0.5) * 2

                x = radius * math.sin(target_phi) * math.cos(target_theta)
                y = radius * math.sin(target_phi) * math.sin(target_theta)
                z = radius * math.cos(target_phi)

            else:
                x, y, z = 0, 0, 0

            # Add chaos perturbation
            if chaos_level > 0:
                x += random.uniform(-0.2, 0.2) * chaos_level
                y += random.uniform(-0.2, 0.2) * chaos_level
                z += random.uniform(-0.2, 0.2) * chaos_level

            # Smooth the position
            smooth = 0.3
            p['x'] = p['x'] * (1 - smooth) + x * smooth
            p['y'] = p['y'] * (1 - smooth) + y * smooth
            p['z'] = p['z'] * (1 - smooth) + z * smooth

            # Update trail
            p['trail'].append((p['x'], p['y'], p['z']))
            if len(p['trail']) > p['trail_length']:
                p['trail'].pop(0)

            # Project
            sx, sy, depth = project_3d_to_2d(
                p['x'], p['y'], p['z'], cx, cy, scale, scale * 0.6,
                camera_distance=2.5,
                rotation_y=rotation_y,
                rotation_x=rotation_x
            )
            points.append((depth, sx, sy, p['color'], 1.0, True))

            # Trail
            for j, (tx, ty, tz) in enumerate(p['trail'][:-1]):
                tsx, tsy, td = project_3d_to_2d(
                    tx, ty, tz, cx, cy, scale, scale * 0.6,
                    camera_distance=2.5,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )
                intensity = (j + 1) / len(p['trail'])
                points.append((td, tsx, tsy, p['color'], intensity * 0.6, False))

        # Sort and render
        points.sort(key=lambda pt: pt[0])

        for depth, sx, sy, color, intensity, is_head in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            depth_norm = (depth + 1.5) / 3.0
            depth_idx = int(depth_norm * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if is_head:
                # Brighter during chaos
                if chaos_level > 0.5:
                    char = '◉' if random.random() < chaos_level else '●'
                else:
                    char = '●'
                render_color = 'bright_white' if depth > 0.2 else color
            elif intensity > 0.6:
                char = chars_by_depth[max(depth_idx, 2)]
                render_color = color
            elif intensity > 0.3:
                char = chars_by_depth[max(depth_idx, 1)]
                render_color = color
            else:
                char = chars_by_depth[depth_idx]
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


# =============================================================================
# NEON SEAMLESS LOOPS - VJ-style looping backgrounds
# =============================================================================

# Neon palette definitions for different loop variations
NEON_PALETTES = {
    'electric_blue': ['electric_blue', 'neon_blue', 'ice_blue', 'bright_cyan'],
    'cyber_pink': ['cyber_pink', 'neon_pink', 'hot_pink', 'neon_purple'],
    'toxic_green': ['toxic_green', 'neon_green', 'lime', 'neon_yellow'],
    'sunset': ['sunset_orange', 'neon_orange', 'neon_yellow', 'neon_pink'],
    'plasma': ['plasma_purple', 'neon_purple', 'violet', 'cyber_pink'],
}


# =============================================================================
# TUNNEL RIDE - First-person roller coaster through torus knot
# =============================================================================

def torus_knot_position(u: float, p: int, q: int, R: float, r: float
                        ) -> Tuple[float, float, float]:
    """Get position on torus knot at parameter u."""
    x = (R + r * math.cos(q * u)) * math.cos(p * u)
    y = (R + r * math.cos(q * u)) * math.sin(p * u)
    z = r * math.sin(q * u)
    return x, y, z


def torus_knot_tangent(u: float, p: int, q: int, R: float, r: float
                       ) -> Tuple[float, float, float]:
    """Get tangent vector (derivative) at parameter u."""
    # Numerical derivative
    eps = 0.001
    x1, y1, z1 = torus_knot_position(u - eps, p, q, R, r)
    x2, y2, z2 = torus_knot_position(u + eps, p, q, R, r)
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    mag = math.sqrt(dx*dx + dy*dy + dz*dz)
    if mag > 0:
        return dx/mag, dy/mag, dz/mag
    return 1, 0, 0


def cross_product(a: Tuple[float, float, float],
                  b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Cross product of two vectors."""
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    )


def normalize(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Normalize a vector."""
    mag = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if mag > 0:
        return v[0]/mag, v[1]/mag, v[2]/mag
    return v


def generate_tunnel_ride_frames(canvas: TerminalCanvas, fps: int,
                                 duration: float = 30.0,
                                 palette: str = 'electric_blue',
                                 knot_p: int = 2, knot_q: int = 3
                                 ) -> Generator[Image.Image, None, None]:
    """Generate first-person tunnel ride - classic racing game style.

    Camera is at the center looking forward. Tunnel rings come TOWARDS the camera
    with their centers following a curved track (Lissajous pattern).

    Args:
        canvas: Terminal canvas.
        fps: Frames per second.
        duration: Total duration.
        palette: Color palette name.
        knot_p, knot_q: Lissajous curve parameters for track shape.

    Yields:
        PIL Image frames.
    """
    total_frames = int(duration * fps)

    colors = NEON_PALETTES.get(palette, NEON_PALETTES['electric_blue'])

    cx = canvas.cols // 2
    cy = canvas.rows // 2

    # Tunnel parameters
    num_rings = 35           # Number of rings in the tunnel (sparser)
    ring_segments = 32       # Points per ring
    tunnel_radius = 0.3      # Radius of tunnel (in screen units)
    max_depth = 60.0         # How far the tunnel extends
    travel_speed = 14.0      # How fast we move through the tunnel

    # Track curve amplitude (how much the tunnel bends)
    curve_amplitude_x = 0.4   # Side to side (more dramatic)
    curve_amplitude_y = 0.15  # Up and down (less vertical, more horizontal turns)

    # Lissajous frequencies for the track curve
    freq_x = knot_p          # Horizontal oscillations
    freq_y = knot_q          # Vertical oscillations

    # Characters for rendering by depth
    ring_chars = ['█', '▓', '▒', '░', '·']

    # Cockpit view - horizon line (bottom portion is cockpit)
    horizon_y = int(cy * 1.3)  # Horizon slightly below center
    cockpit_top = horizon_y + 2  # Where cockpit frame starts

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Track position (how far we've traveled)
        track_pos = t * travel_speed

        # Collect all ring points
        points = []

        for ring_idx in range(num_rings):
            # Z depth of this ring (rings are evenly spaced in depth)
            # Rings wrap around when they pass the camera
            base_z = (ring_idx / num_rings) * max_depth
            z = (base_z - (track_pos % max_depth) + max_depth) % max_depth

            if z < 0.5:  # Too close, skip
                continue

            # Track curve position at this depth
            # The curve is evaluated based on how far "ahead" this ring is
            curve_param = (track_pos + z) * 0.1

            # Lissajous curve for track center offset
            offset_x = curve_amplitude_x * math.sin(freq_x * curve_param)
            offset_y = curve_amplitude_y * math.sin(freq_y * curve_param + math.pi / 4)

            # Perspective scale (closer = bigger)
            perspective = 1.0 / z
            ring_screen_radius = tunnel_radius * canvas.cols * perspective

            # Ring center on screen
            ring_cx = cx + offset_x * canvas.cols * perspective
            ring_cy = cy + offset_y * canvas.rows * perspective

            # Depth-based properties
            depth_ratio = z / max_depth
            color_idx = ring_idx % len(colors)
            char_idx = min(int(depth_ratio * len(ring_chars)), len(ring_chars) - 1)
            ring_char = ring_chars[char_idx]

            # Generate points around the ring
            for seg in range(ring_segments):
                angle = (seg / ring_segments) * 2 * math.pi

                # Point position on ring
                px = ring_cx + ring_screen_radius * math.cos(angle)
                py = ring_cy + ring_screen_radius * math.sin(angle) * 0.5  # Aspect correction

                sx = int(px)
                sy = int(py)

                # Only render above horizon (cockpit view)
                if 0 <= sx < canvas.cols and 0 <= sy < horizon_y:
                    points.append((z, sx, sy, colors[color_idx], ring_char))

        # Sort by depth (far to near) so close rings draw on top
        points.sort(key=lambda p: -p[0])

        # Render all points
        for z, sx, sy, color, char in points:
            canvas.set_pixel(sx, sy, char, color)

        # Draw track - prominent left and right edges
        track_width = 0.45  # Width of track (wider for visibility)

        for guide_idx in range(80):
            guide_z = 0.6 + guide_idx * 0.7
            if guide_z > max_depth:
                break

            curve_param = (track_pos + guide_z) * 0.1
            offset_x = curve_amplitude_x * math.sin(freq_x * curve_param)
            offset_y = curve_amplitude_y * math.sin(freq_y * curve_param + math.pi / 4)

            persp = 1.0 / guide_z
            center_x = cx + offset_x * canvas.cols * persp
            center_y = cy + offset_y * canvas.rows * persp

            # Track edge width in screen space
            edge_offset = track_width * canvas.cols * persp

            # Only draw above horizon
            if center_y >= horizon_y:
                continue

            # LEFT EDGE - bright and clear
            lx = int(center_x - edge_offset)
            ly = int(center_y)
            if 0 <= lx < canvas.cols and 0 <= ly < horizon_y:
                if guide_idx < 6:
                    canvas.set_pixel(lx, ly, '█', 'bright_red')
                elif guide_idx < 15:
                    canvas.set_pixel(lx, ly, '▓', 'red')
                elif guide_idx < 30:
                    canvas.set_pixel(lx, ly, '▒', 'red')
                else:
                    canvas.set_pixel(lx, ly, '░', 'bright_black')

            # RIGHT EDGE - bright and clear
            rx = int(center_x + edge_offset)
            ry = int(center_y)
            if 0 <= rx < canvas.cols and 0 <= ry < horizon_y:
                if guide_idx < 6:
                    canvas.set_pixel(rx, ry, '█', 'bright_green')
                elif guide_idx < 15:
                    canvas.set_pixel(rx, ry, '▓', 'green')
                elif guide_idx < 30:
                    canvas.set_pixel(rx, ry, '▒', 'green')
                else:
                    canvas.set_pixel(rx, ry, '░', 'bright_black')

            # Center dashes (road markings)
            if guide_idx % 4 < 2:
                gx = int(center_x)
                gy = int(center_y)
                if 0 <= gx < canvas.cols and 0 <= gy < horizon_y:
                    if guide_idx < 12:
                        canvas.set_pixel(gx, gy, '─', 'bright_white')
                    elif guide_idx < 30:
                        canvas.set_pixel(gx, gy, '─', 'white')

        # ═══════════════════════════════════════════════════════════════
        # COCKPIT OVERLAY - static frame at bottom
        # ═══════════════════════════════════════════════════════════════

        # Cockpit top edge (horizon line)
        for x in range(canvas.cols):
            canvas.set_pixel(x, horizon_y, '▀', 'bright_black')

        # Fill cockpit area with dark
        for y in range(horizon_y + 1, canvas.rows):
            for x in range(canvas.cols):
                canvas.set_pixel(x, y, '░', 'bright_black')

        # Cockpit frame - left side
        for y in range(horizon_y + 1, canvas.rows):
            canvas.set_pixel(0, y, '║', 'cyan')
            canvas.set_pixel(1, y, '│', 'bright_black')

        # Cockpit frame - right side
        for y in range(horizon_y + 1, canvas.rows):
            canvas.set_pixel(canvas.cols - 1, y, '║', 'cyan')
            canvas.set_pixel(canvas.cols - 2, y, '│', 'bright_black')

        # Dashboard bottom
        dash_y = canvas.rows - 3
        for x in range(2, canvas.cols - 2):
            canvas.set_pixel(x, dash_y, '═', 'cyan')

        # Speed indicator (left)
        speed_display = f"SPD:{int(travel_speed * 10)}"
        for i, ch in enumerate(speed_display):
            if 5 + i < canvas.cols:
                canvas.set_pixel(5 + i, dash_y + 1, ch, 'bright_green')

        # Track position indicator (center)
        track_pct = int((track_pos % (2 * math.pi * 10)) / (2 * math.pi * 10) * 100)
        pos_display = f"TRK:{track_pct:02d}%"
        start_x = cx - len(pos_display) // 2
        for i, ch in enumerate(pos_display):
            canvas.set_pixel(start_x + i, dash_y + 1, ch, 'bright_cyan')

        # Mode indicator (right)
        mode_display = "LISSAJOUS"
        for i, ch in enumerate(mode_display):
            if canvas.cols - 15 + i < canvas.cols - 2:
                canvas.set_pixel(canvas.cols - 15 + i, dash_y + 1, ch, 'bright_magenta')

        yield canvas.render()


def generate_swarm3d_frames(canvas: TerminalCanvas, fps: int,
                             duration: float = 30.0,
                             palette: str = 'electric_blue',
                             knot_p: int = 2, knot_q: int = 3,
                             num_particles: int = 200
                             ) -> Generator[Image.Image, None, None]:
    """Generate first-person tunnel ride ON a 3D torus knot.

    Camera travels along the knot path, looking forward through a tunnel
    that wraps around the 3D shape. True roller coaster experience!

    Args:
        canvas: Terminal canvas.
        fps: Frames per second.
        duration: Total duration.
        palette: Color palette name.
        knot_p, knot_q: Torus knot parameters.
        num_particles: Not used (kept for API compatibility).

    Yields:
        PIL Image frames.
    """
    total_frames = int(duration * fps)
    colors = NEON_PALETTES.get(palette, NEON_PALETTES['electric_blue'])

    cx = canvas.cols // 2
    cy = canvas.rows // 2

    # Torus knot parameters - make it bigger for better tunnel feel
    R = 2.0   # Major radius (size of the "donut")
    r = 0.8   # Minor radius (how much it weaves in/out)

    # Tunnel parameters
    tunnel_radius = 0.35    # Radius of the tunnel around the path (larger = more immersive)
    num_rings_ahead = 40    # Number of tunnel rings ahead of camera
    num_rings_behind = 15   # Number of tunnel rings behind camera (for immersion)
    ring_segments = 24      # Points per ring
    look_ahead = 1.5        # How far ahead to look (in radians along knot)
    look_behind = 0.4       # How far behind to render (in radians)

    # Camera speed - complete one full loop in duration
    # For a (p,q) torus knot, one full trace = 2*pi radians
    cam_speed = (2 * math.pi) / duration

    # Characters for depth
    ring_chars = ['█', '▓', '▒', '░', '·']

    def knot_position(u: float) -> Tuple[float, float, float]:
        """Get 3D position on torus knot at parameter u."""
        x = (R + r * math.cos(knot_q * u)) * math.cos(knot_p * u)
        y = (R + r * math.cos(knot_q * u)) * math.sin(knot_p * u)
        z = r * math.sin(knot_q * u)
        return x, y, z

    def knot_tangent(u: float) -> Tuple[float, float, float]:
        """Get normalized tangent (forward direction) at parameter u."""
        # Numerical derivative
        delta = 0.001
        p1 = knot_position(u - delta)
        p2 = knot_position(u + delta)
        tx = p2[0] - p1[0]
        ty = p2[1] - p1[1]
        tz = p2[2] - p1[2]
        mag = math.sqrt(tx*tx + ty*ty + tz*tz)
        if mag > 0:
            return (tx/mag, ty/mag, tz/mag)
        return (1, 0, 0)

    def knot_normal(u: float) -> Tuple[float, float, float]:
        """Get normal vector (perpendicular to tangent, in curve plane)."""
        # Second derivative gives acceleration, which points toward center of curvature
        delta = 0.001
        t1 = knot_tangent(u - delta)
        t2 = knot_tangent(u + delta)
        nx = t2[0] - t1[0]
        ny = t2[1] - t1[1]
        nz = t2[2] - t1[2]
        mag = math.sqrt(nx*nx + ny*ny + nz*nz)
        if mag > 0:
            return (nx/mag, ny/mag, nz/mag)
        return (0, 1, 0)

    # World up reference - we'll try to keep camera "up" aligned with this
    world_up = (0, 0, 1)

    # Dynamic parameters that change over time
    # Base look-ahead - will be adjusted based on speed and curvature
    base_look_ahead = 0.5

    # Speed profile: start slow, speed up, slow for turns, zoom out at end
    # Duration breakdown:
    #   0-10%: Slow start (0.5x speed)
    #   10-70%: Variable speed with acceleration (0.8x - 1.5x)
    #   70-85%: Fast cruise (1.5x speed)
    #   85-100%: Slow down and zoom out

    def get_speed_multiplier(progress: float) -> float:
        """Get speed multiplier based on progress through the ride."""
        if progress < 0.10:
            # Slow start - ease in
            return 0.5 + progress * 3.0  # 0.5 -> 0.8
        elif progress < 0.70:
            # Variable speed section - sinusoidal variation
            t = (progress - 0.10) / 0.60
            return 0.8 + 0.7 * (0.5 + 0.5 * math.sin(t * math.pi * 4))  # 0.8 -> 1.5
        elif progress < 0.85:
            # Fast cruise
            return 1.5
        else:
            # Slow down for ending
            t = (progress - 0.85) / 0.15
            return 1.5 - t * 1.2  # 1.5 -> 0.3

    def get_look_ahead(progress: float, speed_mult: float) -> float:
        """Dynamic look-ahead - further when going fast, closer in turns."""
        base = base_look_ahead
        # Look further ahead when going faster
        speed_factor = 0.3 + speed_mult * 0.5
        # During zoom-out phase, look even further
        if progress > 0.85:
            zoom_t = (progress - 0.85) / 0.15
            speed_factor += zoom_t * 1.0
        return base * speed_factor

    def get_fov_factor(progress: float) -> float:
        """Camera FOV - widens at the end for dramatic effect (stays inside tube)."""
        if progress < 0.85:
            return 1.0
        else:
            # Widen FOV instead of pulling back - keeps us inside
            t = (progress - 0.85) / 0.15
            return 1.0 + t * 0.8  # 1.0 -> 1.8 (wider view)

    # Track cumulative position (for variable speed)
    cumulative_u = 0.0

    # Smoothed camera orientation - persists between frames
    # Start with tangent at initial position
    initial_tangent = knot_tangent(0.0)
    smooth_fwd = list(initial_tangent)  # Mutable for smoothing
    smooth_up = [0.0, 0.0, 1.0]  # Start with world up

    # Smoothing factor: lower = smoother but slower to respond
    # 0.05 = very smooth (20 frames to catch up)
    # 0.15 = moderate smoothing
    orientation_smoothing = 0.08

    def normalize(v):
        """Normalize a 3D vector."""
        mag = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
        if mag > 0.0001:
            return [v[0]/mag, v[1]/mag, v[2]/mag]
        return [1, 0, 0]

    def lerp_vec(a, b, t):
        """Linear interpolate between two vectors."""
        return [a[0] + t * (b[0] - a[0]),
                a[1] + t * (b[1] - a[1]),
                a[2] + t * (b[2] - a[2])]

    for frame in range(total_frames):
        t = frame / fps
        progress = frame / total_frames  # 0.0 to 1.0
        canvas.clear()

        # Get dynamic parameters for this frame
        speed_mult = get_speed_multiplier(progress)
        current_look_ahead = get_look_ahead(progress, speed_mult)
        fov_mult = get_fov_factor(progress)  # FOV multiplier (stays inside tube)

        # Update camera position with variable speed
        cumulative_u += (cam_speed * speed_mult) / fps

        # Camera position - stays on the track (inside the tube)
        u_cam = cumulative_u
        cam_pos = knot_position(u_cam)

        # TARGET forward = tangent (direction of travel on track)
        # Using tangent instead of look-at gives more stable orientation
        target_fwd = knot_tangent(u_cam)

        # Smooth the forward direction (exponential moving average)
        smooth_fwd = lerp_vec(smooth_fwd, target_fwd, orientation_smoothing)
        smooth_fwd = normalize(smooth_fwd)

        # TARGET up: world_up projected perpendicular to forward
        dot = world_up[0] * smooth_fwd[0] + world_up[1] * smooth_fwd[1] + world_up[2] * smooth_fwd[2]
        target_up = [
            world_up[0] - dot * smooth_fwd[0],
            world_up[1] - dot * smooth_fwd[1],
            world_up[2] - dot * smooth_fwd[2]
        ]
        target_up = normalize(target_up)

        # Handle case where forward is nearly vertical (world_up fails)
        up_mag = math.sqrt(target_up[0]**2 + target_up[1]**2 + target_up[2]**2)
        if up_mag < 0.1:
            # Use X-axis as fallback when going vertical
            target_up = [1, 0, 0]

        # Smooth the up direction
        smooth_up = lerp_vec(smooth_up, target_up, orientation_smoothing)
        smooth_up = normalize(smooth_up)

        # Re-orthogonalize: make sure up is perpendicular to forward
        dot = smooth_up[0] * smooth_fwd[0] + smooth_up[1] * smooth_fwd[1] + smooth_up[2] * smooth_fwd[2]
        cam_up = normalize([
            smooth_up[0] - dot * smooth_fwd[0],
            smooth_up[1] - dot * smooth_fwd[1],
            smooth_up[2] - dot * smooth_fwd[2]
        ])

        cam_fwd = tuple(smooth_fwd)
        cam_up = tuple(cam_up)

        # Right = forward × up
        cam_right = (
            cam_fwd[1] * cam_up[2] - cam_fwd[2] * cam_up[1],
            cam_fwd[2] * cam_up[0] - cam_fwd[0] * cam_up[2],
            cam_fwd[0] * cam_up[1] - cam_fwd[1] * cam_up[0]
        )

        # Collect points to render and store ring screen positions for connectors
        points = []
        ring_screen_positions = []  # [ring_idx][seg_idx] = (sx, sy, depth, color)

        # Dynamic FOV based on progress (for dramatic ending)
        base_fov = 2.0 * fov_mult

        # Helper function to render a ring at parameter u
        def render_ring(u_ring: float, ring_idx: int, total_rings: int, is_behind: bool = False):
            """Render a single tunnel ring and return its screen positions."""
            ring_center = knot_position(u_ring)
            ring_tangent = knot_tangent(u_ring)
            ring_normal = knot_normal(u_ring)
            ring_binormal = (
                ring_tangent[1] * ring_normal[2] - ring_tangent[2] * ring_normal[1],
                ring_tangent[2] * ring_normal[0] - ring_tangent[0] * ring_normal[2],
                ring_tangent[0] * ring_normal[1] - ring_tangent[1] * ring_normal[0]
            )

            ring_positions = []

            for seg in range(ring_segments):
                angle = (seg / ring_segments) * 2 * math.pi
                local_x = tunnel_radius * math.cos(angle)
                local_y = tunnel_radius * math.sin(angle)

                world_x = ring_center[0] + local_x * ring_normal[0] + local_y * ring_binormal[0]
                world_y = ring_center[1] + local_x * ring_normal[1] + local_y * ring_binormal[1]
                world_z = ring_center[2] + local_x * ring_normal[2] + local_y * ring_binormal[2]

                dx = world_x - cam_pos[0]
                dy = world_y - cam_pos[1]
                dz = world_z - cam_pos[2]

                depth = dx * cam_fwd[0] + dy * cam_fwd[1] + dz * cam_fwd[2]
                screen_x = dx * cam_right[0] + dy * cam_right[1] + dz * cam_right[2]
                screen_y = dx * cam_up[0] + dy * cam_up[1] + dz * cam_up[2]

                # Render both in front AND behind (for immersive tunnel feel)
                abs_depth = abs(depth)
                if abs_depth > 0.02:
                    persp = base_fov / abs_depth
                    sx = int(cx + screen_x * canvas.cols * persp)
                    sy = int(cy - screen_y * canvas.rows * 2.0 * persp)

                    # Depth ratio for character selection (further = dimmer)
                    depth_ratio = ring_idx / total_rings
                    char_idx = min(int(depth_ratio * len(ring_chars)), len(ring_chars) - 1)
                    # Behind rings are dimmer (use last character)
                    if is_behind:
                        char_idx = min(char_idx + 2, len(ring_chars) - 1)
                    color_idx = ring_idx % len(colors)

                    ring_positions.append((sx, sy, abs_depth, colors[color_idx]))

                    if 0 <= sx < canvas.cols and 0 <= sy < canvas.rows:
                        points.append((abs_depth, sx, sy, colors[color_idx], ring_chars[char_idx]))
                else:
                    ring_positions.append(None)

            return ring_positions

        # Render rings AHEAD of camera (main forward view)
        for ring_idx in range(num_rings_ahead):
            u_ring = u_cam + (ring_idx + 1) * (look_ahead / num_rings_ahead)
            ring_positions = render_ring(u_ring, ring_idx, num_rings_ahead, is_behind=False)
            ring_screen_positions.append(ring_positions)

        # Render rings BEHIND camera (creates enclosed tunnel feel)
        for ring_idx in range(num_rings_behind):
            u_ring = u_cam - (ring_idx + 1) * (look_behind / num_rings_behind)
            # Behind rings are rendered but not added to connector list
            render_ring(u_ring, ring_idx, num_rings_behind, is_behind=True)

        # Add connector lines between adjacent rings (longitudinal struts)
        connector_chars = ['│', '║', '|', ':', '·']
        num_connectors = 8  # Draw connectors at every N segments

        for ring_idx in range(len(ring_screen_positions) - 1):
            curr_ring = ring_screen_positions[ring_idx]
            next_ring = ring_screen_positions[ring_idx + 1]

            for seg in range(0, ring_segments, ring_segments // num_connectors):
                if seg < len(curr_ring) and seg < len(next_ring):
                    p1 = curr_ring[seg]
                    p2 = next_ring[seg]

                    if p1 is not None and p2 is not None:
                        sx1, sy1, d1, c1 = p1
                        sx2, sy2, d2, c2 = p2

                        # Draw line between points using Bresenham-ish approach
                        dx = abs(sx2 - sx1)
                        dy = abs(sy2 - sy1)
                        steps = max(dx, dy, 1)

                        for step in range(steps + 1):
                            t = step / steps if steps > 0 else 0
                            lx = int(sx1 + t * (sx2 - sx1))
                            ly = int(sy1 + t * (sy2 - sy1))
                            ld = d1 + t * (d2 - d1)

                            if 0 <= lx < canvas.cols and 0 <= ly < canvas.rows:
                                depth_ratio = ring_idx / num_rings_ahead
                                char_idx = min(int(depth_ratio * len(connector_chars)), len(connector_chars) - 1)
                                points.append((ld, lx, ly, c1, connector_chars[char_idx]))

        # Sort by depth (far to near)
        points.sort(key=lambda p: -p[0])

        # Render all points
        for depth, sx, sy, color, char in points:
            canvas.set_pixel(sx, sy, char, color)

        yield canvas.render()


def generate_neon_loop_frames(canvas: TerminalCanvas, fps: int,
                               duration: float = 40.0,
                               palette: str = 'electric_blue',
                               knot_p: int = 2, knot_q: int = 3
                               ) -> Generator[Image.Image, None, None]:
    """Generate a seamless looping neon torus knot animation.

    Creates a perfect loop suitable for VJ backgrounds, Wallpaper Engine,
    and motion graphics.

    Args:
        canvas: Terminal canvas.
        fps: Frames per second.
        duration: Loop duration in seconds (default 40s for seamless loop).
        palette: Neon color palette name.
        knot_p: Torus knot p parameter (winds around).
        knot_q: Torus knot q parameter (winds through).

    Yields:
        PIL Image frames.
    """
    total_frames = int(duration * fps)

    # Get the color palette
    colors = NEON_PALETTES.get(palette, NEON_PALETTES['electric_blue'])

    cx = canvas.cols // 2
    cy = canvas.rows // 2
    scale_x = canvas.cols // 2.0
    scale_y = canvas.rows // 1.8

    # Torus parameters
    R = 0.7   # Major radius
    r = 0.28  # Minor radius

    # For seamless looping:
    # - Rotation must complete exact cycles
    # - Knot tracer must return to start position
    # Calculate rotation speed so we complete exactly 1 full rotation
    rotation_cycles = 1
    rotation_speed = (2 * math.pi * rotation_cycles) / duration

    # Knot tracer speed - complete enough cycles to return to start
    # For a (p,q) knot, one complete trace = 2*pi / gcd(p,q) * max(p,q) radians
    # Simplified: complete 2 full knot cycles for visual continuity
    knot_cycles = 2
    knot_speed = (2 * math.pi * max(knot_p, knot_q) * knot_cycles) / duration

    chars_by_depth = ['·', '∘', '○', '●', '◉']

    num_tracers = 12  # More particles for denser visuals

    for frame in range(total_frames):
        t = frame / fps
        canvas.clear()

        # Rotation - perfect loop
        rotation_y = t * rotation_speed
        rotation_x = 0.35 + math.sin(t * rotation_speed * 2) * 0.15

        points = []

        # Draw the full knot path (static glowing outline)
        path_points = 800
        for i in range(path_points):
            u = (i / path_points) * 2 * math.pi * max(knot_p, knot_q)

            x = (R + r * math.cos(knot_q * u)) * math.cos(knot_p * u)
            y = (R + r * math.cos(knot_q * u)) * math.sin(knot_p * u)
            z = r * math.sin(knot_q * u)

            sx, sy, depth = project_3d_to_2d(
                x, y, z, cx, cy, scale_x, scale_y,
                camera_distance=2.8,
                rotation_y=rotation_y,
                rotation_x=rotation_x
            )

            if 0 <= sx < canvas.cols and 0 <= sy < canvas.rows:
                color_idx = int((i / path_points) * len(colors)) % len(colors)
                points.append((depth, sx, sy, colors[color_idx], 0.3, False))

        # Draw multiple tracers with long glowing trails
        for tracer in range(num_tracers):
            tracer_offset = (tracer / num_tracers) * 2 * math.pi * max(knot_p, knot_q)
            trail_length = 80

            for trail_i in range(trail_length):
                # Position along the knot
                u = t * knot_speed + tracer_offset - trail_i * 0.02

                x = (R + r * math.cos(knot_q * u)) * math.cos(knot_p * u)
                y = (R + r * math.cos(knot_q * u)) * math.sin(knot_p * u)
                z = r * math.sin(knot_q * u)

                sx, sy, depth = project_3d_to_2d(
                    x, y, z, cx, cy, scale_x, scale_y,
                    camera_distance=2.8,
                    rotation_y=rotation_y,
                    rotation_x=rotation_x
                )

                if 0 <= sx < canvas.cols and 0 <= sy < canvas.rows:
                    intensity = 1.0 - (trail_i / trail_length)
                    is_head = trail_i == 0
                    color = 'bright_white' if is_head else colors[tracer % len(colors)]
                    points.append((depth, sx, sy, color, intensity, is_head))

        # Sort by depth and render
        points.sort(key=lambda pt: pt[0])

        for depth, sx, sy, color, intensity, is_head in points:
            if not (0 <= sx < canvas.cols and 0 <= sy < canvas.rows):
                continue

            depth_norm = (depth + 1.5) / 3.0
            depth_idx = int(depth_norm * (len(chars_by_depth) - 1))
            depth_idx = max(0, min(len(chars_by_depth) - 1, depth_idx))

            if is_head:
                char = '◉'
                render_color = 'bright_white'
            elif intensity > 0.7:
                char = '●'
                render_color = color
            elif intensity > 0.4:
                char = '○'
                render_color = color
            elif intensity > 0.2:
                char = '∘'
                render_color = color
            else:
                char = '·'
                render_color = color

            canvas.set_pixel(sx, sy, char, render_color)

        yield canvas.render()


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Lissajous Particle Swarm - 3D Visualization"
    )

    parser.add_argument('-o', '--output', default='lissajous_swarm.gif',
                        help='Output GIF path')
    parser.add_argument('--cols', type=int, default=133,
                        help='Terminal columns (default: 133)')
    parser.add_argument('--rows', type=int, default=37,
                        help='Terminal rows (default: 37)')
    parser.add_argument('--fps', type=int, default=30,
                        help='Frames per second (default: 30)')
    parser.add_argument('--duration', type=float, default=30.0,
                        help='Duration in seconds (default: 30)')
    parser.add_argument('--particles', type=int, default=50,
                        help='Number of particles (default: 50)')
    parser.add_argument('--mode', choices=['swarm', 'journey', 'sphere', 'torus', 'helix', 'breathing', 'compilation', 'knots', 'neon_loop', 'tunnel', 'swarm3d'],
                        default='journey',
                        help='Visualization mode: swarm, journey, sphere, torus, helix, breathing, compilation, knots, neon_loop, tunnel (default: journey)')
    parser.add_argument('--stability', type=float, default=0.6,
                        help='Stability bias 0-1 for swarm mode (default: 0.6)')
    parser.add_argument('--palette', choices=['electric_blue', 'cyber_pink', 'toxic_green', 'sunset', 'plasma'],
                        default='electric_blue',
                        help='Neon color palette for neon_loop mode (default: electric_blue)')
    parser.add_argument('--knot', type=str, default='2,3',
                        help='Torus knot p,q parameters for neon_loop mode (default: 2,3 = trefoil)')

    args = parser.parse_args()

    canvas = TerminalCanvas(cols=args.cols, rows=args.rows)

    print(f"Canvas: {canvas.cols}x{canvas.rows} chars = "
          f"{canvas.img_width}x{canvas.img_height} pixels")
    print(f"Mode: {args.mode}, Duration: {args.duration}s, FPS: {args.fps}")

    if args.mode == 'swarm':
        print(f"Particles: {args.particles}, Stability: {args.stability}")
        frames = generate_swarm_frames(
            canvas, args.fps, args.duration,
            num_particles=args.particles,
            stability_bias=args.stability
        )
    elif args.mode == 'journey':
        print("Generating stability journey (chaos → stable → chaos)")
        frames = generate_stability_journey_frames(
            canvas, args.fps, args.duration
        )
    elif args.mode == 'sphere':
        print(f"Generating spherical harmonics with {args.particles} particles")
        frames = generate_sphere_harmonics_frames(
            canvas, args.fps, args.duration,
            num_particles=args.particles
        )
    elif args.mode == 'torus':
        print("Generating torus knots")
        frames = generate_torus_knots_frames(
            canvas, args.fps, args.duration,
            num_knots=5
        )
    elif args.mode == 'helix':
        print("Generating double helix patterns")
        frames = generate_helix_frames(
            canvas, args.fps, args.duration,
            num_helices=3
        )
    elif args.mode == 'breathing':
        print(f"Generating breathing sphere with {args.particles} particles")
        frames = generate_breathing_sphere_frames(
            canvas, args.fps, args.duration,
            num_particles=args.particles
        )
    elif args.mode == 'compilation':
        print(f"Generating chaos compilation with {args.particles} particles")
        print("  Journey: sphere → chaos → lissajous → torus → helix → breathing → convergence")
        frames = generate_chaos_compilation_frames(
            canvas, args.fps, args.duration,
            num_particles=args.particles
        )
    elif args.mode == 'knots':
        print("Generating torus knots showcase")
        print("  Knots: trefoil → solomon → cinquefoil → septafoil → seven_twist → complex → high_order → three_four")
        frames = generate_torus_showcase_frames(
            canvas, args.fps, args.duration
        )
    elif args.mode == 'neon_loop':
        knot_p, knot_q = map(int, args.knot.split(','))
        print(f"Generating neon seamless loop ({knot_p},{knot_q}) torus knot")
        print(f"  Palette: {args.palette}")
        print(f"  Duration: {args.duration}s (seamless loop)")
        frames = generate_neon_loop_frames(
            canvas, args.fps, args.duration,
            palette=args.palette,
            knot_p=knot_p, knot_q=knot_q
        )
    elif args.mode == 'tunnel':
        knot_p, knot_q = map(int, args.knot.split(','))
        print(f"Generating tunnel ride through ({knot_p},{knot_q}) torus knot")
        print(f"  Palette: {args.palette}")
        print("  First-person roller coaster view!")
        frames = generate_tunnel_ride_frames(
            canvas, args.fps, args.duration,
            palette=args.palette,
            knot_p=knot_p, knot_q=knot_q
        )

    elif args.mode == 'swarm3d':
        knot_p, knot_q = map(int, args.knot.split(','))
        print(f"Generating first-person tunnel ride on ({knot_p},{knot_q}) torus knot")
        print(f"  Palette: {args.palette}")
        print("  Dynamic speed: Slow start → Variable → Fast → Slow/Zoom-out")
        print("  Adaptive look-ahead and zoom-out finale!")
        frames = generate_swarm3d_frames(
            canvas, args.fps, args.duration,
            palette=args.palette,
            knot_p=knot_p, knot_q=knot_q,
            num_particles=args.particles
        )

    render_gif(args.output, frames, args.fps)


if __name__ == '__main__':
    main()
