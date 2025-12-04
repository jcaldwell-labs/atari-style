"""Canvas Explorer - Boxes-live style infinite canvas with zoom/pan/edit.

A terminal-based canvas explorer inspired by boxes-live. Features:
- 20 levels of zoom (logarithmic scale)
- Grid display with scale indicators
- Cursor navigation via joystick/keyboard/mouse
- Marker placement and box creation
- Input mode switching (navigate, select, edit)

This is atari-style's implementation of the boxes-live interface concepts,
providing a simpler but compatible canvas experience.
"""

import time
import math
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from ...core.renderer import Renderer, Color
from ...core.input_handler import InputHandler, InputType


# =============================================================================
# Input Modes
# =============================================================================

class InputMode(Enum):
    """Input mode determines how controls are interpreted."""
    NAVIGATE = auto()   # Pan/zoom canvas
    SELECT = auto()     # Select boxes
    EDIT = auto()       # Edit selected box
    CREATE = auto()     # Create new marker/box


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Marker:
    """A point marker on the canvas."""
    x: float
    y: float
    label: str = ""
    color: int = Color.WHITE

    def __hash__(self):
        return hash((self.x, self.y))


@dataclass
class Box:
    """A rectangular box on the canvas."""
    id: int
    x: float
    y: float
    width: float
    height: float
    title: str = ""
    content: List[str] = field(default_factory=list)
    color: int = Color.CYAN
    selected: bool = False

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    def contains_point(self, px: float, py: float) -> bool:
        """Check if point is inside box."""
        return self.x <= px <= self.x2 and self.y <= py <= self.y2


# =============================================================================
# Zoom System
# =============================================================================

class ZoomController:
    """Manages 20 levels of zoom with logarithmic scaling."""

    # 20 zoom levels from 0.1x to 10x (logarithmic distribution)
    ZOOM_LEVELS = [
        0.1, 0.125, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.65, 0.8,
        1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.5, 10.0
    ]

    def __init__(self, initial_level: int = 10):  # Start at 1.0x
        self.level = initial_level

    @property
    def scale(self) -> float:
        """Current zoom scale factor."""
        return self.ZOOM_LEVELS[self.level]

    @property
    def level_count(self) -> int:
        return len(self.ZOOM_LEVELS)

    def zoom_in(self) -> bool:
        """Zoom in one level. Returns True if changed."""
        if self.level < len(self.ZOOM_LEVELS) - 1:
            self.level += 1
            return True
        return False

    def zoom_out(self) -> bool:
        """Zoom out one level. Returns True if changed."""
        if self.level > 0:
            self.level -= 1
            return True
        return False

    def set_level(self, level: int) -> None:
        """Set zoom to specific level."""
        self.level = max(0, min(level, len(self.ZOOM_LEVELS) - 1))

    def format_scale(self) -> str:
        """Format current scale for display."""
        return f"{self.scale:.2f}x"


# =============================================================================
# Grid System
# =============================================================================

class GridDisplay:
    """Manages grid display with adaptive scale indicators."""

    def __init__(self):
        self.visible = True
        self.show_dots = True
        self.show_axes = True
        self.show_labels = True

    def get_grid_spacing(self, zoom_scale: float) -> Tuple[float, float]:
        """Calculate grid spacing based on zoom level.

        Uses a log10-based system where grid lines appear at:
        - 1, 10, 100, 1000... when zoomed out
        - 0.1, 0.01... when zoomed in
        """
        # Base spacing that looks good at 1x zoom (about 10 chars apart)
        base_spacing = 10.0

        # Scale by zoom
        world_spacing = base_spacing / zoom_scale

        # Snap to power of 10 for clean numbers
        log_spacing = math.log10(world_spacing)
        major_spacing = 10 ** round(log_spacing)
        minor_spacing = major_spacing / 5

        return (major_spacing, minor_spacing)

    def toggle(self) -> None:
        """Toggle grid visibility."""
        self.visible = not self.visible

    def toggle_dots(self) -> None:
        """Toggle dot display."""
        self.show_dots = not self.show_dots

    def toggle_axes(self) -> None:
        """Toggle axis display."""
        self.show_axes = not self.show_axes


