"""Auto-demo mode for screensaver - smooth parameter sweeps without user input."""
import time
import math
import os
from atari_style.demos.visualizers.screensaver import ScreenSaver


class ScreenSaverDemo(ScreenSaver):
    """Screensaver with automatic parameter animation for recording."""

    def __init__(self):
        super().__init__()
        self.demo_time = 0
        self.animation_duration = 25  # seconds per animation
        self.param_cycle_speed = 0.3  # How fast parameters oscillate

    def auto_adjust_params(self, dt: float):
        """Automatically adjust parameters in smooth sinusoidal patterns."""
        self.demo_time += dt

        anim = self.animations[self.current_animation]

        # Different parameter patterns for each animation
        if self.current_animation == 0:  # Lissajous
            # Sweep frequencies smoothly
            t = self.demo_time * self.param_cycle_speed
            anim.a = 2 + math.sin(t) * 2  # Freq X: 2-4
            anim.b = 3 + math.sin(t * 1.3) * 2  # Freq Y: 1-5
            anim.delta = math.sin(t * 0.5) * math.pi  # Phase sweep

        elif self.current_animation == 1:  # Spiral
            t = self.demo_time * self.param_cycle_speed
            anim.num_spirals = int(3 + math.sin(t) * 2)  # 1-5 spirals
            anim.rotation_speed = 1 + math.sin(t * 1.5) * 0.5
            anim.tightness = 8 + math.sin(t * 0.7) * 4

        elif self.current_animation == 2:  # Wave Circles
            t = self.demo_time * self.param_cycle_speed
            anim.num_circles = int(15 + math.sin(t) * 8)  # 7-23 circles
            anim.wave_amplitude = 3 + math.sin(t * 1.2) * 2
            anim.wave_frequency = 0.8 + math.sin(t * 0.8) * 0.4

        elif self.current_animation == 3:  # Plasma
            t = self.demo_time * self.param_cycle_speed
            anim.freq_x = 0.1 + math.sin(t) * 0.05
            anim.freq_y = 0.1 + math.sin(t * 1.1) * 0.05
            anim.freq_diag = 0.08 + math.sin(t * 0.9) * 0.04

        elif self.current_animation == 4:  # Mandelbrot
            t = self.demo_time * self.param_cycle_speed * 0.3  # Slower for Mandelbrot
            # Zoom into interesting region
            anim.zoom = 1 + t * 2  # Gradual zoom
            anim.center_x = -0.75 + math.sin(t * 0.5) * 0.1
            anim.center_y = math.sin(t * 0.3) * 0.1

        elif self.current_animation == 5:  # Fluid Lattice
            t = self.demo_time * self.param_cycle_speed
            # Lower rain rate for distinct drops, sweep damping for wave decay
            anim.rain_rate = 0.15 + math.sin(t) * 0.1  # Range: 0.05-0.25 (sparse drops)
            anim.wave_speed = 0.4 + math.sin(t * 1.2) * 0.15  # Range: 0.25-0.55
            anim.drop_strength = 12 + math.sin(t * 0.8) * 4  # Range: 8-16 (strong splashes)
            anim.damping = 0.88 + math.sin(t * 0.5) * 0.05  # Range: 0.83-0.93 (faster decay)

        elif self.current_animation == 6:  # Particle Swarm
            t = self.demo_time * self.param_cycle_speed
            anim.max_speed = 2 + math.sin(t) * 1
            anim.cohesion_factor = 0.8 + math.sin(t * 1.1) * 0.5
            anim.separation_factor = 1.5 + math.sin(t * 0.9) * 0.8

        elif self.current_animation == 7:  # Tunnel Vision
            t = self.demo_time * self.param_cycle_speed
            anim.depth_speed = 1.5 + math.sin(t) * 1
            anim.rotation_speed = math.sin(t * 0.7) * 1.5
            anim.tunnel_size = 1.2 + math.sin(t * 0.5) * 0.5

    def run_demo(self, total_duration: int = 200):
        """Run automated demo for specified duration."""
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            start_time = time.time()
            last_time = start_time
            last_switch = start_time

            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                # Check total duration
                elapsed = current_time - start_time
                if elapsed >= total_duration:
                    break

                # Auto-switch animations
                if current_time - last_switch >= self.animation_duration:
                    self.current_animation = (self.current_animation + 1) % len(self.animations)
                    last_switch = current_time
                    self.demo_time = 0  # Reset param time for new animation

                # Auto-adjust parameters
                self.auto_adjust_params(dt)

                # Draw and update
                self.draw()
                self.update(dt)

                # Still check for quit
                self.handle_input()

                time.sleep(0.016)  # ~60 FPS

        finally:
            self.renderer.exit_fullscreen()

    def run_single_mode_demo(self, mode: int, duration: int):
        """Run a single animation mode without auto-switching.

        Args:
            mode: Animation mode index (0-7)
            duration: How long to run in seconds
        """
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()

            start_time = time.time()
            last_time = start_time

            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                # Check total duration
                elapsed = current_time - start_time
                if elapsed >= duration:
                    break

                # Auto-adjust parameters
                self.auto_adjust_params(dt)

                # Draw and update
                self.draw()
                self.update(dt)

                # Still check for quit
                self.handle_input()

                time.sleep(0.016)  # ~60 FPS

        finally:
            self.renderer.exit_fullscreen()


