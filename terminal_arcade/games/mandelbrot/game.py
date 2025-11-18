"""Mandelbrot Set Explorer - Interactive fractal viewer.

Navigate and zoom into the infinite complexity of the Mandelbrot set.
"""

import time
import subprocess
from datetime import datetime
from pathlib import Path
from ...engine.renderer import Renderer, Color
from ...engine.input_handler import InputHandler, InputType


class MandelbrotExplorer:
    """Interactive Mandelbrot set fractal explorer."""

    # Character palette for fractal density (darkest to brightest)
    DENSITY_CHARS = [' ', '·', '░', '▒', '▓', '█']

    # Color palette options (16+ colors for smooth gradients)
    PALETTES = {
        'electric': [
            Color.BLUE, Color.BLUE, Color.BRIGHT_BLUE, Color.BRIGHT_BLUE,
            Color.CYAN, Color.CYAN, Color.BRIGHT_CYAN, Color.BRIGHT_CYAN,
            Color.WHITE, Color.WHITE, Color.BRIGHT_WHITE, Color.BRIGHT_WHITE,
            Color.CYAN, Color.BLUE, Color.BRIGHT_BLUE, Color.CYAN
        ],
        'fire': [
            Color.RED, Color.RED, Color.RED, Color.BRIGHT_RED,
            Color.BRIGHT_RED, Color.BRIGHT_RED, Color.YELLOW, Color.YELLOW,
            Color.YELLOW, Color.BRIGHT_YELLOW, Color.BRIGHT_YELLOW, Color.BRIGHT_YELLOW,
            Color.WHITE, Color.WHITE, Color.BRIGHT_WHITE, Color.BRIGHT_WHITE
        ],
        'ocean': [
            Color.BLUE, Color.BLUE, Color.CYAN, Color.CYAN,
            Color.BRIGHT_CYAN, Color.BRIGHT_CYAN, Color.BRIGHT_CYAN, Color.BRIGHT_BLUE,
            Color.BRIGHT_BLUE, Color.CYAN, Color.BRIGHT_CYAN, Color.WHITE,
            Color.WHITE, Color.BRIGHT_WHITE, Color.CYAN, Color.BLUE
        ],
        'sunset': [
            Color.MAGENTA, Color.MAGENTA, Color.BRIGHT_MAGENTA, Color.BRIGHT_MAGENTA,
            Color.RED, Color.RED, Color.BRIGHT_RED, Color.BRIGHT_RED,
            Color.YELLOW, Color.YELLOW, Color.BRIGHT_YELLOW, Color.BRIGHT_YELLOW,
            Color.WHITE, Color.WHITE, Color.BRIGHT_WHITE, Color.BRIGHT_WHITE
        ],
        'forest': [
            Color.GREEN, Color.GREEN, Color.GREEN, Color.BRIGHT_GREEN,
            Color.BRIGHT_GREEN, Color.BRIGHT_GREEN, Color.CYAN, Color.CYAN,
            Color.BRIGHT_CYAN, Color.YELLOW, Color.YELLOW, Color.BRIGHT_YELLOW,
            Color.WHITE, Color.WHITE, Color.BRIGHT_WHITE, Color.BRIGHT_WHITE
        ],
        'psychedelic': [
            Color.RED, Color.BRIGHT_RED, Color.MAGENTA, Color.BRIGHT_MAGENTA,
            Color.BLUE, Color.BRIGHT_BLUE, Color.CYAN, Color.BRIGHT_CYAN,
            Color.GREEN, Color.BRIGHT_GREEN, Color.YELLOW, Color.BRIGHT_YELLOW,
            Color.RED, Color.MAGENTA, Color.BLUE, Color.CYAN
        ],
        'copper': [
            Color.RED, Color.RED, Color.RED, Color.BRIGHT_RED,
            Color.YELLOW, Color.YELLOW, Color.YELLOW, Color.BRIGHT_YELLOW,
            Color.YELLOW, Color.BRIGHT_YELLOW, Color.WHITE, Color.WHITE,
            Color.BRIGHT_WHITE, Color.BRIGHT_YELLOW, Color.YELLOW, Color.RED
        ],
        'grayscale': [
            Color.BLACK, Color.DARK_GRAY, Color.DARK_GRAY, Color.DARK_GRAY,
            Color.WHITE, Color.WHITE, Color.WHITE, Color.WHITE,
            Color.BRIGHT_WHITE, Color.BRIGHT_WHITE, Color.BRIGHT_WHITE, Color.BRIGHT_WHITE,
            Color.WHITE, Color.WHITE, Color.DARK_GRAY, Color.DARK_GRAY
        ],
    }

    def __init__(self):
        """Initialize the Mandelbrot explorer."""
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Viewport settings (complex plane coordinates)
        self.center_x = -0.5
        self.center_y = 0.0
        self.zoom = 1.5  # Width of viewport in complex plane
        self.max_iterations = 50
        self.min_zoom = 1e-15  # Allow much deeper zooming

        # Display settings
        self.current_palette = 'electric'  # Start with better default
        self.show_help = False
        self.show_coords = True
        self.smooth_coloring = True

        # Color cycling animation
        self.color_cycle_offset = 0  # Offset for cycling colors within palette
        self.color_cycling = False    # Animation on/off
        self.cycle_speed = 0.1        # Seconds per cycle step

        # Parameter visitor mode (for joystick parameter adjustment)
        self.parameter_mode = False   # False = pan/zoom, True = parameter visitor
        self.selected_param = 0       # Which parameter is selected (0-4)
        self.parameters = [
            {'name': 'Palette', 'value': self.current_palette, 'type': 'palette'},
            {'name': 'Iterations', 'value': self.max_iterations, 'type': 'int', 'min': 10, 'max': 1000, 'step': 10},
            {'name': 'Color Cycle', 'value': self.color_cycling, 'type': 'bool'},
            {'name': 'Cycle Speed', 'value': self.cycle_speed, 'type': 'float', 'min': 0.05, 'max': 1.0, 'step': 0.05},
            {'name': 'Show Coords', 'value': self.show_coords, 'type': 'bool'},
        ]

        # Interaction
        self.running = True
        self.needs_redraw = True

        # Screenshot settings
        self.screenshot_dir = Path.home() / ".terminal-arcade" / "mandelbrot-screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.last_screenshot = None

        # Interesting locations (zoom targets)
        self.bookmarks = {
            'overview': (-0.5, 0.0, 1.5),
            'valley': (-0.75, 0.1, 0.05),
            'spiral': (-0.7269, 0.1889, 0.001),
            'seahorse': (-0.745, 0.186, 0.0025),
            'triple_spiral': (0.285, 0.01, 0.005),
            'elephant': (0.285, 0.0, 0.012),
        }

    def mandelbrot_iterations(self, c_real, c_imag):
        """Calculate iterations for a complex number c.

        Args:
            c_real: Real component of c
            c_imag: Imaginary component of c

        Returns:
            Number of iterations before divergence (or max_iterations)
        """
        z_real, z_imag = 0.0, 0.0

        for i in range(self.max_iterations):
            # z = z^2 + c
            z_real_new = z_real * z_real - z_imag * z_imag + c_real
            z_imag_new = 2 * z_real * z_imag + c_imag

            # Check for divergence (|z| > 2)
            if z_real_new * z_real_new + z_imag_new * z_imag_new > 4.0:
                if self.smooth_coloring:
                    # Smooth coloring algorithm
                    log_zn = (z_real_new * z_real_new + z_imag_new * z_imag_new) ** 0.5
                    nu = (i + 1 - (log_zn / 2.0) / 0.693147)  # log(2) = 0.693147
                    return nu
                return i

            z_real, z_imag = z_real_new, z_imag_new

        return self.max_iterations

    def get_char_and_color(self, iterations):
        """Map iterations to character and color.

        Args:
            iterations: Iteration count (may be fractional for smooth coloring)

        Returns:
            Tuple of (character, color)
        """
        if iterations >= self.max_iterations:
            # Inside the set - use darkest character
            return '█', Color.BLACK

        # Map to palette with color cycling offset
        palette = self.PALETTES[self.current_palette]
        base_index = int(iterations * len(palette) / self.max_iterations)
        # Apply color cycle offset for animation
        color_index = (base_index + self.color_cycle_offset) % len(palette)
        color = palette[color_index]

        # Map to character density
        density = iterations / self.max_iterations
        char_index = int(density * (len(self.DENSITY_CHARS) - 1))
        char = self.DENSITY_CHARS[char_index]

        return char, color

    def screen_to_complex(self, screen_x, screen_y):
        """Convert screen coordinates to complex plane coordinates.

        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate

        Returns:
            Tuple of (real, imaginary) complex coordinates
        """
        # Account for terminal aspect ratio (~2:1)
        aspect_ratio = self.renderer.width / (self.renderer.height * 2)

        # Map screen to complex plane
        real = self.center_x + (screen_x - self.renderer.width / 2) * (self.zoom / self.renderer.width)
        imag = self.center_y + (screen_y - self.renderer.height / 2) * (self.zoom / self.renderer.width) * aspect_ratio

        return real, imag

    def draw_fractal(self):
        """Render the Mandelbrot set to the buffer."""
        for y in range(self.renderer.height):
            for x in range(self.renderer.width):
                c_real, c_imag = self.screen_to_complex(x, y)
                iterations = self.mandelbrot_iterations(c_real, c_imag)
                char, color = self.get_char_and_color(iterations)
                self.renderer.set_pixel(x, y, char, color)

    def _sync_parameters(self):
        """Sync parameter values from game state."""
        self.parameters[0]['value'] = self.current_palette
        self.parameters[1]['value'] = self.max_iterations
        self.parameters[2]['value'] = self.color_cycling
        self.parameters[3]['value'] = self.cycle_speed
        self.parameters[4]['value'] = self.show_coords

    def _create_parameter_box(self):
        """Create parameter display box using /usr/bin/boxes.

        Returns:
            List of box lines to draw
        """
        self._sync_parameters()

        # Build parameter text
        param_lines = ["MANDELBROT PARAMETERS", ""]

        # Mode indicator
        mode_text = "MODE: PARAMETER ADJUST" if self.parameter_mode else "MODE: PAN/ZOOM"
        param_lines.append(mode_text)
        param_lines.append("")

        # Add each parameter
        for i, param in enumerate(self.parameters):
            prefix = "► " if (self.parameter_mode and i == self.selected_param) else "  "

            if param['type'] == 'palette':
                value_str = param['value']
            elif param['type'] == 'bool':
                value_str = "ON" if param['value'] else "OFF"
            elif param['type'] == 'int':
                value_str = str(param['value'])
            elif param['type'] == 'float':
                value_str = f"{param['value']:.2f}"
            else:
                value_str = str(param['value'])

            param_lines.append(f"{prefix}{param['name']}: {value_str}")

        param_lines.append("")
        param_lines.append("Center: ({:.6f}, {:.6f}i)".format(self.center_x, self.center_y))
        param_lines.append("Zoom: {:.6e}".format(self.zoom))

        # Use boxes to create bordered text with double-line border
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
                return result.stdout.strip().split('\n')
        except Exception:
            pass

        # Fallback to simple box
        max_width = max(len(line) for line in param_lines)
        box_lines = [
            "╔" + "═" * (max_width + 2) + "╗"
        ]
        for line in param_lines:
            box_lines.append(f"║ {line:<{max_width}} ║")
        box_lines.append("╚" + "═" * (max_width + 2) + "╝")

        return box_lines

    def draw_ui(self):
        """Draw UI overlay (coordinates, controls, etc.)."""
        # Draw parameter box in top-right corner
        box_lines = self._create_parameter_box()
        box_width = max(len(line) for line in box_lines)
        box_x = self.renderer.width - box_width - 2
        box_y = 1

        for i, line in enumerate(box_lines):
            # Color based on mode
            if self.parameter_mode and "MODE: PARAMETER" in line:
                color = Color.BRIGHT_GREEN
            elif "MODE: PAN/ZOOM" in line:
                color = Color.BRIGHT_CYAN
            elif line.strip().startswith("►"):
                color = Color.BRIGHT_YELLOW  # Selected parameter
            else:
                color = Color.WHITE

            self.renderer.draw_text(box_x, box_y + i, line, color)

        # Show mode toggle hint at bottom
        if self.parameter_mode:
            mode_hint = "[SPACE] Pan/Zoom Mode | JOYSTICK: ↕ Select Param, ← → Adjust Value"
            hint_color = Color.BRIGHT_GREEN
        else:
            mode_hint = "[SPACE] Parameter Mode | JOYSTICK: Pan & Zoom  |  Z=Zoom+ X=Zoom-  S=Screenshot  H=Help  ESC=Exit"
            hint_color = Color.BRIGHT_CYAN

        hint_x = (self.renderer.width - len(mode_hint)) // 2
        hint_y = self.renderer.height - 1
        self.renderer.draw_text(hint_x, hint_y, mode_hint, hint_color)

        if self.show_help:
            mode = "PARAMETER ADJUST" if self.parameter_mode else "PAN/ZOOM"
            help_lines = [
                "═══ MANDELBROT EXPLORER ═══",
                "",
                "CURRENT MODE: " + mode,
                "",
                "SPACE - Toggle Mode:",
                "  Pan/Zoom: Navigate fractal",
                "  Parameter: Adjust settings",
                "",
                "PAN/ZOOM MODE:",
                "  Joystick/Arrow: Pan view",
                "  Button0 / Z: Zoom IN",
                "  Button1 / X: Zoom OUT",
                "",
                "PARAMETER MODE:",
                "  Joystick ↕: Select parameter",
                "  Joystick ← →: Adjust value",
                "  Button0: Toggle ON/OFF",
                "  See panel (top-right) →",
                "",
                "QUICK KEYS:",
                "  S/Button4: Screenshot",
                "  1-6: Bookmarks",
                "  R: Reset  H: Help",
                "  ESC/Q: Exit",
                "",
                "Screenshots saved to:",
                "~/.terminal-arcade/",
                "mandelbrot-screenshots/",
            ]

            # Draw help box (sized for content)
            help_width = max(len(line) for line in help_lines) + 4
            help_x = (self.renderer.width - help_width) // 2
            help_y = (self.renderer.height - len(help_lines) - 2) // 2

            # Background box
            for i in range(len(help_lines) + 2):
                self.renderer.draw_text(help_x - 1, help_y + i,
                                       " " * (help_width + 2), Color.DARK_GRAY)

            # Border
            self.renderer.draw_border(help_x - 1, help_y,
                                     help_width + 2, len(help_lines) + 2, Color.CYAN)

            # Content
            for i, line in enumerate(help_lines):
                self.renderer.draw_text(help_x, help_y + 1 + i, line,
                                       Color.BRIGHT_WHITE if i == 0 else Color.WHITE)

    def save_screenshot(self):
        """Save current view as a text file with metadata overlay."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mandelbrot_{timestamp}.txt"
        filepath = self.screenshot_dir / filename

        # Capture current buffer state
        lines = []
        for y in range(self.renderer.height):
            line = ""
            for x in range(self.renderer.width):
                char = self.renderer.buffer[y][x]
                line += char
            lines.append(line.rstrip())  # Remove trailing spaces

        # Create metadata
        metadata_lines = [
            f"Mandelbrot Set Explorer",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Center: {self.center_x:.10e} + {self.center_y:.10e}i",
            f"Zoom: {self.zoom:.10e}",
            f"Palette: {self.current_palette}",
            f"Iterations: {self.max_iterations}",
        ]

        # Use boxes to create a nice border around metadata
        metadata_text = "\n".join(metadata_lines)
        try:
            # Use boxes command to create bordered text
            result = subprocess.run(
                ['boxes', '-d', 'stone', '-p', 'a1l2'],
                input=metadata_text,
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                metadata_box = result.stdout.strip().split('\n')
            else:
                # Fallback to simple box
                metadata_box = [
                    "╔═══════════════════════════════════╗"
                ] + [f"║ {line:<35} ║" for line in metadata_lines] + [
                    "╚═══════════════════════════════════╝"
                ]
        except Exception:
            # Fallback if boxes fails
            metadata_box = [
                "╔═══════════════════════════════════╗"
            ] + [f"║ {line:<35} ║" for line in metadata_lines] + [
                "╚═══════════════════════════════════╝"
            ]

        # Overlay metadata in top-right corner
        box_width = max(len(line) for line in metadata_box)
        box_height = len(metadata_box)
        box_x = self.renderer.width - box_width - 2
        box_y = 1

        # Insert metadata box into lines
        for i, box_line in enumerate(metadata_box):
            if box_y + i < len(lines):
                line = lines[box_y + i]
                # Overlay the box line
                if box_x + len(box_line) <= len(line):
                    lines[box_y + i] = line[:box_x] + box_line + line[box_x + len(box_line):]
                else:
                    # Extend line if needed
                    lines[box_y + i] = line[:box_x] + box_line

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        self.last_screenshot = filename
        return filename

    def _adjust_parameter(self, direction):
        """Adjust the selected parameter value.

        Args:
            direction: 1 for increase, -1 for decrease
        """
        param = self.parameters[self.selected_param]

        if param['type'] == 'palette':
            palettes = list(self.PALETTES.keys())
            current_index = palettes.index(param['value'])
            new_index = (current_index + direction) % len(palettes)
            self.current_palette = palettes[new_index]
            param['value'] = self.current_palette

        elif param['type'] == 'int':
            step = param.get('step', 1)
            new_val = param['value'] + (direction * step)
            param['value'] = max(param['min'], min(param['max'], new_val))
            if param['name'] == 'Iterations':
                self.max_iterations = param['value']

        elif param['type'] == 'float':
            step = param.get('step', 0.1)
            new_val = param['value'] + (direction * step)
            param['value'] = max(param['min'], min(param['max'], new_val))
            if param['name'] == 'Cycle Speed':
                self.cycle_speed = param['value']

        elif param['type'] == 'bool':
            param['value'] = not param['value']
            if param['name'] == 'Color Cycle':
                self.color_cycling = param['value']
            elif param['name'] == 'Show Coords':
                self.show_coords = param['value']

        self.needs_redraw = True

    def handle_input(self, input_type, raw_key):
        """Handle user input.

        Args:
            input_type: InputType from input handler
            raw_key: Raw key from blessed terminal (or None)
        """
        # Handle special keys first
        if raw_key:
            # SPACE = Toggle mode
            if raw_key == ' ':
                self.parameter_mode = not self.parameter_mode
                self.needs_redraw = True
                return

            # ESC = Exit
            if raw_key.name == 'KEY_ESCAPE':
                self.running = False
                return

        # Handle Q key exit (comes through InputType.QUIT)
        if input_type == InputType.QUIT:
            self.running = False
            return

        # Handle ESC via InputType.BACK as well
        if input_type == InputType.BACK:
            self.running = False
            return

        # MODE 1: Parameter visitor mode (joystick navigates parameters)
        if self.parameter_mode:
            if input_type == InputType.UP:
                self.selected_param = (self.selected_param - 1) % len(self.parameters)
                self.needs_redraw = True
            elif input_type == InputType.DOWN:
                self.selected_param = (self.selected_param + 1) % len(self.parameters)
                self.needs_redraw = True
            elif input_type == InputType.LEFT:
                self._adjust_parameter(-1)
            elif input_type == InputType.RIGHT:
                self._adjust_parameter(1)
            elif input_type == InputType.SELECT:
                # Toggle boolean parameters
                param = self.parameters[self.selected_param]
                if param['type'] == 'bool':
                    self._adjust_parameter(1)

        # MODE 2: Pan/zoom mode (joystick pans and zooms)
        else:
            # Pan movement (scaled by zoom level)
            pan_speed = self.zoom * 0.1

            if input_type == InputType.UP:
                self.center_y -= pan_speed
                self.needs_redraw = True
            elif input_type == InputType.DOWN:
                self.center_y += pan_speed
                self.needs_redraw = True
            elif input_type == InputType.LEFT:
                self.center_x -= pan_speed
                self.needs_redraw = True
            elif input_type == InputType.RIGHT:
                self.center_x += pan_speed
                self.needs_redraw = True
            elif input_type == InputType.SELECT:
                # Button 0 / Enter = Zoom IN
                self.zoom = max(self.min_zoom, self.zoom * 0.7)
                # Increase iterations when zooming deep
                if self.zoom < 1e-6:
                    self.max_iterations = min(500, max(100, self.max_iterations))
                self.needs_redraw = True

        # Check for joystick buttons (work in both modes)
        if self.input_handler.joystick_initialized:
            buttons = self.input_handler.get_joystick_buttons()

            # Button 1 = Zoom OUT (in pan/zoom mode only)
            if buttons.get(1, False) and not self.parameter_mode:
                self.zoom = min(5.0, self.zoom * 1.3)
                self.needs_redraw = True
                time.sleep(0.15)  # Debounce

            # Button 4 = Screenshot (works in both modes)
            if buttons.get(4, False):
                filename = self.save_screenshot()
                # Show brief message
                msg = f"Screenshot saved: {filename}"
                msg_x = (self.renderer.width - len(msg)) // 2
                self.renderer.draw_text(msg_x, self.renderer.height - 3, msg, Color.BRIGHT_GREEN)
                self.renderer.render()
                time.sleep(1.0)
                self.needs_redraw = True

        # Process keyboard shortcuts (raw_key passed from run loop)
        if raw_key:
            key_lower = raw_key.lower()

            # Zoom controls (keyboard always works in both modes)
            if key_lower == 'z':
                self.zoom = max(self.min_zoom, self.zoom * 0.7)  # Zoom in
                # Auto-increase iterations when zooming deep
                if self.zoom < 1e-6:
                    self.max_iterations = min(500, max(100, self.max_iterations))
                self.needs_redraw = True
            elif key_lower == 'x' or key_lower == 'o':
                # X or O = Zoom out
                self.zoom = min(5.0, self.zoom * 1.3)  # Zoom out (capped)
                self.needs_redraw = True

            # Screenshot
            elif key_lower == 's':
                filename = self.save_screenshot()
                # Show brief message
                msg = f"Screenshot saved: {filename}"
                msg_x = (self.renderer.width - len(msg)) // 2
                self.renderer.draw_text(msg_x, self.renderer.height - 3, msg, Color.BRIGHT_GREEN)
                self.renderer.render()
                time.sleep(1.0)
                self.needs_redraw = True

            # Help toggle
            elif key_lower == 'h':
                self.show_help = not self.show_help
                self.needs_redraw = True

            # Reset
            elif key_lower == 'r':
                self.center_x, self.center_y, self.zoom = -0.5, 0.0, 1.5
                self.max_iterations = 50
                self.needs_redraw = True

            # Bookmarks
            elif raw_key in '123456':
                bookmark_names = list(self.bookmarks.keys())
                bookmark_index = int(raw_key) - 1
                if bookmark_index < len(bookmark_names):
                    bookmark = bookmark_names[bookmark_index]
                    self.center_x, self.center_y, self.zoom = self.bookmarks[bookmark]
                    self.max_iterations = max(100, self.max_iterations)
                    self.needs_redraw = True

    def run(self):
        """Main game loop."""
        try:
            self.renderer.enter_fullscreen()
            last_cycle_time = time.time()

            while self.running:
                # Handle color cycling animation
                if self.color_cycling:
                    current_time = time.time()
                    if current_time - last_cycle_time >= self.cycle_speed:
                        self.color_cycle_offset = (self.color_cycle_offset + 1) % 16
                        last_cycle_time = current_time
                        self.needs_redraw = True

                if self.needs_redraw:
                    self.renderer.clear_buffer()
                    self.draw_fractal()
                    self.draw_ui()
                    self.renderer.render()
                    self.needs_redraw = False

                # Get input (InputType from joystick/arrows)
                input_type = self.input_handler.get_input(timeout=0.05)

                # Get raw keyboard key for special handling (TAB, ESC, letters)
                raw_key = None
                with self.input_handler.term.cbreak():
                    raw_key = self.input_handler.term.inkey(timeout=0)

                # Handle input
                self.handle_input(input_type, raw_key)

                time.sleep(0.033)  # ~30 FPS

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_mandelbrot():
    """Entry point for Mandelbrot Explorer."""
    explorer = MandelbrotExplorer()
    explorer.run()


if __name__ == '__main__':
    run_mandelbrot()