# =============================================================================
# Canvas Model
# =============================================================================

class CanvasModel:
    """The infinite canvas data model."""

    def __init__(self, world_width: float = 1000.0, world_height: float = 1000.0):
        self.world_width = world_width
        self.world_height = world_height
        self.markers: List[Marker] = []
        self.boxes: List[Box] = []
        self.next_box_id = 1

    def add_marker(self, x: float, y: float, label: str = "",
                   color: int = Color.YELLOW) -> Marker:
        """Add a marker to the canvas."""
        marker = Marker(x=x, y=y, label=label, color=color)
        self.markers.append(marker)
        return marker

    def add_box(self, x: float, y: float, width: float = 20.0,
                height: float = 8.0, title: str = "",
                color: int = Color.CYAN) -> Box:
        """Add a box to the canvas."""
        box = Box(
            id=self.next_box_id,
            x=x, y=y,
            width=width, height=height,
            title=title or f"Box {self.next_box_id}",
            color=color
        )
        self.next_box_id += 1
        self.boxes.append(box)
        return box

    def marker_to_box(self, marker: Marker, width: float = 20.0,
                      height: float = 8.0) -> Box:
        """Convert a marker to a box (stretch operation)."""
        if marker in self.markers:
            self.markers.remove(marker)
        return self.add_box(
            x=marker.x - width / 2,
            y=marker.y - height / 2,
            width=width,
            height=height,
            title=marker.label or f"Box {self.next_box_id}",
            color=marker.color
        )

    def get_box_at(self, x: float, y: float) -> Optional[Box]:
        """Get box at world coordinates (topmost)."""
        for box in reversed(self.boxes):  # Check from top to bottom
            if box.contains_point(x, y):
                return box
        return None

    def select_box(self, box: Optional[Box]) -> None:
        """Select a box, deselecting others."""
        for b in self.boxes:
            b.selected = (b is box)

    def get_selected_box(self) -> Optional[Box]:
        """Get currently selected box."""
        for box in self.boxes:
            if box.selected:
                return box
        return None

    def delete_selected(self) -> bool:
        """Delete selected box. Returns True if deleted."""
        selected = self.get_selected_box()
        if selected:
            self.boxes.remove(selected)
            return True
        return False

    def move_box(self, box: Box, dx: float, dy: float) -> None:
        """Move a box by delta."""
        box.x += dx
        box.y += dy


# =============================================================================
# Viewport
# =============================================================================

