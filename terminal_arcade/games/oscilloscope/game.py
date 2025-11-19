"""Oscilloscope Functions - Lissajous curves and waveform visualizer.

Interactive oscilloscope simulator with multiple display modes.
"""

import time
import signal
import math
from ...engine.renderer import Renderer, Color
from ...engine.input_handler import InputHandler, InputType


class Oscilloscope:
    """Interactive oscilloscope with multiple visualization modes."""

    # Display modes
    MODE_LISSAJOUS = 0
    MODE_XY = 1
    MODE_WAVEFORM = 2
    MODE_DUAL_TRACE = 3
    MODE_SPECTRUM = 4

    MODE_NAMES = [
        "Lissajous Curves",
        "XY Mode",
        "Waveform",
        "Dual Trace",
        "Spectrum Analyzer"
    ]

    # Waveform types
    WAVE_SINE = 0
    WAVE_SQUARE = 1
    WAVE_TRIANGLE = 2
    WAVE_SAWTOOTH = 3

    WAVE_NAMES = ["Sine", "Square", "Triangle", "Sawtooth"]

    def __init__(self):
        """Initialize oscilloscope."""
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Display mode
        self.current_mode = self.MODE_LISSAJOUS
        self.parameter_mode = False  # Dual-mode like Mandelbrot
        self.selected_param = 0

        # Signal parameters
        self.freq_a = 3.0    # Frequency A (Hz)
        self.freq_b = 2.0    # Frequency B (Hz)
        self.freq_lock = False  # Lock frequencies together
        self.phase = 0.0     # Phase offset (0-2π)
        self.amplitude = 0.8 # Amplitude (0-1)
        self.wave_type_a = self.WAVE_SINE
        self.wave_type_b = self.WAVE_SINE

        # Animation
        self.time_offset = 0.0
        self.animating = True
        self.speed = 0.05

        # Display
        self.show_help = False
        self.show_grid = True
        self.trail_length = 100  # Number of points to draw

        # Parameters list for visitor mode
        self.parameters = [
            {'name': 'Mode', 'value': self.current_mode, 'type': 'mode'},
            {'name': 'Freq Lock', 'value': self.freq_lock, 'type': 'bool'},
            {'name': 'Freq A', 'value': self.freq_a, 'type': 'float', 'min': 0.5, 'max': 10.0, 'step': 0.5},
            {'name': 'Freq B', 'value': self.freq_b, 'type': 'float', 'min': 0.5, 'max': 10.0, 'step': 0.5},
            {'name': 'Phase', 'value': self.phase, 'type': 'float', 'min': 0.0, 'max': 6.28, 'step': 0.1},
            {'name': 'Amplitude', 'value': self.amplitude, 'type': 'float', 'min': 0.1, 'max': 1.0, 'step': 0.1},
            {'name': 'Wave A', 'value': self.wave_type_a, 'type': 'wave'},
            {'name': 'Wave B', 'value': self.wave_type_b, 'type': 'wave'},
            {'name': 'Animate', 'value': self.animating, 'type': 'bool'},
            {'name': 'Speed', 'value': self.speed, 'type': 'float', 'min': 0.01, 'max': 0.2, 'step': 0.01},
            {'name': 'Show Grid', 'value': self.show_grid, 'type': 'bool'},
        ]

        self.running = True

    def _generate_wave(self, t, wave_type):
        """Generate waveform value at time t.

        Args:
            t: Time value
            wave_type: Type of wave (WAVE_SINE, etc.)

        Returns:
            Wave value (-1 to 1)
        """
        # Normalize t to 0-1 range
        t_norm = t % 1.0

        if wave_type == self.WAVE_SINE:
            return math.sin(t * 2 * math.pi)
        elif wave_type == self.WAVE_SQUARE:
            return 1.0 if t_norm < 0.5 else -1.0
        elif wave_type == self.WAVE_TRIANGLE:
            if t_norm < 0.25:
                return t_norm * 4
            elif t_norm < 0.75:
                return 1.0 - (t_norm - 0.25) * 4
            else:
                return -1.0 + (t_norm - 0.75) * 4
        elif wave_type == self.WAVE_SAWTOOTH:
            return (t_norm * 2) - 1.0
        return 0.0

    def draw_grid(self):
        """Draw oscilloscope grid."""
        if not self.show_grid:
            return

        center_x = self.renderer.width // 2
        center_y = self.renderer.height // 2

        # Vertical center line
        for y in range(self.renderer.height):
            if y % 2 == 0:
                self.renderer.set_pixel(center_x, y, '│', Color.DARK_GRAY)

        # Horizontal center line
        for x in range(self.renderer.width):
            if x % 2 == 0:
                self.renderer.set_pixel(x, center_y, '─', Color.DARK_GRAY)

        # Tick marks
        for i in range(-4, 5):
            if i != 0:
                x = center_x + i * (self.renderer.width // 10)
                if 0 <= x < self.renderer.width:
                    self.renderer.set_pixel(x, center_y, '┼', Color.DARK_GRAY)

        for i in range(-4, 5):
            if i != 0:
                y = center_y + i * (self.renderer.height // 10)
                if 0 <= y < self.renderer.height:
                    self.renderer.set_pixel(center_x, y, '┼', Color.DARK_GRAY)

    def draw_lissajous(self):
        """Draw Lissajous curve."""
        center_x = self.renderer.width // 2
        center_y = self.renderer.height // 2
        scale_x = (self.renderer.width // 2 - 4) * self.amplitude
        scale_y = (self.renderer.height // 2 - 2) * self.amplitude

        # Generate curve points
        points = []
        for i in range(self.trail_length):
            t = (i / self.trail_length) * 2 * math.pi + self.time_offset

            x_signal = self._generate_wave(self.freq_a * t / (2 * math.pi), self.wave_type_a)
            y_signal = self._generate_wave(self.freq_b * t / (2 * math.pi) + self.phase, self.wave_type_b)

            x = int(center_x + x_signal * scale_x)
            y = int(center_y + y_signal * scale_y)

            if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                points.append((x, y, i))

        # Draw points with fade effect
        for x, y, i in points:
            brightness = i / self.trail_length
            if brightness < 0.3:
                char, color = '·', Color.DARK_GRAY
            elif brightness < 0.6:
                char, color = '○', Color.CYAN
            else:
                char, color = '●', Color.BRIGHT_CYAN

            self.renderer.set_pixel(x, y, char, color)

    def draw_waveform(self):
        """Draw waveform display."""
        center_y = self.renderer.height // 2
        scale_y = (self.renderer.height // 2 - 2) * self.amplitude

        for x in range(self.renderer.width):
            t = (x / self.renderer.width) * 4 * math.pi + self.time_offset
            signal = self._generate_wave(self.freq_a * t / (2 * math.pi), self.wave_type_a)

            y = int(center_y - signal * scale_y)

            if 0 <= y < self.renderer.height:
                self.renderer.set_pixel(x, y, '█', Color.BRIGHT_GREEN)

    def draw_dual_trace(self):
        """Draw dual trace (two waveforms)."""
        center_y = self.renderer.height // 2
        scale_y = (self.renderer.height // 4 - 1) * self.amplitude

        # Channel A (top)
        for x in range(self.renderer.width):
            t = (x / self.renderer.width) * 4 * math.pi + self.time_offset
            signal = self._generate_wave(self.freq_a * t / (2 * math.pi), self.wave_type_a)

            y = int(center_y // 2 - signal * scale_y)

            if 0 <= y < self.renderer.height:
                self.renderer.set_pixel(x, y, '█', Color.BRIGHT_YELLOW)

        # Channel B (bottom)
        for x in range(self.renderer.width):
            t = (x / self.renderer.width) * 4 * math.pi + self.time_offset
            signal = self._generate_wave(self.freq_b * t / (2 * math.pi), self.wave_type_b)

            y = int(center_y + center_y // 2 - signal * scale_y)

            if 0 <= y < self.renderer.height:
                self.renderer.set_pixel(x, y, '█', Color.BRIGHT_CYAN)

    def draw_xy_mode(self):
        """Draw XY mode (one frequency modulates the other)."""
        center_x = self.renderer.width // 2
        center_y = self.renderer.height // 2
        scale = min(self.renderer.width // 2, self.renderer.height) - 4

        for i in range(self.trail_length):
            t = (i / self.trail_length) * 4 * math.pi + self.time_offset

            x_signal = self._generate_wave(t * self.freq_a / 4, self.wave_type_a)
            y_signal = x_signal * self._generate_wave(t * self.freq_b / 4, self.wave_type_b)

            x = int(center_x + x_signal * scale * self.amplitude)
            y = int(center_y + y_signal * scale * self.amplitude * 0.5)

            if 0 <= x < self.renderer.width and 0 <= y < self.renderer.height:
                brightness = i / self.trail_length
                if brightness < 0.5:
                    char, color = '·', Color.GREEN
                else:
                    char, color = '●', Color.BRIGHT_GREEN

                self.renderer.set_pixel(x, y, char, color)

    def draw_spectrum(self):
        """Draw spectrum analyzer bars."""
        bar_width = max(2, self.renderer.width // 16)
        num_bars = self.renderer.width // bar_width

        for i in range(num_bars):
            # Simulate frequency response
            freq = (i + 1) * self.freq_a / num_bars
            t = self.time_offset + i * 0.1
            intensity = abs(self._generate_wave(t * freq, self.wave_type_a)) * self.amplitude

            bar_height = int(intensity * (self.renderer.height - 4))
            x_start = i * bar_width

            for y in range(self.renderer.height - bar_height, self.renderer.height):
                for dx in range(bar_width - 1):
                    x = x_start + dx
                    if x < self.renderer.width:
                        # Color gradient from bottom (red) to top (green)
                        progress = (self.renderer.height - y) / max(1, bar_height)
                        if progress < 0.33:
                            color = Color.BRIGHT_GREEN
                        elif progress < 0.66:
                            color = Color.BRIGHT_YELLOW
                        else:
                            color = Color.BRIGHT_RED

                        self.renderer.set_pixel(x, y, '█', color)

    def _sync_parameters(self):
        """Sync parameter values."""
        self.parameters[0]['value'] = self.current_mode
        self.parameters[1]['value'] = self.freq_lock
        self.parameters[2]['value'] = self.freq_a
        self.parameters[3]['value'] = self.freq_b
        self.parameters[4]['value'] = self.phase
        self.parameters[5]['value'] = self.amplitude
        self.parameters[6]['value'] = self.wave_type_a
        self.parameters[7]['value'] = self.wave_type_b
        self.parameters[8]['value'] = self.animating
        self.parameters[9]['value'] = self.speed
        self.parameters[10]['value'] = self.show_grid

    def draw_ui(self):
        """Draw UI with parameter panel."""
        self._sync_parameters()

        # Build parameter text
        param_lines = ["OSCILLOSCOPE PARAMETERS", ""]

        mode_text = "MODE: ADJUST" if self.parameter_mode else "MODE: VIEW"
        param_lines.append(mode_text)
        param_lines.append("")

        for i, param in enumerate(self.parameters):
            prefix = "► " if (self.parameter_mode and i == self.selected_param) else "  "

            if param['type'] == 'mode':
                value_str = self.MODE_NAMES[param['value']]
            elif param['type'] == 'wave':
                value_str = self.WAVE_NAMES[param['value']]
            elif param['type'] == 'bool':
                value_str = "ON" if param['value'] else "OFF"
            elif param['type'] == 'float':
                value_str = f"{param['value']:.2f}"
            else:
                value_str = str(param['value'])

            param_lines.append(f"{prefix}{param['name']}: {value_str}")

        # Create box
        import subprocess
        param_text = "\n".join(param_lines)
        try:
            result = subprocess.run(
                ['boxes', '-d', 'ansi-double', '-p', 'a1'],
                input=param_text,
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                box_lines = result.stdout.strip().split('\n')
            else:
                # Fallback
                max_width = max(len(line) for line in param_lines)
                box_lines = ["╔" + "═" * (max_width + 2) + "╗"]
                for line in param_lines:
                    box_lines.append(f"║ {line:<{max_width}} ║")
                box_lines.append("╚" + "═" * (max_width + 2) + "╝")
        except Exception:
            max_width = max(len(line) for line in param_lines)
            box_lines = ["╔" + "═" * (max_width + 2) + "╗"]
            for line in param_lines:
                box_lines.append(f"║ {line:<{max_width}} ║")
            box_lines.append("╚" + "═" * (max_width + 2) + "╝")

        # Draw box in top-right
        box_width = max(len(line) for line in box_lines)
        box_x = self.renderer.width - box_width - 2
        box_y = 1

        for i, line in enumerate(box_lines):
            if self.parameter_mode and "MODE: ADJUST" in line:
                color = Color.BRIGHT_GREEN
            elif "MODE: VIEW" in line:
                color = Color.BRIGHT_CYAN
            elif line.strip().startswith("►"):
                color = Color.BRIGHT_YELLOW
            else:
                color = Color.WHITE

            self.renderer.draw_text(box_x, box_y + i, line, color)

        # Mode hint at bottom
        if self.parameter_mode:
            hint = "[SPACE] View Mode | JOYSTICK: ↕ Select, ← → Adjust | ESC=Exit"
            color = Color.BRIGHT_GREEN
        else:
            hint = "[SPACE] Parameter Mode | Current: " + self.MODE_NAMES[self.current_mode] + " | H=Help ESC=Exit"
            color = Color.BRIGHT_CYAN

        hint_x = (self.renderer.width - len(hint)) // 2
        self.renderer.draw_text(hint_x, self.renderer.height - 1, hint, color)

        # Title
        title = "◉ OSCILLOSCOPE FUNCTIONS ◉"
        title_x = (self.renderer.width - len(title)) // 2
        self.renderer.draw_text(title_x, 0, title, Color.BRIGHT_YELLOW)

        # Help overlay
        if self.show_help:
            help_lines = [
                "═══ OSCILLOSCOPE ═══",
                "",
                "MODES (5):",
                "  1=Lissajous  2=XY",
                "  3=Waveform   4=Dual",
                "  5=Spectrum",
                "",
                "SPACE: Toggle mode",
                "In ADJUST mode:",
                "  Joystick ↕: Select",
                "  Joystick ← →: Change",
                "",
                "Keys:",
                "  H: Help",
                "  ESC/Q: Exit",
            ]

            help_width = max(len(line) for line in help_lines) + 4
            help_x = (self.renderer.width - help_width) // 2
            help_y = (self.renderer.height - len(help_lines) - 2) // 2

            for i in range(len(help_lines) + 2):
                self.renderer.draw_text(help_x - 1, help_y + i, " " * (help_width + 2), Color.DARK_GRAY)

            self.renderer.draw_border(help_x - 1, help_y, help_width + 2, len(help_lines) + 2, Color.YELLOW)

            for i, line in enumerate(help_lines):
                self.renderer.draw_text(help_x, help_y + 1 + i, line, Color.BRIGHT_WHITE if i == 0 else Color.WHITE)

    def _adjust_parameter(self, direction):
        """Adjust selected parameter."""
        param = self.parameters[self.selected_param]

        if param['type'] == 'mode':
            self.current_mode = (self.current_mode + direction) % len(self.MODE_NAMES)
            param['value'] = self.current_mode
        elif param['type'] == 'wave':
            if param['name'] == 'Wave A':
                self.wave_type_a = (self.wave_type_a + direction) % len(self.WAVE_NAMES)
                param['value'] = self.wave_type_a
            else:
                self.wave_type_b = (self.wave_type_b + direction) % len(self.WAVE_NAMES)
                param['value'] = self.wave_type_b
        elif param['type'] == 'float':
            step = param.get('step', 0.1)
            new_val = param['value'] + (direction * step)
            param['value'] = max(param['min'], min(param['max'], new_val))

            # Sync back to instance variables
            if param['name'] == 'Freq A':
                self.freq_a = param['value']
                # If freq lock is on, sync Freq B to match
                if self.freq_lock:
                    self.freq_b = self.freq_a
                    self.parameters[3]['value'] = self.freq_b  # Update Freq B param
            elif param['name'] == 'Freq B':
                self.freq_b = param['value']
                # If freq lock is on, sync Freq A to match
                if self.freq_lock:
                    self.freq_a = self.freq_b
                    self.parameters[2]['value'] = self.freq_a  # Update Freq A param
            elif param['name'] == 'Phase':
                self.phase = param['value']
            elif param['name'] == 'Amplitude':
                self.amplitude = param['value']
            elif param['name'] == 'Speed':
                self.speed = param['value']
        elif param['type'] == 'bool':
            param['value'] = not param['value']
            if param['name'] == 'Freq Lock':
                self.freq_lock = param['value']
                # When locking, immediately sync frequencies
                if self.freq_lock:
                    self.freq_b = self.freq_a
                    self.parameters[3]['value'] = self.freq_b
            elif param['name'] == 'Animate':
                self.animating = param['value']
            elif param['name'] == 'Show Grid':
                self.show_grid = param['value']

    def handle_input(self, input_type):
        """Handle input."""
        # Exit
        if input_type == InputType.QUIT or input_type == InputType.BACK:
            self.running = False
            return

        # Button controls
        if self.input_handler.joystick_initialized:
            buttons = self.input_handler.get_joystick_buttons()

            # Button 2 = Toggle mode
            if buttons.get(2, False):
                self.parameter_mode = not self.parameter_mode
                time.sleep(0.2)
                return

            # Button 3 = Toggle help
            if buttons.get(3, False):
                self.show_help = not self.show_help
                time.sleep(0.2)
                return

        # Parameter mode
        if self.parameter_mode:
            if input_type == InputType.UP:
                self.selected_param = (self.selected_param - 1) % len(self.parameters)
            elif input_type == InputType.DOWN:
                self.selected_param = (self.selected_param + 1) % len(self.parameters)
            elif input_type == InputType.LEFT:
                self._adjust_parameter(-1)
            elif input_type == InputType.RIGHT:
                self._adjust_parameter(1)
            elif input_type == InputType.SELECT:
                param = self.parameters[self.selected_param]
                if param['type'] == 'bool':
                    self._adjust_parameter(1)

    def run(self):
        """Main loop."""
        def signal_handler(sig, frame):
            self.running = False
        old_handler = signal.signal(signal.SIGINT, signal_handler)

        try:
            self.renderer.enter_fullscreen()

            while self.running:
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

                # Input (NO custom keyboard!)
                input_type = self.input_handler.get_input(timeout=0.05)
                self.handle_input(input_type)

                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()
            signal.signal(signal.SIGINT, old_handler)


def run_oscilloscope():
    """Entry point for Oscilloscope."""
    osc = Oscilloscope()
    osc.run()


if __name__ == '__main__':
    run_oscilloscope()
