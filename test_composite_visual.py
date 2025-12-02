#!/usr/bin/env python3
"""Quick visual test of composite animations."""

import time
from atari_style.demos.visualizers.screensaver import (
    PlasmaLissajous,
    FluxSpiral,
    LissajousPlasma
)
from atari_style.core.renderer import Renderer


def run_composite_visual(composite, name, duration=5.0):
    """Run visual test for a single composite animation."""
    print(f"\nTesting {name}...")
    print(f"  Source: {type(composite.source).__name__}")
    print(f"  Target: {type(composite.target).__name__}")
    
    renderer = composite.renderer
    
    try:
        renderer.enter_fullscreen()
        renderer.clear_screen()
        
        start = time.time()
        frames = 0
        
        while time.time() - start < duration:
            t = time.time() - start
            
            # Clear buffer
            renderer.clear_buffer()
            
            # Draw composite
            composite.draw(t)
            
            # Show composite name and params
            info = composite.get_param_info()
            y = 1
            for param in info:
                renderer.draw_text(2, y, param)
                y += 1
            
            # Render
            renderer.render()
            
            # Update
            composite.update(0.033)
            
            time.sleep(0.033)
            frames += 1
        
        fps = frames / duration
        print(f"  ✓ Rendered {frames} frames in {duration:.1f}s = {fps:.1f} FPS")
        
    finally:
        renderer.exit_fullscreen()


def main():
    """Run visual tests for all composites."""
    renderer = Renderer()
    
    print("="*60)
    print("COMPOSITE ANIMATION VISUAL TESTS")
    print("="*60)
    print("\nEach animation will run for 5 seconds.")
    print("Press Ctrl+C to skip to next animation.\n")
    
    composites = [
        (PlasmaLissajous(renderer), "Plasma → Lissajous"),
        (FluxSpiral(renderer), "Flux → Spiral"),
        (LissajousPlasma(renderer), "Lissajous → Plasma"),
    ]
    
    for composite, name in composites:
        try:
            run_composite_visual(composite, name)
            time.sleep(1)  # Brief pause between animations
        except KeyboardInterrupt:
            print(f"\n  Skipped {name}")
            continue
    
    print("\n" + "="*60)
    print("✓ All composite animation tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
