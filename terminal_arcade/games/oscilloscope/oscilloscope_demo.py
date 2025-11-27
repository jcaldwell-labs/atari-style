"""Auto-demo mode for oscilloscope - smooth parameter sweeps without user input."""
import time
import math
import signal
from .game import Oscilloscope


class OscilloscopeDemo(Oscilloscope):
    """Oscilloscope with automatic parameter animation for recording."""

    def __init__(self):
        super().__init__()
        self.demo_time = 0
        self.mode_duration = 25  # seconds per mode
        self.param_cycle_speed = 0.4  # How fast parameters oscillate

    def auto_adjust_params(self, dt: float):
        """Automatically adjust parameters in smooth sinusoidal patterns."""
        self.demo_time += dt
        t = self.demo_time * self.param_cycle_speed

        if self.current_mode == self.MODE_LISSAJOUS:
            # Classic Lissajous: sweep frequency ratios and phase
            self.freq_a = 2 + math.sin(t * 0.3) * 1.5  # 0.5-3.5
            self.freq_b = 3 + math.sin(t * 0.4) * 2    # 1-5
            self.phase = math.sin(t * 0.5) * math.pi   # -π to π
            self.amplitude = 0.7 + math.sin(t * 0.6) * 0.2  # 0.5-0.9

        elif self.current_mode == self.MODE_XY:
            # XY mode: modulated frequencies
            self.freq_a = 1.5 + math.sin(t * 0.35) * 1  # 0.5-2.5
            self.freq_b = 2 + math.sin(t * 0.45) * 1.5  # 0.5-3.5
            self.amplitude = 0.8 + math.sin(t * 0.5) * 0.15

        elif self.current_mode == self.MODE_WAVEFORM:
            # Waveform: frequency sweep with amplitude modulation
            self.freq_a = 2 + math.sin(t * 0.25) * 1.5  # 0.5-3.5
            self.amplitude = 0.6 + math.sin(t * 0.6) * 0.3  # 0.3-0.9
            # Cycle wave types slowly
            wave_cycle = int((self.demo_time / 6) % 4)
            self.wave_type_a = wave_cycle

        elif self.current_mode == self.MODE_DUAL_TRACE:
            # Dual trace: two independent waveforms
            self.freq_a = 2 + math.sin(t * 0.3) * 1  # 1-3
            self.freq_b = 3 + math.sin(t * 0.4) * 1.5  # 1.5-4.5
            self.amplitude = 0.7 + math.sin(t * 0.5) * 0.2
            # Cycle wave types
            self.wave_type_a = int((self.demo_time / 8) % 4)
            self.wave_type_b = int((self.demo_time / 10 + 1) % 4)

        elif self.current_mode == self.MODE_SPECTRUM:
            # Spectrum analyzer: frequency modulation
            self.freq_a = 3 + math.sin(t * 0.2) * 2  # 1-5
            self.amplitude = 0.7 + math.sin(t * 0.4) * 0.25
            # Sweep wave types for different patterns
            wave_cycle = int((self.demo_time / 5) % 4)
            self.wave_type_a = wave_cycle

        # Vary speed slightly for organic feel
        self.speed = 0.05 + math.sin(t * 0.3) * 0.02

    def run_demo(self, total_duration: int = 150):
        """Run automated demo for specified duration."""
        def signal_handler(sig, frame):
            self.running = False
        old_handler = signal.signal(signal.SIGINT, signal_handler)

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

                # Auto-switch modes
                if current_time - last_switch >= self.mode_duration:
                    self.current_mode = (self.current_mode + 1) % 5
                    last_switch = current_time
                    self.demo_time = 0  # Reset param time for new mode

                # Auto-adjust parameters
                self.auto_adjust_params(dt)

                # Update animation
                if self.animating:
                    self.time_offset += self.speed

                # Draw
                self.renderer.clear_buffer()
                self.draw_grid()

                if self.current_mode == self.MODE_LISSAJOUS:
                    self.draw_lissajous()
                elif self.current_mode == self.MODE_XY:
                    self.draw_xy_mode()
                elif self.current_mode == self.MODE_WAVEFORM:
                    self.draw_waveform()
                elif self.current_mode == self.MODE_DUAL_TRACE:
                    self.draw_dual_trace()
                elif self.current_mode == self.MODE_SPECTRUM:
                    self.draw_spectrum()

                self.draw_ui()
                self.renderer.render()

                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()
            signal.signal(signal.SIGINT, old_handler)


def run_demo(duration: int = 150):
    """Entry point for demo mode."""
    demo = OscilloscopeDemo()
    demo.run_demo(duration)


if __name__ == "__main__":
    run_demo()
