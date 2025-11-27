"""Auto-demo mode for screensaver - smooth parameter sweeps without user input."""
import time
import math
import os
from atari_style.demos.screensaver import ScreenSaver


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
            anim.rain_rate = 0.5 + math.sin(t) * 0.4
            anim.wave_speed = 0.3 + math.sin(t * 1.2) * 0.2
            anim.drop_power = 10 + math.sin(t * 0.8) * 5

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


if __name__ == "__main__":
    run_demo()
