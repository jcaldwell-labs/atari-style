"""Simplified main menu system with clean navigation.

Provides a minimal, scannable menu for games, tools, and demos
with keyboard and joystick support.
"""

import sys
from pathlib import Path
from ..engine.renderer import Renderer, Color
from ..engine.input_handler import InputHandler, InputType
from .game_registry import GameRegistry, GameCategory


class EnhancedMenu:
    """Clean menu with category grouping and simple navigation."""

    def __init__(self, registry: GameRegistry):
        """Initialize menu.

        Args:
            registry: Game registry with discovered games
        """
        self.registry = registry
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.selected_index = 0
        self.running = True

        # Build menu items from registry
        self.menu_items = self._build_menu_items()

    def _build_menu_items(self):
        """Build menu items from game registry.

        Returns:
            List of menu items organized by category
        """
        items = []

        # Add games for each category with simple category labels
        for category in GameCategory:
            games = self.registry.get_games_by_category(category)
            if not games:
                continue

            # Category label (non-selectable)
            items.append({
                'type': 'category',
                'name': category.value.upper(),
            })

            # Games in this category
            for game in games:
                items.append({
                    'type': 'game',
                    'title': game.title,
                    'description': game.description,
                    'action': game.run_function,
                    'joystick': game.joystick_support,
                })

        # Add exit option
        items.append({
            'type': 'category',
            'name': 'SYSTEM',
        })
        items.append({
            'type': 'game',
            'title': 'Exit',
            'description': 'Exit Terminal Arcade',
            'action': self._exit_menu,
            'joystick': False,
        })

        return items

    def _exit_menu(self):
        """Exit the menu."""
        self.running = False

    def _get_selectable_items(self):
        """Get indices of selectable menu items.

        Returns:
            List of indices for items that can be selected
        """
        return [i for i, item in enumerate(self.menu_items) if item['type'] == 'game']

    def draw(self):
        """Draw the menu."""
        self.renderer.clear_buffer()

        # Title - simple centered text
        title = "TERMINAL ARCADE"
        title_x = (self.renderer.width - len(title)) // 2
        self.renderer.draw_text(title_x, 1, title, Color.BRIGHT_CYAN)

        # Subtitle with game count
        count = self.registry.get_game_count()
        subtitle = f"{count} items available"
        subtitle_x = (self.renderer.width - len(subtitle)) // 2
        self.renderer.draw_text(subtitle_x, 2, subtitle, Color.DARK_GRAY)

        # Menu list - left aligned with consistent indentation
        current_y = 4
        selectable_indices = self._get_selectable_items()
        menu_x = 4  # Left margin

        for i, item in enumerate(self.menu_items):
            if current_y >= self.renderer.height - 5:
                break  # Leave room for footer

            if item['type'] == 'category':
                # Category label - dim, no decoration
                if current_y > 4:
                    current_y += 1  # Space before category
                self.renderer.draw_text(menu_x, current_y, item['name'], Color.YELLOW)
                current_y += 1

            elif item['type'] == 'game':
                is_selected = (i == self.selected_index)

                if is_selected:
                    # Highlight selected item
                    indicator = ">"
                    color = Color.BRIGHT_WHITE
                else:
                    indicator = " "
                    color = Color.WHITE

                text = f"  {indicator} {item['title']}"
                self.renderer.draw_text(menu_x, current_y, text, color)
                current_y += 1

        # Footer area - description of selected item
        footer_y = self.renderer.height - 4
        self.renderer.draw_text(0, footer_y, "─" * self.renderer.width, Color.DARK_GRAY)

        # Show selected item description
        selected_item = self.menu_items[self.selected_index]
        if selected_item.get('description'):
            desc = selected_item['description']
            desc_x = (self.renderer.width - len(desc)) // 2
            self.renderer.draw_text(desc_x, footer_y + 1, desc, Color.BRIGHT_CYAN)

        # Controls hint
        controls = "Arrow/WASD: Navigate | Enter/Space: Select | ESC/Q: Exit"
        controls_x = (self.renderer.width - len(controls)) // 2
        self.renderer.draw_text(controls_x, self.renderer.height - 2, controls, Color.DARK_GRAY)

        # Joystick status - bottom right
        joystick_info = self.input_handler.verify_joystick()
        if joystick_info['connected']:
            status = f"Joystick: {joystick_info['name'][:20]}"
            status_color = Color.GREEN
        else:
            status = "Keyboard mode"
            status_color = Color.DARK_GRAY

        status_x = self.renderer.width - len(status) - 2
        self.renderer.draw_text(status_x, self.renderer.height - 1, status, status_color)

        self.renderer.render()

    def handle_input(self, input_type):
        """Handle menu navigation.

        Args:
            input_type: InputType from input handler
        """
        selectable = self._get_selectable_items()

        if input_type == InputType.UP:
            current_pos = selectable.index(self.selected_index) if self.selected_index in selectable else 0
            new_pos = (current_pos - 1) % len(selectable)
            self.selected_index = selectable[new_pos]

        elif input_type == InputType.DOWN:
            current_pos = selectable.index(self.selected_index) if self.selected_index in selectable else 0
            new_pos = (current_pos + 1) % len(selectable)
            self.selected_index = selectable[new_pos]

        elif input_type == InputType.SELECT:
            item = self.menu_items[self.selected_index]
            if item['action']:
                try:
                    self.renderer.exit_fullscreen()
                    item['action']()
                    self.renderer.enter_fullscreen()
                except Exception as e:
                    print(f"Error: {e}")
                    input("Press Enter to continue...")

        elif input_type == InputType.BACK or input_type == InputType.QUIT:
            self.running = False

    def run(self):
        """Main menu loop."""
        try:
            self.renderer.enter_fullscreen()

            # Initialize to first selectable item
            selectable = self._get_selectable_items()
            if selectable:
                self.selected_index = selectable[0]

            while self.running:
                self.draw()
                input_type = self.input_handler.get_input(timeout=0.1)
                self.handle_input(input_type)

        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()
