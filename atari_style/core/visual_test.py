#!/usr/bin/env python3
"""Visual regression testing framework for terminal demos.

Generates baseline images from demos and compares against current renders
to detect unintended visual changes.

Usage:
    # Generate baseline images
    python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10

    # Compare against baseline
    python -m atari_style.core.visual_test compare joystick_test

    # Generate diff images
    python -m atari_style.core.visual_test compare joystick_test --save-diff
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

try:
    from PIL import Image, ImageChops, ImageDraw
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageChops = None
    ImageDraw = None
    np = None

from .scripted_input import ScriptedInputHandler, InputScript
from .headless_renderer import HeadlessRenderer
from .demo_video import DEMO_REGISTRY


def render_demo_frames(
    demo_factory,
    renderer: HeadlessRenderer,
    input_handler: ScriptedInputHandler,
    total_frames: int,
) -> List['Image.Image']:
    """Render frames from a demo using scripted input.

    Args:
        demo_factory: Factory function(renderer, input_handler) -> demo
        renderer: HeadlessRenderer instance
        input_handler: ScriptedInputHandler with loaded script
        total_frames: Number of frames to render

    Returns:
        List of PIL Image objects
    """
    demo = demo_factory(renderer, input_handler)
    frame_images = []

    # Start script playback
    input_handler.start()

    # Get frame time from script FPS
    frame_time = 1.0 / input_handler.script.fps

    # Render each frame
    for frame_num in range(total_frames):
        # Update input handler time
        input_handler.current_time = frame_num * frame_time

        # Render frame
        demo.draw()

        # Capture as image
        frame_images.append(renderer.to_image())

    return frame_images


class VisualTestConfig:
    """Configuration for visual regression tests."""

    def __init__(
        self,
        baseline_dir: Path = None,
        diff_dir: Path = None,
        threshold: float = 0.01,
        allow_antialiasing: bool = True,
    ):
        """Initialize visual test configuration.

        Args:
            baseline_dir: Directory containing baseline images
            diff_dir: Directory for diff images
            threshold: Maximum allowed pixel difference ratio (0.0-1.0)
            allow_antialiasing: Allow minor anti-aliasing differences
        """
        if baseline_dir is None:
            baseline_dir = Path(__file__).parent.parent.parent / "baselines"
        if diff_dir is None:
            diff_dir = Path(__file__).parent.parent.parent / "baselines" / "diffs"

        self.baseline_dir = Path(baseline_dir)
        self.diff_dir = Path(diff_dir)
        self.threshold = threshold
        self.allow_antialiasing = allow_antialiasing

        # Create directories if needed
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.diff_dir.mkdir(parents=True, exist_ok=True)


class VisualTestResult:
    """Result of a visual comparison test."""

    def __init__(
        self,
        demo_name: str,
        frame_number: int,
        passed: bool,
        diff_ratio: float = 0.0,
        diff_image_path: Optional[Path] = None,
        error: Optional[str] = None,
    ):
        self.demo_name = demo_name
        self.frame_number = frame_number
        self.passed = passed
        self.diff_ratio = diff_ratio
        self.diff_image_path = diff_image_path
        self.error = error

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"<VisualTestResult {self.demo_name} frame {self.frame_number}: {status} (diff: {self.diff_ratio:.4f})>"


def generate_baseline(
    demo_name: str,
    script_path: str,
    frames: List[int],
    config: VisualTestConfig,
    width: int = 120,
    height: int = 40,
) -> bool:
    """Generate baseline images for a demo.

    Args:
        demo_name: Name of registered demo
        script_path: Path to input script JSON
        frames: List of frame numbers to capture
        config: Visual test configuration
        width: Terminal width in characters
        height: Terminal height in characters

    Returns:
        True if successful, False otherwise
    """
    if not PIL_AVAILABLE:
        print("ERROR: PIL/Pillow is required. Install with: pip install Pillow numpy")
        return False

    if demo_name not in DEMO_REGISTRY:
        print(f"ERROR: Unknown demo '{demo_name}'")
        print(f"Available demos: {', '.join(DEMO_REGISTRY.keys())}")
        return False

    # Create demo-specific baseline directory
    demo_baseline_dir = config.baseline_dir / demo_name
    demo_baseline_dir.mkdir(parents=True, exist_ok=True)

    # Load input script
    script = InputScript.from_file(script_path)

    # Render frames
    print(f"Generating baselines for {demo_name}...")
    print(f"Frames: {frames}")
    print(f"Output directory: {demo_baseline_dir}")

    renderer = HeadlessRenderer(width=width, height=height)
    input_handler = ScriptedInputHandler(script=script)
    demo_factory = DEMO_REGISTRY[demo_name]['factory']

    frame_images = render_demo_frames(
        demo_factory=demo_factory,
        renderer=renderer,
        input_handler=input_handler,
        total_frames=max(frames) + 1,
    )

    # Save selected frames as baselines
    saved_count = 0
    for frame_num in frames:
        if frame_num >= len(frame_images):
            print(f"WARNING: Frame {frame_num} not available (only {len(frame_images)} frames rendered)")
            continue

        baseline_path = demo_baseline_dir / f"frame_{frame_num:04d}.png"
        frame_images[frame_num].save(baseline_path)
        print(f"  Saved: {baseline_path.name}")
        saved_count += 1

    # Save metadata
    metadata = {
        'demo_name': demo_name,
        'script_path': script_path,
        'frames': frames,
        'width': width,
        'height': height,
        'version': '1.0',
    }
    metadata_path = demo_baseline_dir / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nGenerated {saved_count} baseline images")
    return saved_count > 0


def compare_images(
    baseline_img: 'Image.Image',
    current_img: 'Image.Image',
    allow_antialiasing: bool = True,
) -> Tuple[float, 'Image.Image']:
    """Compare two images and generate diff visualization.

    Args:
        baseline_img: Reference image
        current_img: Current render
        allow_antialiasing: Tolerate minor anti-aliasing differences

    Returns:
        Tuple of (diff_ratio, diff_image)
        diff_ratio: Fraction of differing pixels (0.0-1.0)
        diff_image: Highlighted diff visualization
    """
    if baseline_img.size != current_img.size:
        raise ValueError(f"Image size mismatch: {baseline_img.size} vs {current_img.size}")

    # Convert to RGB if needed
    if baseline_img.mode != 'RGB':
        baseline_img = baseline_img.convert('RGB')
    if current_img.mode != 'RGB':
        current_img = current_img.convert('RGB')

    # Calculate pixel-wise difference
    diff = ImageChops.difference(baseline_img, current_img)
    diff_array = np.array(diff)

    # Calculate per-pixel max channel difference
    pixel_diffs = diff_array.max(axis=2)

    if allow_antialiasing:
        # Tolerate small differences (< 10/255) that might be anti-aliasing
        threshold = 10
        significant_diff_mask = pixel_diffs > threshold
    else:
        # Any difference is significant
        significant_diff_mask = pixel_diffs > 0

    # Calculate diff ratio
    total_pixels = pixel_diffs.size
    diff_pixels = significant_diff_mask.sum()
    diff_ratio = diff_pixels / total_pixels

    # Generate visualization
    diff_visual = _create_diff_visualization(
        baseline_img,
        current_img,
        significant_diff_mask,
    )

    return diff_ratio, diff_visual


def _create_diff_visualization(
    baseline_img: 'Image.Image',
    current_img: 'Image.Image',
    diff_mask: 'np.ndarray',
) -> 'Image.Image':
    """Create a visual diff highlighting changed pixels.

    Args:
        baseline_img: Reference image
        current_img: Current render
        diff_mask: Boolean array marking different pixels

    Returns:
        Combined visualization image
    """
    width, height = baseline_img.size

    # Create side-by-side comparison
    result = Image.new('RGB', (width * 3, height))

    # Left: baseline
    result.paste(baseline_img, (0, 0))

    # Middle: current
    result.paste(current_img, (width, 0))

    # Right: diff overlay
    # Show current image with red highlights on differences
    diff_overlay = current_img.copy()
    diff_array = np.array(diff_overlay)

    # Highlight differences in red
    diff_array[diff_mask, 0] = 255  # Red channel
    diff_array[diff_mask, 1] = 0    # Green channel
    diff_array[diff_mask, 2] = 0    # Blue channel

    diff_overlay = Image.fromarray(diff_array)
    result.paste(diff_overlay, (width * 2, 0))

    # Add labels
    draw = ImageDraw.Draw(result)
    label_color = (255, 255, 0)  # Yellow
    draw.text((10, 10), "BASELINE", fill=label_color)
    draw.text((width + 10, 10), "CURRENT", fill=label_color)
    draw.text((width * 2 + 10, 10), "DIFF", fill=label_color)

    return result


def compare_baseline(
    demo_name: str,
    script_path: str,
    config: VisualTestConfig,
    save_diffs: bool = False,
    width: int = 120,
    height: int = 40,
) -> List[VisualTestResult]:
    """Compare current render against baseline images.

    Args:
        demo_name: Name of registered demo
        script_path: Path to input script JSON
        config: Visual test configuration
        save_diffs: Save diff images to disk
        width: Terminal width in characters
        height: Terminal height in characters

    Returns:
        List of test results
    """
    if not PIL_AVAILABLE:
        return [VisualTestResult(
            demo_name, 0, False,
            error="PIL/Pillow is required. Install with: pip install Pillow numpy"
        )]

    if demo_name not in DEMO_REGISTRY:
        return [VisualTestResult(
            demo_name, 0, False,
            error=f"Unknown demo '{demo_name}'"
        )]

    # Load baseline metadata
    demo_baseline_dir = config.baseline_dir / demo_name
    metadata_path = demo_baseline_dir / 'metadata.json'

    if not metadata_path.exists():
        return [VisualTestResult(
            demo_name, 0, False,
            error=f"No baseline found. Run 'generate' first."
        )]

    with open(metadata_path) as f:
        metadata = json.load(f)

    frames = metadata['frames']

    # Render current frames
    script = InputScript.from_file(script_path)
    renderer = HeadlessRenderer(width=width, height=height)
    input_handler = ScriptedInputHandler(script=script)
    demo_factory = DEMO_REGISTRY[demo_name]['factory']

    frame_images = render_demo_frames(
        demo_factory=demo_factory,
        renderer=renderer,
        input_handler=input_handler,
        total_frames=max(frames) + 1,
    )

    # Compare each frame
    results = []
    for frame_num in frames:
        baseline_path = demo_baseline_dir / f"frame_{frame_num:04d}.png"

        if not baseline_path.exists():
            results.append(VisualTestResult(
                demo_name, frame_num, False,
                error=f"Baseline image not found: {baseline_path}"
            ))
            continue

        if frame_num >= len(frame_images):
            results.append(VisualTestResult(
                demo_name, frame_num, False,
                error=f"Frame {frame_num} not rendered"
            ))
            continue

        # Load baseline
        baseline_img = Image.open(baseline_path)
        current_img = frame_images[frame_num]

        try:
            # Compare
            diff_ratio, diff_img = compare_images(
                baseline_img,
                current_img,
                allow_antialiasing=config.allow_antialiasing,
            )

            # Check threshold
            passed = diff_ratio <= config.threshold

            # Save diff if requested or if failed
            diff_path = None
            if save_diffs or not passed:
                diff_path = config.diff_dir / demo_name / f"diff_frame_{frame_num:04d}.png"
                diff_path.parent.mkdir(parents=True, exist_ok=True)
                diff_img.save(diff_path)

            results.append(VisualTestResult(
                demo_name, frame_num, passed,
                diff_ratio=diff_ratio,
                diff_image_path=diff_path,
            ))

        except Exception as e:
            results.append(VisualTestResult(
                demo_name, frame_num, False,
                error=str(e)
            ))

    return results


def print_results(results: List[VisualTestResult], verbose: bool = True):
    """Print test results summary.

    Args:
        results: List of test results
        verbose: Print detailed information
    """
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    print("\n" + "=" * 60)
    print("VISUAL REGRESSION TEST RESULTS")
    print("=" * 60)

    for result in results:
        if result.passed:
            status = "✓ PASS"
            color_code = "\033[92m"  # Green
        else:
            status = "✗ FAIL"
            color_code = "\033[91m"  # Red

        reset_code = "\033[0m"

        print(f"{color_code}{status}{reset_code} Frame {result.frame_number:4d}: diff={result.diff_ratio:.4f}")

        if verbose and result.error:
            print(f"       Error: {result.error}")
        if verbose and result.diff_image_path:
            print(f"       Diff: {result.diff_image_path}")

    print("=" * 60)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    print("=" * 60)

    return passed, failed


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Visual regression testing for terminal demos"
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Generate command
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate baseline images'
    )
    generate_parser.add_argument('demo', help='Demo name')
    generate_parser.add_argument(
        '--script',
        default='scripts/demos/joystick-demo.json',
        help='Input script path'
    )
    generate_parser.add_argument(
        '--frames',
        default='0,5,10',
        help='Comma-separated frame numbers'
    )
    generate_parser.add_argument(
        '--baseline-dir',
        help='Baseline directory'
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        'compare',
        help='Compare against baseline'
    )
    compare_parser.add_argument('demo', help='Demo name')
    compare_parser.add_argument(
        '--script',
        default='scripts/demos/joystick-demo.json',
        help='Input script path'
    )
    compare_parser.add_argument(
        '--save-diff',
        action='store_true',
        help='Save diff images'
    )
    compare_parser.add_argument(
        '--threshold',
        type=float,
        default=0.01,
        help='Diff threshold (0.0-1.0)'
    )
    compare_parser.add_argument(
        '--baseline-dir',
        help='Baseline directory'
    )
    compare_parser.add_argument(
        '--no-antialiasing',
        action='store_true',
        help='Disable anti-aliasing tolerance'
    )

    args = parser.parse_args()

    # Create config
    config = VisualTestConfig(
        baseline_dir=Path(args.baseline_dir) if hasattr(args, 'baseline_dir') and args.baseline_dir else None,
        threshold=args.threshold if hasattr(args, 'threshold') else 0.01,
        allow_antialiasing=not args.no_antialiasing if hasattr(args, 'no_antialiasing') else True,
    )

    if args.command == 'generate':
        frames = [int(f.strip()) for f in args.frames.split(',')]
        success = generate_baseline(
            args.demo,
            args.script,
            frames,
            config,
        )
        sys.exit(0 if success else 1)

    elif args.command == 'compare':
        results = compare_baseline(
            args.demo,
            args.script,
            config,
            save_diffs=args.save_diff,
        )
        passed, failed = print_results(results)
        sys.exit(0 if failed == 0 else 1)
