"""ASCII Painter - Joystick-controlled ASCII art editor."""

import time
import os
from collections import deque
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType


class DrawingTool:
    """Base class for drawing tools."""

    def __init__(self, name):
        self.name = name

    def draw(self, canvas, x, y, char, color):
        """Draw at position."""
        pass


class FreehandTool(DrawingTool):
    """Freehand drawing tool."""

    def __init__(self):
        super().__init__("Freehand")

    def draw(self, canvas, x, y, char, color, brush_size=1):
        """Draw character at position with brush size."""
        offsets = {
            1: [(0, 0)],
            3: [(-1, 0), (0, 0), (1, 0), (0, -1), (0, 1)],  # Cross pattern
            5: [(-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
                (0, -2), (0, -1), (0, 1), (0, 2),
                (-1, -1), (-1, 1), (1, -1), (1, 1)],  # Larger cross
        }

        for dx, dy in offsets.get(brush_size, [(0, 0)]):
            nx, ny = x + dx, y + dy
            if 0 <= nx < canvas.width and 0 <= ny < canvas.height:
                canvas.set_pixel(nx, ny, char, color)


class LineTool(DrawingTool):
    """Line drawing tool."""

    def __init__(self):
        super().__init__("Line")
        self.start_pos = None

    def set_start(self, x, y):
        """Set line start position."""
        self.start_pos = (x, y)

    def draw(self, canvas, x, y, char, color):
        """Draw line from start to end."""
        if self.start_pos is None:
            return

        x0, y0 = self.start_pos
        x1, y1 = x, y

        # Bresenham's line algorithm
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            canvas.set_pixel(x0, y0, char, color)

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy


class RectangleTool(DrawingTool):
    """Rectangle drawing tool."""

    def __init__(self, filled=False):
        super().__init__("Rectangle" if not filled else "Filled Rectangle")
        self.filled = filled
        self.start_pos = None

    def set_start(self, x, y):
        """Set rectangle start corner."""
        self.start_pos = (x, y)

    def draw(self, canvas, x, y, char, color):
        """Draw rectangle."""
        if self.start_pos is None:
            return

        x0, y0 = self.start_pos
        x1, y1 = x, y

        # Ensure x0 < x1 and y0 < y1
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0

        if self.filled:
            for dy in range(y0, y1 + 1):
                for dx in range(x0, x1 + 1):
                    canvas.set_pixel(dx, dy, char, color)
        else:
            # Draw border
            for dx in range(x0, x1 + 1):
                canvas.set_pixel(dx, y0, char, color)
                canvas.set_pixel(dx, y1, char, color)
            for dy in range(y0, y1 + 1):
                canvas.set_pixel(x0, dy, char, color)
                canvas.set_pixel(x1, dy, char, color)


class CircleTool(DrawingTool):
    """Circle drawing tool."""

    def __init__(self):
        super().__init__("Circle")
        self.center_pos = None

    def set_center(self, x, y):
        """Set circle center."""
        self.center_pos = (x, y)

    def draw(self, canvas, x, y, char, color):
        """Draw circle from center to radius point using Bresenham's algorithm."""
        if self.center_pos is None:
            return

        cx, cy = self.center_pos
        radius = max(abs(x - cx), abs(y - cy) // 2)  # Aspect ratio correction

        # Bresenham's Midpoint Circle Algorithm
        # Draw 8 symmetric points for each calculated point
        def draw_circle_points(xc, yc, x_offset, y_offset):
            """Draw all 8 octants of the circle."""
            points = [
                (xc + x_offset, yc + y_offset),
                (xc - x_offset, yc + y_offset),
                (xc + x_offset, yc - y_offset),
                (xc - x_offset, yc - y_offset),
                (xc + y_offset, yc + x_offset),
                (xc - y_offset, yc + x_offset),
                (xc + y_offset, yc - x_offset),
                (xc - y_offset, yc - x_offset),
            ]
            for px, py in points:
                if 0 <= px < canvas.width and 0 <= py < canvas.height:
                    canvas.set_pixel(px, py, char, color)

        x_offset = 0
        y_offset = radius
        d = 3 - 2 * radius

        draw_circle_points(cx, cy, x_offset, y_offset)

        while y_offset >= x_offset:
            x_offset += 1

            if d > 0:
                y_offset -= 1
                d = d + 4 * (x_offset - y_offset) + 10
            else:
                d = d + 4 * x_offset + 6

            draw_circle_points(cx, cy, x_offset, y_offset)


class FloodFillTool(DrawingTool):
    """Flood fill tool."""

    def __init__(self):
        super().__init__("Flood Fill")

    def draw(self, canvas, x, y, char, color):
        """Flood fill starting at position."""
        if not (0 <= x < canvas.width and 0 <= y < canvas.height):
            return

        target_char = canvas.canvas[y][x]
        target_color = canvas.colors[y][x]

        if target_char == char and target_color == color:
            return  # Already filled

        # Stack-based flood fill
        stack = [(x, y)]
        visited = set()

        while stack and len(visited) < 2000:  # Limit to prevent infinite loops
            cx, cy = stack.pop()

            if (cx, cy) in visited:
                continue
            if not (0 <= cx < canvas.width and 0 <= cy < canvas.height):
                continue

            if canvas.canvas[cy][cx] != target_char or canvas.colors[cy][cx] != target_color:
                continue

            canvas.set_pixel(cx, cy, char, color)
            visited.add((cx, cy))

            # Add neighbors
            stack.append((cx + 1, cy))
            stack.append((cx - 1, cy))
            stack.append((cx, cy + 1))
            stack.append((cx, cy - 1))


class Canvas:
    """Drawing canvas."""

    def __init__(self, width=60, height=30):
        self.width = width
        self.height = height
        self.canvas = [[' ' for _ in range(width)] for _ in range(height)]
        self.colors = [[Color.WHITE for _ in range(width)] for _ in range(height)]

    def set_pixel(self, x, y, char, color):
        """Set pixel on canvas."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.canvas[y][x] = char
            self.colors[y][x] = color

    def get_pixel(self, x, y):
        """Get pixel from canvas."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.canvas[y][x], self.colors[y][x]
        return ' ', Color.WHITE

    def clear(self):
        """Clear canvas."""
        self.canvas = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.colors = [[Color.WHITE for _ in range(self.width)] for _ in range(self.height)]

    def copy(self):
        """Create a copy of the canvas."""
        new_canvas = Canvas(self.width, self.height)
        new_canvas.canvas = [row[:] for row in self.canvas]
        new_canvas.colors = [row[:] for row in self.colors]
        return new_canvas

    def to_text(self):
        """Export as plain text."""
        lines = []
        for row in self.canvas:
            lines.append(''.join(row))
        return '\n'.join(lines)

    def to_ansi(self):
        """Export with ANSI color codes."""
        color_map = {
            Color.RED: '\033[31m',
            Color.GREEN: '\033[32m',
            Color.YELLOW: '\033[33m',
            Color.BLUE: '\033[34m',
            Color.MAGENTA: '\033[35m',
            Color.CYAN: '\033[36m',
            Color.WHITE: '\033[37m',
            Color.BRIGHT_RED: '\033[91m',
            Color.BRIGHT_GREEN: '\033[92m',
            Color.BRIGHT_YELLOW: '\033[93m',
            Color.BRIGHT_BLUE: '\033[94m',
            Color.BRIGHT_MAGENTA: '\033[95m',
            Color.BRIGHT_CYAN: '\033[96m',
            Color.BRIGHT_WHITE: '\033[97m',
        }
        reset = '\033[0m'

        lines = []
        for y in range(self.height):
            line = ''
            current_color = None

            for x in range(self.width):
                char = self.canvas[y][x]
                color = self.colors[y][x]

                if color != current_color:
                    if current_color is not None:
                        line += reset
                    line += color_map.get(color, '')
                    current_color = color

                line += char

            if current_color is not None:
                line += reset

            lines.append(line)

        return '\n'.join(lines)


class ASCIIPainter:
    """Main ASCII Painter application."""

    # Character palettes
    PALETTE_ASCII = list(' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~')
    PALETTE_BOX = list('─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬')
    PALETTE_BLOCKS = list('▀▄█▌▐░▒▓')
    PALETTE_SPECIAL = list('·•○●◦◉◯⊕⊗⊙◊◇◆⬖⬗★☆')

    COLORS = [
        Color.WHITE, Color.RED, Color.GREEN, Color.BLUE,
        Color.YELLOW, Color.MAGENTA, Color.CYAN,
        Color.BRIGHT_WHITE, Color.BRIGHT_RED, Color.BRIGHT_GREEN,
        Color.BRIGHT_BLUE, Color.BRIGHT_YELLOW, Color.BRIGHT_MAGENTA, Color.BRIGHT_CYAN
    ]

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()

        # Canvas
        self.canvas = Canvas(60, 30)

        # Cursor
        self.cursor_x = self.canvas.width // 2
        self.cursor_y = self.canvas.height // 2

        # Tools
        self.tools = {
            'freehand': FreehandTool(),
            'line': LineTool(),
            'rectangle': RectangleTool(filled=False),
            'filled_rect': RectangleTool(filled=True),
            'circle': CircleTool(),
            'flood_fill': FloodFillTool(),
        }
        self.current_tool = 'freehand'

        # Current character and color
        self.current_char = '█'
        self.current_color = Color.WHITE
        self.char_palette_index = 0
        self.color_index = 0

        # Current palette
        self.current_palette = 'blocks'
        self.palettes = {
            'ascii': self.PALETTE_ASCII,
            'box': self.PALETTE_BOX,
            'blocks': self.PALETTE_BLOCKS,
            'special': self.PALETTE_SPECIAL,
        }

        # Brush size
        self.brush_size = 1

        # Undo/Redo
        self.undo_stack = deque(maxlen=20)
        self.redo_stack = deque(maxlen=20)

        # UI state
        self.show_help = False
        self.show_grid = False
        self.message = ""
        self.message_timer = 0

        # Tool state (for multi-step tools)
        self.tool_start_set = False

        # Frame timing
        self.last_time = time.time()
        self.cursor_blink = True
        self.blink_timer = 0

    def handle_input(self, dt):
        """Handle user input."""
        # Get joystick state
        jx, jy = self.input_handler.get_joystick_state()
        buttons = self.input_handler.get_joystick_buttons()

        # Read keyboard once per frame
        key_pressed = False
        draw_action = False

        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)

            if key:
                key_pressed = True

                # Movement
                if key.name == 'KEY_LEFT' or key.lower() == 'a':
                    self.cursor_x -= 1
                elif key.name == 'KEY_RIGHT' or key.lower() == 'd':
                    self.cursor_x += 1
                elif key.name == 'KEY_UP' or key.lower() == 'w':
                    self.cursor_y -= 1
                elif key.name == 'KEY_DOWN' or key.lower() == 's':
                    self.cursor_y += 1

                # Drawing action
                elif key == ' ' or key.name == 'KEY_ENTER':
                    draw_action = True

                # Tool switching
                elif key == '1':
                    self.current_tool = 'freehand'
                    self.show_message("Tool: Freehand")
                elif key == '2':
                    self.current_tool = 'line'
                    self.show_message("Tool: Line")
                elif key == '3':
                    self.current_tool = 'rectangle'
                    self.show_message("Tool: Rectangle")
                elif key == '4':
                    self.current_tool = 'filled_rect'
                    self.show_message("Tool: Filled Rectangle")
                elif key == '5':
                    self.current_tool = 'circle'
                    self.show_message("Tool: Circle")
                elif key == '6':
                    self.current_tool = 'flood_fill'
                    self.show_message("Tool: Flood Fill")

                # Character palette
                elif key == '[':
                    self.char_palette_index = (self.char_palette_index - 1) % len(self.palettes[self.current_palette])
                    self.current_char = self.palettes[self.current_palette][self.char_palette_index]
                elif key == ']':
                    self.char_palette_index = (self.char_palette_index + 1) % len(self.palettes[self.current_palette])
                    self.current_char = self.palettes[self.current_palette][self.char_palette_index]

                # Color selection
                elif key == ',':
                    self.color_index = (self.color_index - 1) % len(self.COLORS)
                    self.current_color = self.COLORS[self.color_index]
                elif key == '.':
                    self.color_index = (self.color_index + 1) % len(self.COLORS)
                    self.current_color = self.COLORS[self.color_index]

                # Brush size
                elif key == '-':
                    self.brush_size = max(1, self.brush_size - 2)
                    self.show_message(f"Brush size: {self.brush_size}")
                elif key == '=':
                    self.brush_size = min(5, self.brush_size + 2)
                    self.show_message(f"Brush size: {self.brush_size}")

                # Undo/Redo
                elif key.lower() == 'z':
                    self.undo()
                elif key.lower() == 'y':
                    self.redo()

                # Grid toggle
                elif key.lower() == 'g':
                    self.show_grid = not self.show_grid

                # Help
                elif key.lower() == 'h':
                    self.show_help = not self.show_help

                # Clear canvas
                elif key.lower() == 'c':
                    self.save_undo()
                    self.canvas.clear()
                    self.show_message("Canvas cleared")

                # Save
                elif key.lower() == 'f':
                    self.save_drawing()

        # Joystick cursor movement (only if no keyboard movement)
        if not key_pressed and (abs(jx) > 0 or abs(jy) > 0):
            cursor_speed = 15  # chars per second
            self.cursor_x += int(jx * cursor_speed * dt)
            self.cursor_y += int(jy * cursor_speed * dt)

        # Clamp cursor
        self.cursor_x = max(0, min(self.cursor_x, self.canvas.width - 1))
        self.cursor_y = max(0, min(self.cursor_y, self.canvas.height - 1))

        # Drawing action (keyboard or button 0)
        if draw_action or buttons.get(0):
            self.perform_drawing_action()

    def perform_drawing_action(self):
        """Perform drawing action with current tool."""
        tool = self.tools[self.current_tool]

        if self.current_tool == 'freehand':
            self.save_undo()
            tool.draw(self.canvas, self.cursor_x, self.cursor_y,
                      self.current_char, self.current_color, self.brush_size)

        elif self.current_tool in ['line', 'rectangle', 'filled_rect', 'circle']:
            if not self.tool_start_set:
                # Set start position
                if hasattr(tool, 'set_start'):
                    tool.set_start(self.cursor_x, self.cursor_y)
                elif hasattr(tool, 'set_center'):
                    tool.set_center(self.cursor_x, self.cursor_y)
                self.tool_start_set = True
                self.show_message("Start point set. Move cursor and press again.")
            else:
                # Complete shape
                self.save_undo()
                tool.draw(self.canvas, self.cursor_x, self.cursor_y,
                          self.current_char, self.current_color)
                self.tool_start_set = False
                self.show_message("Shape drawn")

        elif self.current_tool == 'flood_fill':
            self.save_undo()
            tool.draw(self.canvas, self.cursor_x, self.cursor_y,
                      self.current_char, self.current_color)
            self.show_message("Fill complete")

    def save_undo(self):
        """Save current state to undo stack."""
        self.undo_stack.append(self.canvas.copy())
        self.redo_stack.clear()

    def undo(self):
        """Undo last action."""
        if self.undo_stack:
            self.redo_stack.append(self.canvas.copy())
            self.canvas = self.undo_stack.pop()
            self.show_message("Undo")

    def redo(self):
        """Redo last undone action."""
        if self.redo_stack:
            self.undo_stack.append(self.canvas.copy())
            self.canvas = self.redo_stack.pop()
            self.show_message("Redo")

    def save_drawing(self):
        """Save drawing to file."""
        # Create directory if it doesn't exist
        save_dir = os.path.expanduser("~/.atari-style/drawings")
        os.makedirs(save_dir, exist_ok=True)

        # Generate filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename_txt = os.path.join(save_dir, f"drawing_{timestamp}.txt")
        filename_ansi = os.path.join(save_dir, f"drawing_{timestamp}.ansi")

        # Save as plain text
        with open(filename_txt, 'w') as f:
            f.write(self.canvas.to_text())

        # Save as ANSI
        with open(filename_ansi, 'w') as f:
            f.write(self.canvas.to_ansi())

        self.show_message(f"Saved to {filename_txt}")

    def show_message(self, message):
        """Show temporary message."""
        self.message = message
        self.message_timer = 2.0  # Show for 2 seconds

    def update(self, dt):
        """Update application state."""
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt

        # Update cursor blink
        self.blink_timer += dt
        if self.blink_timer >= 0.5:
            self.blink_timer = 0
            self.cursor_blink = not self.cursor_blink

    def draw(self):
        """Draw the application."""
        self.renderer.clear_buffer()

        # Draw canvas
        canvas_offset_x = 2
        canvas_offset_y = 3

        # Draw canvas border
        self.renderer.draw_border(canvas_offset_x - 1, canvas_offset_y - 1,
                                   self.canvas.width + 2, self.canvas.height + 2,
                                   Color.CYAN)

        # Draw canvas contents
        for y in range(self.canvas.height):
            for x in range(self.canvas.width):
                char, color = self.canvas.get_pixel(x, y)
                screen_x = canvas_offset_x + x
                screen_y = canvas_offset_y + y

                # Draw grid if enabled
                if self.show_grid and (x % 5 == 0 or y % 5 == 0):
                    if char == ' ':
                        self.renderer.set_pixel(screen_x, screen_y, '·', Color.BLUE)
                    else:
                        self.renderer.set_pixel(screen_x, screen_y, char, color)
                else:
                    self.renderer.set_pixel(screen_x, screen_y, char, color)

        # Draw cursor
        if self.cursor_blink:
            cursor_screen_x = canvas_offset_x + self.cursor_x
            cursor_screen_y = canvas_offset_y + self.cursor_y
            self.renderer.set_pixel(cursor_screen_x, cursor_screen_y, '+', Color.BRIGHT_YELLOW)

        # Draw HUD
        self._draw_hud()

        # Draw help if enabled
        if self.show_help:
            self._draw_help()

        self.renderer.render()

    def _draw_hud(self):
        """Draw heads-up display."""
        # Title
        title = "ASCII PAINTER"
        self.renderer.draw_text(2, 0, title, Color.BRIGHT_CYAN)

        # Current tool
        tool_text = f"Tool: {self.tools[self.current_tool].name}"
        self.renderer.draw_text(2, 1, tool_text, Color.BRIGHT_WHITE)

        # Current character and color
        char_text = f"Char: '{self.current_char}'"
        self.renderer.draw_text(20, 1, char_text, self.current_color)

        color_text = f"Color: {self.current_color}"
        self.renderer.draw_text(35, 1, color_text, self.current_color)

        # Brush size
        brush_text = f"Brush: {self.brush_size}x{self.brush_size}"
        self.renderer.draw_text(55, 1, brush_text, Color.WHITE)

        # Cursor position
        pos_text = f"Pos: ({self.cursor_x}, {self.cursor_y})"
        self.renderer.draw_text(70, 1, pos_text, Color.WHITE)

        # Undo levels
        undo_text = f"Undo: {len(self.undo_stack)}"
        self.renderer.draw_text(90, 1, undo_text, Color.YELLOW)

        # Message
        if self.message_timer > 0:
            msg_x = self.renderer.width // 2 - len(self.message) // 2
            self.renderer.draw_text(msg_x, self.renderer.height - 1,
                                    self.message, Color.BRIGHT_GREEN)

        # Controls hint
        hint = "H:Help  F:Save  G:Grid  C:Clear  Z:Undo  Y:Redo  1-6:Tools  []:<>:Char  ,.Color  -=:Brush  ESC:Exit"
        if len(hint) < self.renderer.width:
            self.renderer.draw_text(2, self.renderer.height - 2, hint, Color.CYAN)

    def _draw_help(self):
        """Draw help overlay."""
        # Draw semi-transparent background
        help_x = self.renderer.width // 2 - 30
        help_y = self.renderer.height // 2 - 10
        help_width = 60
        help_height = 20

        # Border
        self.renderer.draw_border(help_x, help_y, help_width, help_height, Color.BRIGHT_YELLOW)

        # Title
        title = "HELP"
        self.renderer.draw_text(help_x + help_width // 2 - len(title) // 2, help_y + 1,
                                title, Color.BRIGHT_YELLOW)

        # Help text
        help_lines = [
            "MOVEMENT:",
            "  Arrow Keys / WASD / Joystick - Move cursor",
            "",
            "DRAWING:",
            "  Space / Enter / Button 0 - Draw",
            "  1-6 - Select tool (Freehand/Line/Rect/FilledRect/Circle/Fill)",
            "  [ ] - Previous/Next character",
            "  , . - Previous/Next color",
            "  - = - Decrease/Increase brush size",
            "",
            "EDITING:",
            "  Z - Undo    Y - Redo    C - Clear canvas",
            "",
            "VIEW:",
            "  G - Toggle grid    H - Toggle help",
            "",
            "FILE:",
            "  F - Save drawing (saves to ~/.atari-style/drawings/)",
        ]

        y = help_y + 3
        for line in help_lines:
            if y < help_y + help_height - 1:
                self.renderer.draw_text(help_x + 2, y, line[:help_width - 4], Color.WHITE)
                y += 1

    def run(self):
        """Main application loop."""
        self.renderer.enter_fullscreen()

        try:
            running = True

            while running:
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time

                # Cap dt
                dt = min(dt, 0.1)

                # Handle input
                input_type = self.input_handler.get_input(timeout=0.001)

                if input_type == InputType.BACK or input_type == InputType.QUIT:
                    running = False

                # Continuous input
                self.handle_input(dt)

                # Update
                self.update(dt)

                # Draw
                self.draw()

                # Frame rate (30 FPS)
                time.sleep(0.033)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()


def run_ascii_painter():
    """Entry point for ASCII Painter."""
    painter = ASCIIPainter()
    painter.run()


if __name__ == "__main__":
    run_ascii_painter()
