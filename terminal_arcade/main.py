"""Terminal Arcade - Main Entry Point.

Launches the splash screen and main menu system.
"""

import sys
from pathlib import Path
from .engine.renderer import Renderer
from .engine.input_handler import InputHandler
from .launcher.splash_screen import SplashScreen
from .launcher.game_registry import GameRegistry, GameCategory
from .launcher.main_menu import EnhancedMenu


def main():
    """Main entry point for Terminal Arcade."""
    # Get base path
    base_path = Path(__file__).parent

    # Initialize input handler to check joystick
    input_handler = InputHandler()
    joystick_detected = input_handler.verify_joystick()['connected']
    input_handler.cleanup()

    # Show splash screen
    renderer = Renderer()
    splash = SplashScreen(renderer)
    splash.show(duration=2.0, joystick_detected=joystick_detected)

    # Initialize game registry
    registry = GameRegistry(base_path)

    # Scan for games in each category
    games_dir = base_path / "games"
    tools_dir = base_path / "tools"
    demos_dir = base_path / "demos"

    # Scan directories
    registry.scan_directory(games_dir, GameCategory.ARCADE_GAME)
    registry.scan_directory(tools_dir, GameCategory.CREATIVE_TOOL)
    registry.scan_directory(demos_dir, GameCategory.VISUAL_DEMO)

    # Check if any games were found
    if not registry.has_games():
        print("No games found! Please check the installation.")
        print(f"Searched in:")
        print(f"  - {games_dir}")
        print(f"  - {tools_dir}")
        print(f"  - {demos_dir}")
        sys.exit(1)

    # Show main menu
    menu = EnhancedMenu(registry)
    menu.run()

    print("\nThanks for playing Terminal Arcade!")
    print("Visit: https://github.com/jcaldwell-labs/terminal-arcade")


if __name__ == '__main__':
    main()
