"""Test script for GPU effect library (Phase 4).

Tests all new GLSL effects: plasma, spiral, tunnel, lissajous, fluid.

Usage:
    python -m atari_style.core.gl.test_effects
    python -m atari_style.core.gl.test_effects --effect plasma
    python -m atari_style.core.gl.test_effects --output effects_demo.png
    python -m atari_style.core.gl.test_effects --grid
"""

import sys
import time
import argparse

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required: pip install Pillow")
    sys.exit(1)

from .renderer import GLRenderer
from .uniforms import ShaderUniforms


# Effect configurations: shader path and default parameters
EFFECTS = {
    'plasma': {
        'shader': 'atari_style/shaders/effects/plasma.frag',
        'params': (0.1, 0.1, 0.08, 0.1),  # freq_x, freq_y, freq_diag, freq_radial
        'description': 'Classic demoscene plasma effect'
    },
    'spiral': {
        'shader': 'atari_style/shaders/effects/spiral.frag',
        'params': (0.3, 1.0, 1.6, 1.0),  # num_spirals, rotation_speed, tightness, scale
        'description': 'Rotating spiral pattern'
    },
    'tunnel': {
        'shader': 'atari_style/shaders/effects/tunnel.frag',
        'params': (1.5, 0.5, 1.0, 0.3),  # depth_speed, rotation_speed, tunnel_size, color_speed
        'description': 'Flying through infinite tunnel'
    },
    'lissajous': {
        'shader': 'atari_style/shaders/effects/lissajous.frag',
        'params': (0.3, 0.4, 0.5, 0.7),  # freqA, freqB, phase, trail_intensity
        'description': 'Parametric Lissajous curves with glow'
    },
    'fluid': {
        'shader': 'atari_style/shaders/effects/fluid.frag',
        'params': (0.3, 0.4, 8.0, 0.95),  # rain_rate, wave_speed, drop_strength, damping
        'description': 'Water ripple simulation'
    },
}


def render_effect(effect_name: str, width: int = 800, height: int = 600,
                  time_val: float = 2.0, color_mode: int = 0) -> Image.Image:
    """Render a single frame of an effect.

    Args:
        effect_name: Name of effect (plasma, spiral, tunnel, lissajous, fluid)
        width: Output width in pixels
        height: Output height in pixels
        time_val: Animation time value
        color_mode: Color palette (0-3)

    Returns:
        PIL Image of the rendered effect
    """
    if effect_name not in EFFECTS:
        raise ValueError(f"Unknown effect: {effect_name}. Available: {list(EFFECTS.keys())}")

    effect = EFFECTS[effect_name]

    # Create headless renderer
    renderer = GLRenderer(width, height, headless=True)

    # Load shader
    program = renderer.load_shader(effect['shader'])

    # Set up uniforms
    uniforms = ShaderUniforms()
    uniforms.set_resolution(width, height)
    uniforms.iTime = time_val
    uniforms.iParams = effect['params']
    uniforms.iColorMode = color_mode

    # Render
    arr = renderer.render_to_array(program, uniforms.to_dict())
    img = Image.fromarray(arr, 'RGBA')

    return img


def render_effect_grid(width: int = 1600, height: int = 1200,
                       time_val: float = 2.0) -> Image.Image:
    """Render all effects in a grid.

    Args:
        width: Total output width
        height: Total output height
        time_val: Animation time value

    Returns:
        PIL Image with all effects in a 3x2 grid
    """
    # Calculate cell size (3 columns, 2 rows for 5 effects + info)
    cell_w = width // 3
    cell_h = height // 2

    # Create output image
    grid = Image.new('RGB', (width, height), (20, 20, 30))

    # Render each effect
    effects_list = list(EFFECTS.keys())
    positions = [
        (0, 0), (cell_w, 0), (cell_w * 2, 0),
        (0, cell_h), (cell_w, cell_h)
    ]

    for i, effect_name in enumerate(effects_list):
        print(f"  Rendering {effect_name}...")
        img = render_effect(effect_name, cell_w, cell_h, time_val)
        img = img.convert('RGB')
        grid.paste(img, positions[i])

    # Add labels
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(grid)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 24)
        except Exception:
            font = ImageFont.load_default()

        for i, effect_name in enumerate(effects_list):
            x, y = positions[i]
            # Draw label with shadow
            draw.text((x + 12, y + 12), effect_name.upper(), fill=(0, 0, 0), font=font)
            draw.text((x + 10, y + 10), effect_name.upper(), fill=(255, 255, 255), font=font)

        # Add info in 6th cell
        info_x, info_y = cell_w * 2, cell_h
        info_text = "GPU Effect Library\nPhase 4\n\n5 GLSL Shaders:\n- Plasma\n- Spiral\n- Tunnel\n- Lissajous\n- Fluid"
        draw.text((info_x + 20, info_y + 20), info_text, fill=(200, 200, 200), font=font)

    except Exception as e:
        print(f"Warning: Could not add labels: {e}")

    return grid


def run_effect_test(effect_name: str, duration: float = 3.0):
    """Run test for a single effect by rendering multiple frames.

    Args:
        effect_name: Name of the effect to test
        duration: Duration to simulate in seconds
    """
    print(f"\nTesting {effect_name}...")
    effect = EFFECTS[effect_name]
    print(f"  Description: {effect['description']}")
    print(f"  Shader: {effect['shader']}")
    print(f"  Parameters: {effect['params']}")

    # Test rendering multiple frames
    frames = 30
    start = time.time()

    for i in range(frames):
        t = i / frames * duration
        render_effect(effect_name, 640, 480, t)

    elapsed = time.time() - start
    fps = frames / elapsed
    print(f"  Rendered {frames} frames in {elapsed:.2f}s = {fps:.1f} FPS")

    return True


def main():
    parser = argparse.ArgumentParser(description='Test GPU effect library')
    parser.add_argument('--effect', choices=list(EFFECTS.keys()),
                        help='Test specific effect')
    parser.add_argument('--output', '-o', help='Save output image to file')
    parser.add_argument('--grid', action='store_true',
                        help='Render all effects in a grid')
    parser.add_argument('--width', type=int, default=800)
    parser.add_argument('--height', type=int, default=600)
    parser.add_argument('--time', type=float, default=2.0,
                        help='Animation time value')
    parser.add_argument('--color-mode', type=int, default=0, choices=[0, 1, 2, 3],
                        help='Color palette (0-3)')
    args = parser.parse_args()

    print("=" * 60)
    print("GPU EFFECT LIBRARY TEST (Phase 4)")
    print("=" * 60)

    if args.grid:
        print("\nRendering effect grid...")
        img = render_effect_grid(args.width * 2, args.height * 2, args.time)
        output = args.output or 'effects_grid.png'
        img.save(output)
        print(f"\nGrid saved to: {output}")

    elif args.effect:
        print(f"\nRendering {args.effect}...")
        img = render_effect(args.effect, args.width, args.height,
                           args.time, args.color_mode)
        if args.output:
            img.save(args.output)
            print(f"Saved to: {args.output}")
        else:
            run_effect_test(args.effect)

    else:
        # Test all effects
        print("\nTesting all effects...")
        for effect_name in EFFECTS:
            try:
                run_effect_test(effect_name)
                print(f"  ✓ {effect_name} passed")
            except Exception as e:
                print(f"  ✗ {effect_name} FAILED: {e}")
                return 1

        print("\n" + "=" * 60)
        print("✓ All effect tests passed!")
        print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
