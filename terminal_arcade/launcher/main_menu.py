"""Enhanced main menu system with game registry and sections.

Provides organized navigation through games, tools, and demos with
visual indicators and section headers.
"""

import sys
from pathlib import Path
from ..engine.renderer import Renderer, Color
from ..engine.input_handler import InputHandler, InputType
from ..engine.menu import Menu, MenuItem
from ..engine.branding import Brand
from .game_registry import GameRegistry, GameCategory


class EnhancedMenu:
    """Enhanced menu with section headers and game registry integration."""

    def __init__(self, registry: GameRegistry):
        """Initialize enhanced menu.

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

        # Add section headers and games for each category
        for category in GameCategory:
            games = self.registry.get_games_by_category(category)
            if not games:
                continue

            # Section header (non-selectable)
            header_lines = Brand.get_section_header(category.value)
            items.append({
                'type': 'header',
                'lines': header_lines,
            })

            # Games in this category
            for game in games:
                indicator = "⭐" if game.is_new else ("🎮" if game.joystick_support else "⌨️ ")
                title = f"{indicator} {game.title}"

                items.append({
                    'type': 'game',
                    'title': title,
                    'description': game.description,
                    'action': game.run_function,
                    'metadata': game,
                })

        # Add exit option
        items.append({
            'type': 'header',
            'lines': Brand.get_section_header("SYSTEM"),
        })
        items.append({
            'type': 'game',
            'title': "❌ Exit",
            'description': "Exit Terminal Arcade",
            'action': self._exit_menu,
            'metadata': None,
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

        # Draw title
        Brand.draw_logo_compact(self.renderer, y=2)

        # Draw subtitle
        subtitle = f"Terminal Arcade v2.0 - {self.registry.get_game_count()} Games Available"
        subtitle_x = (self.renderer.width - len(subtitle)) // 2
        self.renderer.draw_text(subtitle_x, 6, subtitle, Color.DARK_GRAY)

        # Draw menu items
        current_y = 9
        selectable_indices = self._get_selectable_items()
        selectable_position = selectable_indices.index(self.selected_index) if self.selected_index in selectable_indices else 0

        for i, item in enumerate(self.menu_items):
            if item['type'] == 'header':
                # Draw section header
                if current_y > 9:  # Add spacing before headers (except first)
                    current_y += 1

                for line in item['lines']:
                    x = (self.renderer.width - len(line)) // 2
                    self.renderer.draw_text(x, current_y, line, Color.BRIGHT_YELLOW)
                    current_y += 1

                current_y += 1  # Spacing after header

            elif item['type'] == 'game':
                # Determine if this item is selected
                is_selected = (i == self.selected_index)

                # Draw selection indicator
                if is_selected:
                    indicator = "►"
                    title_color = Color.BRIGHT_WHITE
                    desc_color = Color.BRIGHT_CYAN
                else:
                    indicator = " "
                    title_color = Color.WHITE
                    desc_color = Color.DARK_GRAY

                # Draw title
                title_text = f"{indicator} {item['title']}"
                title_x = (self.renderer.width - len(title_text)) // 2
                self.renderer.draw_text(title_x, current_y, title_text, title_color)

                # Draw description (only for selected item)
                if is_selected and item['description']:
                    desc_x = (self.renderer.width - len(item['description'])) // 2
                    self.renderer.draw_text(desc_x, current_y + 1, item['description'], desc_color)
                    current_y += 1

                current_y += 1

        # Draw controls help at bottom
        Brand.draw_controls_help(self.renderer)

        # Draw joystick status
        joystick_info = self.input_handler.verify_joystick()
        if joystick_info['connected']:
            status = f"🎮 {joystick_info['name']}"
            status_color = Color.BRIGHT_GREEN
        else:
            status = "⌨️  Keyboard Mode"
            status_color = Color.YELLOW

        status_x = self.renderer.width - len(status) - 2
        self.renderer.draw_text(status_x, 1, status, status_color)

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
            # Execute selected action
            item = self.menu_items[self.selected_index]
            if item['action']:
                try:
                    # Exit fullscreen for game
                    self.renderer.exit_fullscreen()

                    # Run the game
                    item['action']()

                    # Re-enter fullscreen for menu
                    self.renderer.enter_fullscreen()
                except Exception as e:
                    print(f"Error running {item['title']}: {e}")
                    input("Press Enter to continue...")

        elif input_type == InputType.BACK or input_type == InputType.QUIT:
            self.running = False

    def run(self):
        """Main menu loop."""
        try:
            self.renderer.enter_fullscreen()

            # Initialize selected to first selectable item
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
