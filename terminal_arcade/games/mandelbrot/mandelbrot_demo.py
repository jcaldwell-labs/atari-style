"""Auto-demo mode for Mandelbrot - tours interesting regions with smooth transitions."""
import time
import math
import signal
from .game import MandelbrotExplorer


class MandelbrotDemo(MandelbrotExplorer):
    """Mandelbrot explorer with automatic navigation to interesting regions."""

    # Interesting locations in the Mandelbrot set
    # (center_x, center_y, target_zoom, duration, palette, description)
    # Design: Follow edges longer at each zoom level before going deeper
    # Pan and scan, zoom a bit, pan and scan more
    TOUR_LOCATIONS = [
        # === OVERVIEW - Pan along the entire boundary ===
        (-0.5, 0.0, 1.5, 8, 'electric', 'Overview'),
        (-0.2, 0.0, 1.3, 5, 'electric', 'Pan East'),
        (0.1, 0.3, 1.3, 5, 'electric', 'Pan Northeast'),
        (-0.3, 0.5, 1.3, 5, 'electric', 'Pan North'),
        (-0.7, 0.3, 1.3, 5, 'electric', 'Pan Northwest'),
        (-0.9, 0.0, 1.3, 5, 'electric', 'Pan West'),
        (-0.7, -0.3, 1.3, 5, 'electric', 'Pan Southwest'),
        (-0.3, -0.5, 1.3, 5, 'electric', 'Pan South'),

        # === SEAHORSE VALLEY - Follow the edge extensively ===
        (-0.6, 0.0, 0.6, 5, 'ocean', 'Approach Seahorse'),
        # Pan along the edge at medium zoom
        (-0.7, 0.1, 0.4, 5, 'ocean', 'Edge Pan 1'),
        (-0.72, 0.15, 0.4, 5, 'ocean', 'Edge Pan 2'),
        (-0.74, 0.18, 0.4, 5, 'ocean', 'Edge Pan 3'),
        (-0.745, 0.186, 0.4, 4, 'ocean', 'Lock Seahorse'),
        # Zoom in a bit, then pan more
        (-0.745, 0.186, 0.15, 5, 'ocean', 'Zoom Level 1'),
        (-0.746, 0.184, 0.15, 5, 'ocean', 'Pan at Zoom 1'),
        (-0.744, 0.188, 0.15, 5, 'ocean', 'Pan at Zoom 1'),
        (-0.745, 0.186, 0.15, 4, 'ocean', 'Return Center'),
        # Zoom deeper, pan more
        (-0.745, 0.186, 0.05, 5, 'ocean', 'Zoom Level 2'),
        (-0.7452, 0.1125, 0.05, 5, 'ocean', 'Pan at Zoom 2'),
        (-0.7454, 0.1129, 0.05, 5, 'ocean', 'Pan at Zoom 2'),
        # Final deep zoom
        (-0.7453, 0.1127, 0.015, 6, 'ocean', 'Deep Seahorse'),

        # === PULL BACK ===
        (-0.5, 0.0, 0.8, 4, 'fire', 'Pull Back'),

        # === ELEPHANT VALLEY - Follow trunk edges ===
        (0.0, 0.0, 0.5, 5, 'fire', 'Approach Elephant'),
        # Pan along the boundary
        (0.15, 0.05, 0.4, 5, 'fire', 'Edge Pan 1'),
        (0.25, 0.02, 0.4, 5, 'fire', 'Edge Pan 2'),
        (0.285, 0.0, 0.4, 4, 'fire', 'Lock Elephant'),
        # Zoom and pan
        (0.285, 0.0, 0.12, 5, 'fire', 'Zoom Level 1'),
        (0.284, 0.005, 0.12, 5, 'fire', 'Pan at Zoom 1'),
        (0.286, -0.005, 0.12, 5, 'fire', 'Pan at Zoom 1'),
        # Deeper zoom and pan
        (0.285, 0.0, 0.04, 5, 'fire', 'Zoom Level 2'),
        (0.2852, 0.008, 0.04, 5, 'fire', 'Pan at Zoom 2'),
        (0.2858, 0.012, 0.04, 5, 'fire', 'Pan at Zoom 2'),
        # Final deep zoom
        (0.2855, 0.01, 0.01, 6, 'fire', 'Deep Elephant'),

        # === PULL BACK ===
        (-0.5, 0.1, 0.6, 4, 'psychedelic', 'Pull Back'),

        # === SPIRAL REGION - Trace spirals ===
        (-0.72, 0.19, 0.25, 5, 'psychedelic', 'Approach Spiral'),
        # Pan along spiral edge
        (-0.724, 0.188, 0.2, 5, 'psychedelic', 'Edge Pan 1'),
        (-0.728, 0.190, 0.2, 5, 'psychedelic', 'Edge Pan 2'),
        (-0.7269, 0.1889, 0.2, 4, 'psychedelic', 'Lock Spiral'),
        # Zoom and trace
        (-0.7269, 0.1889, 0.06, 5, 'psychedelic', 'Zoom Level 1'),
        (-0.7268, 0.1890, 0.06, 5, 'psychedelic', 'Trace Spiral'),
        (-0.7270, 0.1888, 0.06, 5, 'psychedelic', 'Trace Spiral'),
        # Deep spiral
        (-0.7269, 0.1889, 0.015, 6, 'psychedelic', 'Zoom Level 2'),
        (-0.7269, 0.1889, 0.004, 7, 'psychedelic', 'Deep Spiral'),

        # === MINI MANDELBROT - Approach slowly ===
        (-0.9, 0.0, 0.4, 4, 'copper', 'Scout West'),
        (-1.1, 0.0, 0.35, 5, 'copper', 'Pan West'),
        (-1.25, 0.0, 0.3, 5, 'copper', 'Approach Mini'),
        # Pan around mini
        (-1.253, 0.002, 0.2, 5, 'copper', 'Edge Pan 1'),
        (-1.255, -0.002, 0.2, 5, 'copper', 'Edge Pan 2'),
        (-1.254, 0.0, 0.2, 4, 'copper', 'Lock Mini'),
        # Zoom into mini
        (-1.254, 0.0, 0.08, 5, 'copper', 'Zoom Level 1'),
        (-1.254, 0.0, 0.025, 6, 'copper', 'Mini Mandelbrot'),

        # === RETURN HOME ===
        (-0.8, 0.0, 0.5, 4, 'electric', 'Return Journey'),
        (-0.5, 0.0, 1.0, 5, 'electric', 'Approaching Home'),
        (-0.5, 0.0, 1.5, 6, 'electric', 'Home'),
    ]

    def __init__(self):
        super().__init__()
        self.demo_time = 0
        self.location_index = 0
        self.location_time = 0
        self.transitioning = True

        # Fixed high iterations for detail
        self.max_iterations = 150

        # Color cycling always on, faster speed
        self.color_cycling = True
        self.cycle_speed = 0.08  # Faster cycling

        # Palette changes only every 15+ seconds
        self.last_palette_change = 0
        self.palette_change_interval = 15.0

        # Starting position
        self.start_x = self.center_x
        self.start_y = self.center_y
        self.start_zoom = self.zoom

        # Target from first location
        loc = self.TOUR_LOCATIONS[0]
        self.target_x = loc[0]
        self.target_y = loc[1]
        self.target_zoom = loc[2]
        self.transition_duration = loc[3]
        self.current_palette = loc[4]

    def smooth_interpolate(self, t):
        """Smooth easing function (ease-in-out)."""
        # Smoothstep for natural motion
        return t * t * (3 - 2 * t)

    def get_time_multiplier(self):
        """Calculate time multiplier based on fill_delta (rate of change).

        High delta = interesting (slow down)
        Low delta = stable/boring (speed up)
        """
        abs_delta = abs(self.fill_delta)

        if abs_delta > 5.0:
            # Rapidly changing = very interesting!
            return 0.6
        elif abs_delta > 2.0:
            # Moderate change = interesting
            return 0.8
        elif abs_delta < 0.5:
            # Stable/boring = speed up
            return 1.5
        else:
            # Normal range
            return 1.0

    def update_navigation(self, dt):
        """Update camera position and zoom smoothly.

        Uses fill_percentage to dynamically adjust timing:
        - Low fill (empty areas): advance faster
        - High fill (interesting areas): linger longer
        """
        # Apply dynamic time multiplier based on content density
        time_multiplier = self.get_time_multiplier()
        adjusted_dt = dt * time_multiplier

        self.location_time += adjusted_dt

        loc = self.TOUR_LOCATIONS[self.location_index]
        duration = loc[3]

        if self.location_time >= duration:
            # Move to next location
            self.location_index = (self.location_index + 1) % len(self.TOUR_LOCATIONS)
            self.location_time = 0

            # Store current as start
            self.start_x = self.center_x
            self.start_y = self.center_y
            self.start_zoom = self.zoom

            # Set new target
            new_loc = self.TOUR_LOCATIONS[self.location_index]
            self.target_x = new_loc[0]
            self.target_y = new_loc[1]
            self.target_zoom = new_loc[2]
            self.transition_duration = new_loc[3]

            # Only change palette if 15+ seconds have passed
            if self.demo_time - self.last_palette_change >= self.palette_change_interval:
                self.current_palette = new_loc[4]
                self.last_palette_change = self.demo_time

            return

        # Interpolate smoothly
        t = self.location_time / duration
        t_smooth = self.smooth_interpolate(t)

        # Linear interpolation for position
        self.center_x = self.start_x + (self.target_x - self.start_x) * t_smooth
        self.center_y = self.start_y + (self.target_y - self.start_y) * t_smooth

        # Logarithmic interpolation for zoom (feels more natural)
        log_start = math.log(self.start_zoom)
        log_target = math.log(self.target_zoom)
        self.zoom = math.exp(log_start + (log_target - log_start) * t_smooth)

    def run_demo(self, total_duration: int = 180):
        """Run automated demo for specified duration."""
        def signal_handler(sig, frame):
            self.running = False
        old_handler = signal.signal(signal.SIGINT, signal_handler)

        try:
            self.renderer.enter_fullscreen()

            start_time = time.time()
            last_time = start_time
            last_cycle_time = start_time

            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                # Check total duration
                elapsed = current_time - start_time
                if elapsed >= total_duration:
                    break

                # Track total demo time for palette changes
                self.demo_time = elapsed

                # Update navigation
                self.update_navigation(dt)

                # Handle color cycling
                if self.color_cycling:
                    if current_time - last_cycle_time >= self.cycle_speed:
                        self.color_cycle_offset = (self.color_cycle_offset + 1) % 16
                        last_cycle_time = current_time

                # Draw and update delta
                self.renderer.clear_buffer()
                self.draw_fractal()
                self.update_fill_delta(dt)  # Track rate of change
                self.draw_ui()
                self.renderer.render()

                time.sleep(0.05)  # ~20 FPS (fractal rendering is CPU intensive)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()
            signal.signal(signal.SIGINT, old_handler)


def run_demo(duration: int = 180):
    """Entry point for demo mode."""
    demo = MandelbrotDemo()
    demo.run_demo(duration)


if __name__ == "__main__":
    run_demo()