def run_demo(duration: int = 200):
    """Entry point for demo mode."""
    demo = ScreenSaverDemo()
    demo.run_demo(duration)


def run_lissajous_demo(duration: int = 60):
    """Run Lissajous curve animation demo.

    Args:
        duration: How long to run in seconds (default: 60)
    """
    demo = ScreenSaverDemo()
    demo.current_animation = 0
    demo.run_single_mode_demo(0, duration)


def run_spiral_demo(duration: int = 60):
    """Run spiral animation demo.

    Args:
        duration: How long to run in seconds (default: 60)
    """
    demo = ScreenSaverDemo()
    demo.current_animation = 1
    demo.run_single_mode_demo(1, duration)


def run_circlewave_demo(duration: int = 60):
    """Run circle wave animation demo.

    Args:
        duration: How long to run in seconds (default: 60)
    """
    demo = ScreenSaverDemo()
    demo.current_animation = 2
    demo.run_single_mode_demo(2, duration)


def run_plasma_demo(duration: int = 60):
    """Run plasma animation demo.

    Args:
        duration: How long to run in seconds (default: 60)
    """
    demo = ScreenSaverDemo()
    demo.current_animation = 3
    demo.run_single_mode_demo(3, duration)


def run_mandelbrot_demo(duration: int = 60):
    """Run Mandelbrot zoomer animation demo.

    Args:
        duration: How long to run in seconds (default: 60)
    """
    demo = ScreenSaverDemo()
    demo.current_animation = 4
    demo.run_single_mode_demo(4, duration)


def run_fluidlattice_demo(duration: int = 60):
    """Run fluid lattice animation demo.

    Args:
        duration: How long to run in seconds (default: 60)
    """
    demo = ScreenSaverDemo()
    demo.current_animation = 5
    demo.run_single_mode_demo(5, duration)


def run_particleswarm_demo(duration: int = 60):
    """Run particle swarm animation demo.

    Args:
        duration: How long to run in seconds (default: 60)
    """
    demo = ScreenSaverDemo()
    demo.current_animation = 6
    demo.run_single_mode_demo(6, duration)


def run_tunnelvision_demo(duration: int = 60):
    """Run tunnel vision animation demo.

    Args:
        duration: How long to run in seconds (default: 60)
    """
    demo = ScreenSaverDemo()
    demo.current_animation = 7
    demo.run_single_mode_demo(7, duration)


def capture_thumbnail(mode: int, output_path: str, setup_time: float = 2.0) -> bool:
    """Capture a single frame thumbnail for a screensaver mode.

    This function runs a specific animation mode for a brief setup time to let it
    reach an interesting state, then captures the current frame as a PNG image.

    Args:
        mode: Animation mode index (0-7):
            0 - Lissajous Curve
            1 - Spiral
            2 - Wave Circles
            3 - Plasma
            4 - Mandelbrot
            5 - Fluid Lattice
            6 - Particle Swarm
            7 - Tunnel Vision
        output_path: Path where the PNG thumbnail will be saved
        setup_time: How long to run the animation before capturing (default: 2.0 seconds)

    Returns:
        True if capture was successful, False otherwise

    Example:
        >>> capture_thumbnail(0, "thumbnails/lissajous.png", setup_time=3.0)
        >>> capture_thumbnail(4, "thumbnails/mandelbrot.png", setup_time=5.0)
    """
    if not 0 <= mode < 8:
        print(f"Error: mode must be 0-7, got {mode}")
        return False

    try:
        demo = ScreenSaverDemo()
        demo.current_animation = mode
        demo.running = True

        # Run the animation for setup_time to get an interesting state
        start_time = time.time()
        last_time = start_time

        while time.time() - start_time < setup_time:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Auto-adjust parameters
            demo.auto_adjust_params(dt)

            # Clear and draw the frame
            demo.renderer.clear_buffer()
            demo.draw()
            demo.update(dt)

            time.sleep(0.016)  # ~60 FPS

        # Capture the current frame
        success = demo.renderer.save_screenshot(output_path)

        if success:
            print(f"Thumbnail captured: {output_path}")
        else:
            print(f"Failed to capture thumbnail for mode {mode}")

        return success

    except Exception as e:
        print(f"Error capturing thumbnail: {e}")
        return False


def capture_all_thumbnails(output_dir: str = "thumbnails", setup_time: float = 3.0) -> int:
    """Capture thumbnails for all 8 screensaver modes.

    Args:
        output_dir: Directory where thumbnails will be saved (default: "thumbnails")
        setup_time: How long to run each animation before capturing (default: 3.0 seconds)

    Returns:
        Number of thumbnails successfully captured

    Example:
        >>> capture_all_thumbnails("./screenshots", setup_time=2.5)
    """
    mode_names = [
        "lissajous",
        "spiral",
        "wave_circles",
        "plasma",
        "mandelbrot",
        "fluid_lattice",
        "particle_swarm",
        "tunnel_vision"
    ]

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    success_count = 0
    for mode, name in enumerate(mode_names):
        output_path = os.path.join(output_dir, f"{name}.png")
        print(f"Capturing {name} (mode {mode})...")

        if capture_thumbnail(mode, output_path, setup_time):
            success_count += 1
        else:
            print(f"Failed to capture {name}")

        # Small delay between captures
        time.sleep(0.5)

    print(f"\nCaptured {success_count}/{len(mode_names)} thumbnails")
    return success_count


if __name__ == "__main__":
    run_demo()
