"""Menu system for demo selection."""

from typing import List, Callable, Optional
from .renderer import Renderer, Color
from .input_handler import InputHandler, InputType
import time


class MenuItem:
    """Represents a menu item."""

    def __init__(self, title: str, action: Callable, description: str = ""):
        self.title = title
        self.action = action
        self.description = description


class Menu:
    """Interactive menu system."""

    def __init__(self, title: str, items: List[MenuItem]):
        self.title = title
        self.items = items
        self.selected_index = 0
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True

    def draw(self):
        """Draw the menu."""
        self.renderer.clear_buffer()

        # Draw title
        title_x = (self.renderer.width - len(self.title)) // 2
        self.renderer.draw_text(title_x, 3, self.title, Color.BRIGHT_CYAN)

        # Draw subtitle/instructions
        instructions = "Use Arrow Keys/WASD or Joystick | ENTER/SPACE to Select | Q/ESC to Exit"
        inst_x = (self.renderer.width - len(instructions)) // 2
        self.renderer.draw_text(inst_x, 5, instructions, Color.YELLOW)

        # Draw menu items
        menu_start_y = 8
        max_width = max(len(item.title) for item in self.items) + 4

        for i, item in enumerate(self.items):
            y = menu_start_y + i * 2
            x = (self.renderer.width - max_width) // 2

            if i == self.selected_index:
                # Highlight selected item
                self.renderer.draw_text(x - 2, y, '>', Color.BRIGHT_GREEN)
                self.renderer.draw_text(x, y, item.title, Color.BRIGHT_GREEN)
                self.renderer.draw_text(x + len(item.title) + 2, y, '<', Color.BRIGHT_GREEN)

                # Draw description if available
                if item.description:
                    desc_x = (self.renderer.width - len(item.description)) // 2
                    self.renderer.draw_text(desc_x, self.renderer.height - 3, item.description, Color.CYAN)
            else:
                self.renderer.draw_text(x, y, item.title, Color.WHITE)

        # Draw decorative border
        border_width = max_width + 8
        border_height = len(self.items) * 2 + 4
        border_x = (self.renderer.width - border_width) // 2
        border_y = menu_start_y - 2
        self.renderer.draw_border(border_x, border_y, border_width, border_height, Color.MAGENTA)

        self.renderer.render()

    def handle_input(self):
        """Handle user input."""
        input_type = self.input_handler.get_input(timeout=0.05)

        if input_type == InputType.UP:
            self.selected_index = (self.selected_index - 1) % len(self.items)
            time.sleep(0.15)  # Debounce
        elif input_type == InputType.DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.items)
            time.sleep(0.15)  # Debounce
        elif input_type == InputType.SELECT:
            # Execute selected action
            self.items[self.selected_index].action()
            time.sleep(0.2)  # Debounce
            # Redraw after returning from action
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()
        elif input_type == InputType.QUIT or input_type == InputType.BACK:
            self.running = False

    def run(self):
        """Run the menu loop."""
        try:
            self.renderer.enter_fullscreen()
            self.renderer.clear_screen()
            time.sleep(0.1)  # Let terminal settle

            while self.running:
                self.draw()
                self.handle_input()

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()
