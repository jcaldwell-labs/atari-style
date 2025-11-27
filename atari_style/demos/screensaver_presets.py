"""Preset configurations for screensaver animation modes."""

import math

# Lissajous Curve presets (a, b, delta, points)
LISSAJOUS_PRESETS = {
    'classic': {
        'a': 3.0,
        'b': 4.0,
        'delta': math.pi / 2,
        'points': 500
    },
    'butterfly': {
        'a': 5.0,
        'b': 4.0,
        'delta': 1.05,
        'points': 600
    },
    'infinity': {
        'a': 2.0,
        'b': 2.0,
        'delta': 0.79,
        'points': 400
    },
    'flower': {
        'a': 7.0,
        'b': 5.0,
        'delta': 0.0,
        'points': 800
    },
    'complex': {
        'a': 9.0,
        'b': 8.0,
        'delta': 1.57,
        'points': 900
    }
}

# Spiral Animation presets (num_spirals, rotation_speed, tightness, radius_scale)
SPIRAL_PRESETS = {
    'galaxy': {
        'num_spirals': 2,
        'rotation_speed': 0.5,
        'tightness': 8.0,
        'radius_scale': 0.4
    },
    'hurricane': {
        'num_spirals': 1,
        'rotation_speed': 1.5,
        'tightness': 12.0,
        'radius_scale': 0.5
    },
    'triple_helix': {
        'num_spirals': 3,
        'rotation_speed': 1.0,
        'tightness': 6.0,
        'radius_scale': 0.6
    },
    'slow_bloom': {
        'num_spirals': 4,
        'rotation_speed': 0.3,
        'tightness': 4.0,
        'radius_scale': 0.7
    },
    'hypnotic': {
        'num_spirals': 6,
        'rotation_speed': 2.0,
        'tightness': 10.0,
        'radius_scale': 0.35
    }
}

# Circle Wave Animation presets (num_circles, wave_amplitude, wave_frequency, spacing)
CIRCLE_WAVE_PRESETS = {
    'ripples': {
        'num_circles': 20,
        'wave_amplitude': 3.0,
        'wave_frequency': 0.8,
        'spacing': 3.0
    },
    'pulse': {
        'num_circles': 10,
        'wave_amplitude': 5.0,
        'wave_frequency': 1.5,
        'spacing': 5.0
    },
    'gentle': {
        'num_circles': 25,
        'wave_amplitude': 1.5,
        'wave_frequency': 0.3,
        'spacing': 2.0
    },
    'chaotic': {
        'num_circles': 30,
        'wave_amplitude': 6.0,
        'wave_frequency': 2.0,
        'spacing': 1.5
    },
    'slow_wave': {
        'num_circles': 15,
        'wave_amplitude': 4.0,
        'wave_frequency': 0.2,
        'spacing': 4.0
    }
}

# Plasma Animation presets (freq_x, freq_y, freq_diag, freq_radial)
PLASMA_PRESETS = {
    'classic': {
        'freq_x': 0.1,
        'freq_y': 0.1,
        'freq_diag': 0.08,
        'freq_radial': 0.1
    },
    'horizontal': {
        'freq_x': 0.2,
        'freq_y': 0.05,
        'freq_diag': 0.03,
        'freq_radial': 0.07
    },
    'vertical': {
        'freq_x': 0.05,
        'freq_y': 0.2,
        'freq_diag': 0.03,
        'freq_radial': 0.07
    },
    'radial_burst': {
        'freq_x': 0.05,
        'freq_y': 0.05,
        'freq_diag': 0.05,
        'freq_radial': 0.25
    },
    'diagonal': {
        'freq_x': 0.08,
        'freq_y': 0.08,
        'freq_diag': 0.2,
        'freq_radial': 0.06
    },
    'fine_detail': {
        'freq_x': 0.25,
        'freq_y': 0.25,
        'freq_diag': 0.22,
        'freq_radial': 0.2
    }
}

# Mandelbrot Zoomer presets (zoom, center_x, center_y, max_iterations)
MANDELBROT_PRESETS = {
    'overview': {
        'zoom': 1.0,
        'center_x': -0.5,
        'center_y': 0.0,
        'max_iterations': 50
    },
    'seahorse_valley': {
        'zoom': 50.0,
        'center_x': -0.75,
        'center_y': 0.1,
        'max_iterations': 100
    },
    'spiral': {
        'zoom': 100.0,
        'center_x': -0.7746,
        'center_y': 0.1075,
        'max_iterations': 150
    },
    'elephant_valley': {
        'zoom': 200.0,
        'center_x': 0.3,
        'center_y': 0.0,
        'max_iterations': 120
    },
    'deep_zoom': {
        'zoom': 500.0,
        'center_x': -0.7463,
        'center_y': 0.1102,
        'max_iterations': 200
    },
    'mini_mandelbrot': {
        'zoom': 80.0,
        'center_x': -0.16,
        'center_y': 1.035,
        'max_iterations': 130
    }
}