class Viewport:
    """Manages the view into the infinite canvas."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Camera position (world coordinates of screen center)
        self.camera_x = 0.0
        self.camera_y = 0.0

        self.zoom = ZoomController()

    def pan(self, dx: float, dy: float) -> None:
        """Pan camera by screen-space delta."""
        # Convert screen delta to world delta (inverse of zoom)
        self.camera_x += dx / self.zoom.scale
        self.camera_y += dy / self.zoom.scale

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        # Center of screen is (camera_x, camera_y)
        sx = (wx - self.camera_x) * self.zoom.scale + self.screen_width / 2
        sy = (wy - self.camera_y) * self.zoom.scale + self.screen_height / 2
        return (int(sx), int(sy))

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        wx = (sx - self.screen_width / 2) / self.zoom.scale + self.camera_x
        wy = (sy - self.screen_height / 2) / self.zoom.scale + self.camera_y
        return (wx, wy)

    def get_visible_world_bounds(self) -> Tuple[float, float, float, float]:
        """Get visible world area (x1, y1, x2, y2)."""
        half_w = (self.screen_width / 2) / self.zoom.scale
        half_h = (self.screen_height / 2) / self.zoom.scale
        return (
            self.camera_x - half_w,
            self.camera_y - half_h,
            self.camera_x + half_w,
            self.camera_y + half_h
        )

    def center_on(self, wx: float, wy: float) -> None:
        """Center viewport on world point."""
        self.camera_x = wx
        self.camera_y = wy


# =============================================================================
# Canvas Renderer
# =============================================================================

class CanvasRenderer:
    """Renders the canvas to terminal."""

    # Box drawing characters
    BOX_CHARS = {
        'tl': '+', 'tr': '+', 'bl': '+', 'br': '+',
        'h': '-', 'v': '|',
        'sel_tl': '#', 'sel_tr': '#', 'sel_bl': '#', 'sel_br': '#',
    }

    def __init__(self, renderer: Renderer):
        self.renderer = renderer

    def draw_grid(self, viewport: Viewport, grid: GridDisplay) -> None:
        """Draw grid lines and labels."""
        if not grid.visible:
            return

        bounds = viewport.get_visible_world_bounds()
        major, minor = grid.get_grid_spacing(viewport.zoom.scale)

        # Draw minor grid dots
        if grid.show_dots and viewport.zoom.scale >= 0.5:
            start_x = math.floor(bounds[0] / minor) * minor
            start_y = math.floor(bounds[1] / minor) * minor

            wx = start_x
            while wx < bounds[2]:
                wy = start_y
                while wy < bounds[3]:
                    sx, sy = viewport.world_to_screen(wx, wy)
                    if 0 <= sx < self.renderer.width and 0 <= sy < self.renderer.height:
                        self.renderer.set_pixel(sx, sy, '.', Color.BLUE)
                    wy += minor
                wx += minor

        # Draw major grid lines
        start_x = math.floor(bounds[0] / major) * major
        start_y = math.floor(bounds[1] / major) * major

        # Vertical lines
        wx = start_x
        while wx < bounds[2]:
            sx, _ = viewport.world_to_screen(wx, 0)
            if 0 <= sx < self.renderer.width:
                for sy in range(self.renderer.height):
                    char = '|' if wx != 0 else '|'
                    color = Color.CYAN if wx != 0 else Color.BRIGHT_CYAN
                    self.renderer.set_pixel(sx, sy, char, color)
            wx += major

        # Horizontal lines
        wy = start_y
        while wy < bounds[3]:
            _, sy = viewport.world_to_screen(0, wy)
            if 0 <= sy < self.renderer.height:
                for sx in range(self.renderer.width):
                    char = '-' if wy != 0 else '-'
                    color = Color.CYAN if wy != 0 else Color.BRIGHT_CYAN
                    self.renderer.set_pixel(sx, sy, char, color)
            wy += major

        # Draw axes (brighter)
        if grid.show_axes:
            # Y axis (vertical line at x=0)
            sx, _ = viewport.world_to_screen(0, 0)
            if 0 <= sx < self.renderer.width:
                for sy in range(self.renderer.height):
                    self.renderer.set_pixel(sx, sy, '|', Color.WHITE)

            # X axis (horizontal line at y=0)
            _, sy = viewport.world_to_screen(0, 0)
            if 0 <= sy < self.renderer.height:
                for sx in range(self.renderer.width):
                    self.renderer.set_pixel(sx, sy, '-', Color.WHITE)

            # Origin marker
            sx, sy = viewport.world_to_screen(0, 0)
            if 0 <= sx < self.renderer.width and 0 <= sy < self.renderer.height:
                self.renderer.set_pixel(sx, sy, '+', Color.BRIGHT_WHITE)

        # Draw scale labels
        if grid.show_labels:
            # Label major grid lines
            wx = start_x
            while wx < bounds[2]:
                sx, sy_origin = viewport.world_to_screen(wx, 0)
                # Draw label near x axis
                label = f"{wx:.0f}" if wx == int(wx) else f"{wx:.1f}"
                sy = min(sy_origin + 1, self.renderer.height - 1)
                if 0 <= sx < self.renderer.width - len(label) and 0 <= sy < self.renderer.height:
                    for i, c in enumerate(label):
                        self.renderer.set_pixel(sx + i, sy, c, Color.YELLOW)
                wx += major

    def draw_marker(self, marker: Marker, viewport: Viewport) -> None:
        """Draw a single marker."""
        sx, sy = viewport.world_to_screen(marker.x, marker.y)

        if not (0 <= sx < self.renderer.width and 0 <= sy < self.renderer.height):
            return

        # Draw marker symbol
        self.renderer.set_pixel(sx, sy, '*', marker.color)

        # Draw label if present
        if marker.label:
            label_x = sx + 2
            if label_x + len(marker.label) < self.renderer.width:
                for i, c in enumerate(marker.label):
                    self.renderer.set_pixel(label_x + i, sy, c, marker.color)

    def draw_box(self, box: Box, viewport: Viewport) -> None:
        """Draw a single box."""
        # Get screen coordinates of box corners
        sx1, sy1 = viewport.world_to_screen(box.x, box.y)
        sx2, sy2 = viewport.world_to_screen(box.x2, box.y2)

        # Clip to screen bounds
        sx1_clip = max(0, min(sx1, self.renderer.width - 1))
        sy1_clip = max(0, min(sy1, self.renderer.height - 1))
        sx2_clip = max(0, min(sx2, self.renderer.width - 1))
        sy2_clip = max(0, min(sy2, self.renderer.height - 1))

        # Check if visible
        if sx2 < 0 or sx1 >= self.renderer.width:
            return
        if sy2 < 0 or sy1 >= self.renderer.height:
            return

        color = Color.BRIGHT_WHITE if box.selected else box.color
        corner = '#' if box.selected else '+'

        # Draw box border
        # Top edge
        if 0 <= sy1 < self.renderer.height:
            for sx in range(sx1_clip, sx2_clip + 1):
                char = corner if sx == sx1 or sx == sx2 else '-'
                self.renderer.set_pixel(sx, sy1, char, color)

        # Bottom edge
        if 0 <= sy2 < self.renderer.height:
            for sx in range(sx1_clip, sx2_clip + 1):
                char = corner if sx == sx1 or sx == sx2 else '-'
                self.renderer.set_pixel(sx, sy2, char, color)

        # Left edge
        if 0 <= sx1 < self.renderer.width:
            for sy in range(sy1_clip + 1, sy2_clip):
                self.renderer.set_pixel(sx1, sy, '|', color)

        # Right edge
        if 0 <= sx2 < self.renderer.width:
            for sy in range(sy1_clip + 1, sy2_clip):
                self.renderer.set_pixel(sx2, sy, '|', color)

        # Draw title
        if box.title and sy1 >= 0 and sy1 < self.renderer.height:
            title_x = sx1 + 2
            if title_x > 0:
                title = box.title[:sx2 - sx1 - 3] if sx2 - sx1 > 3 else ""
                for i, c in enumerate(title):
                    px = title_x + i
                    if 0 <= px < self.renderer.width:
                        self.renderer.set_pixel(px, sy1, c, color)

        # Draw content (if zoomed in enough)
        if viewport.zoom.scale >= 0.8 and box.content:
            content_y = sy1 + 1
            for line in box.content[:sy2 - sy1 - 1]:
                if 0 <= content_y < self.renderer.height:
                    content_x = sx1 + 1
                    text = line[:sx2 - sx1 - 1]
                    for i, c in enumerate(text):
                        px = content_x + i
                        if 0 <= px < self.renderer.width:
                            self.renderer.set_pixel(px, content_y, c, Color.WHITE)
                content_y += 1

    def draw_cursor(self, sx: int, sy: int, mode: InputMode) -> None:
        """Draw cursor at screen position."""
        if not (0 <= sx < self.renderer.width and 0 <= sy < self.renderer.height):
            return

        # Different cursor appearance per mode
        if mode == InputMode.NAVIGATE:
            char, color = '+', Color.BRIGHT_WHITE
        elif mode == InputMode.SELECT:
            char, color = '>', Color.YELLOW
        elif mode == InputMode.CREATE:
            char, color = 'X', Color.GREEN
        elif mode == InputMode.EDIT:
            char, color = '@', Color.MAGENTA
        else:
            char, color = '+', Color.WHITE

        self.renderer.set_pixel(sx, sy, char, color)

    def draw_status_bar(self, cursor_world: Tuple[float, float],
                        zoom: ZoomController, mode: InputMode,
                        selected_box: Optional[Box]) -> None:
        """Draw status bar at bottom of screen."""
        y = self.renderer.height - 1

        # Clear status line
        for x in range(self.renderer.width):
            self.renderer.set_pixel(x, y, ' ', Color.WHITE)

        # Mode indicator
        mode_text = f"[{mode.name}]"
        for i, c in enumerate(mode_text):
            self.renderer.set_pixel(i, y, c, Color.CYAN)

        # Position
        pos_text = f" ({cursor_world[0]:.1f}, {cursor_world[1]:.1f})"
        offset = len(mode_text)
        for i, c in enumerate(pos_text):
            self.renderer.set_pixel(offset + i, y, c, Color.WHITE)

        # Zoom
        zoom_text = f" Zoom: {zoom.format_scale()} [{zoom.level+1}/{zoom.level_count}]"
        offset += len(pos_text)
        for i, c in enumerate(zoom_text):
            if offset + i < self.renderer.width:
                self.renderer.set_pixel(offset + i, y, c, Color.GREEN)

        # Selected box info
        if selected_box:
            sel_text = f" | Box: {selected_box.title}"
            offset += len(zoom_text)
            for i, c in enumerate(sel_text):
                if offset + i < self.renderer.width:
                    self.renderer.set_pixel(offset + i, y, c, Color.YELLOW)

        # Help hint (right aligned)
        help_text = "H:Help Q:Quit"
        help_start = self.renderer.width - len(help_text) - 1
        if help_start > offset:
            for i, c in enumerate(help_text):
                self.renderer.set_pixel(help_start + i, y, c, Color.CYAN)

    def draw_help(self) -> None:
        """Draw help overlay."""
        help_lines = [
            "=== Canvas Explorer Help ===",
            "",
            "Navigation (all modes):",
            "  Arrows/WASD/Joystick: Move cursor",
            "  +/- or Triggers: Zoom in/out",
            "  G: Toggle grid  Q: Quit",
            "",
            "Mode Switching:",
            "  Tab: Cycle modes",
            "  N: Navigate  V: Select",
            "  C: Create    E: Edit (box sel.)",
            "",
            "Actions:",
            "  Enter/Space/Btn0: Mode action",
            "    Navigate: Center view",
            "    Select: Select box at cursor",
            "    Create: Place marker",
            "    Edit: Stretch marker to box",
            "  Delete/Backspace: Delete selected",
            "",
            "Press any key to close...",
        ]

        # Draw semi-transparent overlay
        box_width = max(len(line) for line in help_lines) + 4
        box_height = len(help_lines) + 2
        start_x = (self.renderer.width - box_width) // 2
        start_y = (self.renderer.height - box_height) // 2

        # Draw background
        for dy in range(box_height):
            for dx in range(box_width):
                self.renderer.set_pixel(start_x + dx, start_y + dy, ' ', Color.WHITE)

        # Draw border
        for dx in range(box_width):
            self.renderer.set_pixel(start_x + dx, start_y, '=', Color.CYAN)
            self.renderer.set_pixel(start_x + dx, start_y + box_height - 1, '=', Color.CYAN)
        for dy in range(box_height):
            self.renderer.set_pixel(start_x, start_y + dy, '|', Color.CYAN)
            self.renderer.set_pixel(start_x + box_width - 1, start_y + dy, '|', Color.CYAN)

        # Draw text
        for i, line in enumerate(help_lines):
            for j, c in enumerate(line):
                self.renderer.set_pixel(start_x + 2 + j, start_y + 1 + i, c, Color.WHITE)


# =============================================================================
# Main Application
# =============================================================================

class CanvasExplorer:
    """Main canvas explorer application."""

    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.canvas_renderer = CanvasRenderer(self.renderer)

        # Initialize after renderer to get screen size
        self.viewport = Viewport(self.renderer.width, self.renderer.height - 1)
        self.canvas = CanvasModel()
        self.grid = GridDisplay()

        # Cursor (screen coordinates)
        self.cursor_x = self.renderer.width // 2
        self.cursor_y = self.renderer.height // 2

        # State
        self.mode = InputMode.NAVIGATE
        self.running = True
        self.show_help = False

        # Marker being stretched
        self.active_marker: Optional[Marker] = None

        # Timing
        self.last_time = time.time()

        # Create some demo content
        self._create_demo_content()

    def _create_demo_content(self) -> None:
        """Create initial demo boxes and markers."""
        # Add origin marker
        self.canvas.add_marker(0, 0, "Origin", Color.GREEN)

        # Add some demo boxes
        self.canvas.add_box(-30, -15, 25, 8, "Welcome", Color.CYAN)
        self.canvas.boxes[-1].content = ["Canvas Explorer", "Zoom & Pan demo"]

        self.canvas.add_box(10, -10, 20, 6, "Box 2", Color.YELLOW)
        self.canvas.add_box(-20, 10, 22, 7, "Box 3", Color.MAGENTA)

    def handle_input(self, dt: float) -> None:
        """Process input for current frame."""
        # Get joystick state
        joy_x, joy_y = self.input_handler.get_joystick_state()
        buttons = self.input_handler.get_joystick_buttons()

        # Cursor movement speed (screen chars per second)
        cursor_speed = 30.0
        key_pressed = False

        # Read keyboard directly (like ascii_painter)
        with self.input_handler.term.cbreak():
            key = self.input_handler.term.inkey(timeout=0.001)

            if key:
                key_pressed = True

                # Help overlay dismissal
                if self.show_help:
                    self.show_help = False
                    return

                # Quit
                if key.lower() == 'x' or key.name == 'KEY_ESCAPE':
                    self.running = False
                    return

                # Cursor movement
                if key.name == 'KEY_UP' or key.lower() == 'w':
                    self.cursor_y = max(0, self.cursor_y - 1)
                elif key.name == 'KEY_DOWN' or key.lower() == 's':
                    self.cursor_y = min(self.renderer.height - 2, self.cursor_y + 1)
                elif key.name == 'KEY_LEFT' or key.lower() == 'a':
                    self.cursor_x = max(0, self.cursor_x - 1)
                elif key.name == 'KEY_RIGHT' or key.lower() == 'd':
                    self.cursor_x = min(self.renderer.width - 1, self.cursor_x + 1)

                # Action
                elif key == ' ' or key.name == 'KEY_ENTER':
                    self._do_action()

                # Help
                elif key.lower() == 'h':
                    self.show_help = True

                # Grid toggle
                elif key.lower() == 'g':
                    self.grid.toggle()

                # Zoom
                elif key == '+' or key == '=':
                    self.viewport.zoom.zoom_in()
                elif key == '-':
                    self.viewport.zoom.zoom_out()

                # Mode switching
                elif key.lower() == 'n':
                    self.mode = InputMode.NAVIGATE
                elif key.lower() == 'v':  # 'v' for view/select
                    self.mode = InputMode.SELECT
                elif key.lower() == 'c':
                    self.mode = InputMode.CREATE
                elif key.lower() == 'e':
                    if self.canvas.get_selected_box():
                        self.mode = InputMode.EDIT
                elif key.name == 'KEY_TAB':
                    # Cycle modes
                    modes = list(InputMode)
                    idx = modes.index(self.mode)
                    self.mode = modes[(idx + 1) % len(modes)]

                # Delete
                elif key.name == 'KEY_DELETE' or key.name == 'KEY_BACKSPACE':
                    if self.mode == InputMode.SELECT or self.mode == InputMode.EDIT:
                        self.canvas.delete_selected()
                        self.mode = InputMode.SELECT

                # Quick quit
                elif key.lower() == 'q':
                    self.running = False
                    return

        # Apply joystick movement (only if no keyboard movement)
        if not key_pressed and (abs(joy_x) > 0.1 or abs(joy_y) > 0.1):
            self.cursor_x += int(joy_x * cursor_speed * dt)
            self.cursor_y += int(joy_y * cursor_speed * dt)

        # Clamp cursor to screen
        self.cursor_x = max(0, min(self.cursor_x, self.renderer.width - 1))
        self.cursor_y = max(0, min(self.cursor_y, self.renderer.height - 2))  # Leave status bar

        # Joystick buttons
        if buttons.get(0):  # Button 0 - action
            self._do_action()
        if buttons.get(4):  # L trigger - zoom out
            self.viewport.zoom.zoom_out()
        if buttons.get(5):  # R trigger - zoom in
            self.viewport.zoom.zoom_in()

    def _do_action(self) -> None:
        """Perform mode-specific action."""
        cursor_world = self.viewport.screen_to_world(self.cursor_x, self.cursor_y)

        if self.mode == InputMode.NAVIGATE:
            # Center view on cursor
            self.viewport.center_on(*cursor_world)
            # Reset cursor to center
            self.cursor_x = self.renderer.width // 2
            self.cursor_y = self.renderer.height // 2

        elif self.mode == InputMode.SELECT:
            # Select box at cursor
            box = self.canvas.get_box_at(*cursor_world)
            self.canvas.select_box(box)
            if box:
                self.mode = InputMode.EDIT

        elif self.mode == InputMode.CREATE:
            # Place marker
            marker = self.canvas.add_marker(*cursor_world, color=Color.YELLOW)
            self.active_marker = marker

        elif self.mode == InputMode.EDIT:
            # If we have an active marker, stretch it to a box
            if self.active_marker:
                self.canvas.marker_to_box(self.active_marker)
                self.active_marker = None
                self.mode = InputMode.SELECT

    def update(self, dt: float) -> None:
        """Update canvas state."""
        # In NAVIGATE mode, cursor movement also pans view
        if self.mode == InputMode.NAVIGATE:
            # Pan when cursor near edges
            edge_margin = 5
            pan_speed = 20.0

            if self.cursor_x < edge_margin:
                self.viewport.pan(-pan_speed * dt, 0)
            elif self.cursor_x > self.renderer.width - edge_margin:
                self.viewport.pan(pan_speed * dt, 0)

            if self.cursor_y < edge_margin:
                self.viewport.pan(0, -pan_speed * dt)
            elif self.cursor_y > self.renderer.height - edge_margin - 1:
                self.viewport.pan(0, pan_speed * dt)

    def draw(self) -> None:
        """Render the canvas."""
        self.renderer.clear_buffer()

        # Draw grid
        self.canvas_renderer.draw_grid(self.viewport, self.grid)

        # Draw boxes
        for box in self.canvas.boxes:
            self.canvas_renderer.draw_box(box, self.viewport)

        # Draw markers
        for marker in self.canvas.markers:
            self.canvas_renderer.draw_marker(marker, self.viewport)

        # Draw cursor
        self.canvas_renderer.draw_cursor(self.cursor_x, self.cursor_y, self.mode)

        # Draw status bar
        cursor_world = self.viewport.screen_to_world(self.cursor_x, self.cursor_y)
        self.canvas_renderer.draw_status_bar(
            cursor_world,
            self.viewport.zoom,
            self.mode,
            self.canvas.get_selected_box()
        )

        # Draw help overlay if active
        if self.show_help:
            self.canvas_renderer.draw_help()

        self.renderer.render()

    def run(self) -> None:
        """Main loop."""
        try:
            self.renderer.enter_fullscreen()

            while self.running:
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time

                self.handle_input(dt)
                self.update(dt)
                self.draw()

                # Target ~30 FPS
                time.sleep(0.033)

        finally:
            self.renderer.exit_fullscreen()


def run_canvas_explorer():
    """Entry point for canvas explorer."""
    explorer = CanvasExplorer()
    explorer.run()


if __name__ == '__main__':
    run_canvas_explorer()
