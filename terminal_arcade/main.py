"""Terminal Arcade - Main Entry Point.

Launches the main menu system for games, tools, and demos.
"""

import sys
from pathlib import Path
from .launcher.game_registry import GameRegistry, GameCategory
from .launcher.main_menu import EnhancedMenu


def main():
    """Main entry point for Terminal Arcade."""
    base_path = Path(__file__).parent

    # Initialize game registry
    registry = GameRegistry(base_path)

    # Scan for games in each category
    games_dir = base_path / "games"
    tools_dir = base_path / "tools"
    demos_dir = base_path / "demos"

    registry.scan_directory(games_dir, GameCategory.ARCADE_GAME)
    registry.scan_directory(tools_dir, GameCategory.CREATIVE_TOOL)
    registry.scan_directory(demos_dir, GameCategory.VISUAL_DEMO)

    if not registry.has_games():
        print("No games found! Check installation.")
        print(f"Searched: {games_dir}, {tools_dir}, {demos_dir}")
        sys.exit(1)

    # Run menu
    menu = EnhancedMenu(registry)
    menu.run()

    print("\nThanks for playing!")


if __name__ == '__main__':
    main()