# Fluid Lattice presets (rain_rate, wave_speed, drop_strength, damping)
FLUID_LATTICE_PRESETS = {
    'light_rain': {
        'rain_rate': 0.2,
        'wave_speed': 0.3,
        'drop_strength': 5.0,
        'damping': 0.95
    },
    'heavy_storm': {
        'rain_rate': 1.0,
        'wave_speed': 0.5,
        'drop_strength': 15.0,
        'damping': 0.90
    },
    'gentle_drops': {
        'rain_rate': 0.1,
        'wave_speed': 0.2,
        'drop_strength': 8.0,
        'damping': 0.98
    },
    'fast_ripples': {
        'rain_rate': 0.5,
        'wave_speed': 0.8,
        'drop_strength': 6.0,
        'damping': 0.85
    },
    'persistent_waves': {
        'rain_rate': 0.3,
        'wave_speed': 0.25,
        'drop_strength': 10.0,
        'damping': 0.995
    }
}

# Particle Swarm presets (num_particles, speed, cohesion, separation)
PARTICLE_SWARM_PRESETS = {
    'balanced': {
        'num_particles': 50,
        'speed': 2.0,
        'cohesion': 0.5,
        'separation': 1.0
    },
    'tight_flock': {
        'num_particles': 70,
        'speed': 1.5,
        'cohesion': 1.5,
        'separation': 0.3
    },
    'dispersed': {
        'num_particles': 40,
        'speed': 3.0,
        'cohesion': 0.2,
        'separation': 2.5
    },
    'fast_chaos': {
        'num_particles': 100,
        'speed': 4.0,
        'cohesion': 0.3,
        'separation': 1.5
    },
    'slow_dance': {
        'num_particles': 30,
        'speed': 1.0,
        'cohesion': 1.0,
        'separation': 0.8
    },
    'busy_swarm': {
        'num_particles': 80,
        'speed': 2.5,
        'cohesion': 0.8,
        'separation': 1.2
    }
}

# Tunnel Vision presets (depth_speed, rotation_speed, tunnel_size, color_cycle_speed)
TUNNEL_VISION_PRESETS = {
    'classic': {
        'depth_speed': 1.0,
        'rotation_speed': 0.5,
        'tunnel_size': 1.0,
        'color_cycle_speed': 1.0
    },
    'fast_spin': {
        'depth_speed': 0.5,
        'rotation_speed': 2.0,
        'tunnel_size': 1.2,
        'color_cycle_speed': 1.5
    },
    'hyperspace': {
        'depth_speed': 4.0,
        'rotation_speed': 0.2,
        'tunnel_size': 0.8,
        'color_cycle_speed': 2.0
    },
    'wide_slow': {
        'depth_speed': 0.3,
        'rotation_speed': 0.1,
        'tunnel_size': 2.5,
        'color_cycle_speed': 0.5
    },
    'reverse_spin': {
        'depth_speed': 1.5,
        'rotation_speed': -1.5,
        'tunnel_size': 1.0,
        'color_cycle_speed': 1.2
    },
    'psychedelic': {
        'depth_speed': 2.0,
        'rotation_speed': 1.0,
        'tunnel_size': 1.5,
        'color_cycle_speed': 3.0
    }
}

# Master dictionary mapping animation indices to their preset collections
ANIMATION_PRESETS = {
    0: LISSAJOUS_PRESETS,
    1: SPIRAL_PRESETS,
    2: CIRCLE_WAVE_PRESETS,
    3: PLASMA_PRESETS,
    4: MANDELBROT_PRESETS,
    5: FLUID_LATTICE_PRESETS,
    6: PARTICLE_SWARM_PRESETS,
    7: TUNNEL_VISION_PRESETS,
}


def get_preset_names(animation_index: int) -> list:
    """Get list of preset names for a given animation mode."""
    if animation_index in ANIMATION_PRESETS:
        return list(ANIMATION_PRESETS[animation_index].keys())
    return []


def get_preset(animation_index: int, preset_name: str) -> dict:
    """Get preset parameters for a given animation mode and preset name."""
    if animation_index in ANIMATION_PRESETS:
        presets = ANIMATION_PRESETS[animation_index]
        if preset_name in presets:
            return presets[preset_name]
    return None
