"""Test script for GPU composite animations (Phase 5).

Tests composite shaders: plasma_lissajous, flux_spiral, lissajous_plasma.

Usage:
    python -m atari_style.core.gl.test_composites
    python -m atari_style.core.gl.test_composites --composite plasma_lissajous
    python -m atari_style.core.gl.test_composites --output composite_demo.png
    python -m atari_style.core.gl.test_composites --grid
"""

import sys
import time
import argparse

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required: pip install Pillow")
    sys.exit(1)

from .composites import CompositeManager, COMPOSITES, list_composites, get_composite_info


def render_composite_grid(width: int = 1600, height: int = 600,
                          time_val: float = 2.0) -> Image.Image:
    """Render all composites in a horizontal grid.

    Args:
        width: Total output width
        height: Total output height
        time_val: Animation time value

    Returns:
        PIL Image with all composites side by side
    """
    # Calculate cell size (3 columns for 3 composites)
    num_composites = len(COMPOSITES)
    cell_w = width // num_composites
    cell_h = height

    # Create output image
    grid = Image.new('RGB', (width, height), (20, 20, 30))

    # Create manager
    manager = CompositeManager(cell_w, cell_h)

    # Render each composite
    composites_list = list_composites()

    for i, composite_name in enumerate(composites_list):
        print(f"  Rendering {composite_name}...")
        img = manager.render_frame(composite_name, time_val)
        img = img.convert('RGB')
        grid.paste(img, (i * cell_w, 0))

    # Add labels
    try:
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(grid)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 20)
        except Exception:
            font = ImageFont.load_default()

        for i, composite_name in enumerate(composites_list):
            x = i * cell_w
            config = COMPOSITES[composite_name]
            label = config.name

            # Draw label with shadow
            draw.text((x + 12, 12), label, fill=(0, 0, 0), font=font)
            draw.text((x + 10, 10), label, fill=(255, 255, 255), font=font)

    except Exception as e:
        print(f"Warning: Could not add labels: {e}")

    return grid


def run_composite_test(composite_name: str, duration: float = 3.0):
    """Run test for a single composite by rendering multiple frames.

    Args:
        composite_name: Name of the composite to test
        duration: Duration to simulate in seconds
    """
    print(f"\nTesting {composite_name}...")
    info = get_composite_info(composite_name)

    print(f"  Name: {info['name']}")
    print(f"  Description: {info['description']}")
    print(f"  Shader: {info['shader']}")
    print(f"  Parameters: {info['params']}")

    # Test rendering multiple frames
    frames = 30
    manager = CompositeManager(640, 480)

    start = time.time()

    for i in range(frames):
        t = i / frames * duration
        manager.render_frame(composite_name, t)

    elapsed = time.time() - start
    fps = frames / elapsed
    print(f"  Rendered {frames} frames in {elapsed:.2f}s = {fps:.1f} FPS")

    return True


def run_benchmark(composite_name: str):
    """Run performance benchmark for a composite.

    Args:
        composite_name: Name of composite to benchmark
    """
    print(f"\nBenchmarking {composite_name}...")

    manager = CompositeManager(800, 600)
    results = manager.benchmark(composite_name, frames=60)

    print(f"  Frames: {results['frames']}")
    print(f"  Total time: {results['total_time']:.2f}s")
    print(f"  Average FPS: {results['fps']:.1f}")
    print(f"  Frame time: {results['avg_frame_time']*1000:.1f}ms avg, "
          f"{results['min_time']*1000:.1f}ms min, {results['max_time']*1000:.1f}ms max")

    return results


def main():
    parser = argparse.ArgumentParser(description='Test GPU composite animations')
    parser.add_argument('--composite', choices=list_composites(),
                        help='Test specific composite')
    parser.add_argument('--output', '-o', help='Save output image to file')
    parser.add_argument('--grid', action='store_true',
                        help='Render all composites in a grid')
    parser.add_argument('--benchmark', action='store_true',
                        help='Run performance benchmark')
    parser.add_argument('--width', type=int, default=800)
    parser.add_argument('--height', type=int, default=600)
    parser.add_argument('--time', type=float, default=2.0,
                        help='Animation time value')
    parser.add_argument('--color-mode', type=int, default=0, choices=[0, 1, 2, 3],
                        help='Color palette (0-3)')
    args = parser.parse_args()

    print("=" * 60)
    print("GPU COMPOSITE ANIMATION TEST (Phase 5)")
    print("=" * 60)

    if args.grid:
        print("\nRendering composite grid...")
        img = render_composite_grid(args.width * 2, args.height, args.time)
        output = args.output or 'composites_grid.png'
        img.save(output)
        print(f"\nGrid saved to: {output}")

    elif args.composite:
        if args.benchmark:
            run_benchmark(args.composite)
        elif args.output:
            print(f"\nRendering {args.composite}...")
            manager = CompositeManager(args.width, args.height)
            img = manager.render_frame(args.composite, args.time,
                                        color_mode=args.color_mode)
            img.save(args.output)
            print(f"Saved to: {args.output}")
        else:
            run_composite_test(args.composite)

    else:
        # Test all composites
        print("\nTesting all composites...")
        all_passed = True

        for composite_name in list_composites():
            try:
                run_composite_test(composite_name)
                print(f"  PASS: {composite_name}")
            except Exception as e:
                print(f"  FAIL: {composite_name}: {e}")
                all_passed = False

        if args.benchmark:
            print("\n" + "-" * 60)
            print("PERFORMANCE BENCHMARKS")
            print("-" * 60)
            for composite_name in list_composites():
                run_benchmark(composite_name)

        print("\n" + "=" * 60)
        if all_passed:
            print("All composite tests passed!")
        else:
            print("Some tests FAILED")
            return 1
        print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
