"""Game registry system for dynamic game discovery and loading.

Scans game directories for metadata.json files and automatically
registers games for the menu system.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class GameCategory(Enum):
    """Categories for organizing games in the menu."""
    ARCADE_GAME = "🎮 ARCADE GAMES"
    CREATIVE_TOOL = "🎨 CREATIVE TOOLS"
    VISUAL_DEMO = "✨ VISUAL DEMOS"
    UTILITY = "⚙️  UTILITIES"


@dataclass
class GameMetadata:
    """Metadata for a registered game."""
    id: str  # Unique identifier (directory name)
    title: str  # Display name
    category: GameCategory  # Menu category
    description: str  # Short description
    run_function: Optional[Callable] = None  # Function to launch the game
    has_intro: bool = False  # Has intro cutscene
    has_attract_mode: bool = False  # Has attract mode demo
    joystick_support: bool = True  # Supports joystick
    keyboard_support: bool = True  # Supports keyboard
    controls_hint: str = ""  # Custom controls description
    is_new: bool = False  # Mark as new in menu
    version: str = "1.0"  # Game version
    author: str = ""  # Game author
    tags: List[str] = field(default_factory=list)  # Tags for searching


class GameRegistry:
    """Registry for discovering and managing available games."""

    def __init__(self, base_path: Path):
        """Initialize game registry.

        Args:
            base_path: Root path for terminal_arcade package
        """
        self.base_path = base_path
        self.games: Dict[str, GameMetadata] = {}
        self.categories: Dict[GameCategory, List[GameMetadata]] = {
            category: [] for category in GameCategory
        }

    def scan_directory(self, directory: Path, category: GameCategory):
        """Scan a directory for games with metadata.json files.

        Args:
            directory: Directory to scan (e.g., terminal_arcade/games)
            category: Category to assign to discovered games
        """
        if not directory.exists():
            return

        for game_dir in directory.iterdir():
            if not game_dir.is_dir():
                continue

            metadata_file = game_dir / "metadata.json"
            if not metadata_file.exists():
                continue

            try:
                metadata = self._load_metadata(game_dir, metadata_file, category)
                self.register_game(metadata)
            except Exception as e:
                print(f"Failed to load game metadata from {game_dir}: {e}")

    def _load_metadata(self, game_dir: Path, metadata_file: Path,
                       category: GameCategory) -> GameMetadata:
        """Load game metadata from JSON file.

        Args:
            game_dir: Game directory
            metadata_file: Path to metadata.json
            category: Game category

        Returns:
            GameMetadata instance
        """
        with open(metadata_file, 'r') as f:
            data = json.load(f)

        # Try to import the run function
        run_function = None
        if "run_function" in data:
            try:
                # Import the game module dynamically
                module_path = data["run_function"]["module"]
                function_name = data["run_function"]["function"]

                # Dynamic import
                import importlib
                module = importlib.import_module(module_path)
                run_function = getattr(module, function_name)
            except Exception as e:
                print(f"Failed to load run function for {game_dir.name}: {e}")

        return GameMetadata(
            id=game_dir.name,
            title=data.get("title", game_dir.name),
            category=category,
            description=data.get("description", ""),
            run_function=run_function,
            has_intro=data.get("has_intro", False),
            has_attract_mode=data.get("has_attract_mode", False),
            joystick_support=data.get("joystick_support", True),
            keyboard_support=data.get("keyboard_support", True),
            controls_hint=data.get("controls_hint", ""),
            is_new=data.get("is_new", False),
            version=data.get("version", "1.0"),
            author=data.get("author", ""),
            tags=data.get("tags", []),
        )

    def register_game(self, metadata: GameMetadata):
        """Register a game in the registry.

        Args:
            metadata: Game metadata
        """
        self.games[metadata.id] = metadata
        self.categories[metadata.category].append(metadata)

    def register_manual(self, game_id: str, title: str, category: GameCategory,
                       description: str, run_function: Callable, **kwargs):
        """Manually register a game without metadata.json.

        Args:
            game_id: Unique identifier
            title: Display name
            category: Game category
            description: Description
            run_function: Function to launch the game
            **kwargs: Additional metadata fields
        """
        metadata = GameMetadata(
            id=game_id,
            title=title,
            category=category,
            description=description,
            run_function=run_function,
            **kwargs
        )
        self.register_game(metadata)

    def get_game(self, game_id: str) -> Optional[GameMetadata]:
        """Get game metadata by ID.

        Args:
            game_id: Game identifier

        Returns:
            GameMetadata or None if not found
        """
        return self.games.get(game_id)

    def get_games_by_category(self, category: GameCategory) -> List[GameMetadata]:
        """Get all games in a category.

        Args:
            category: Game category

        Returns:
            List of GameMetadata
        """
        return self.categories.get(category, [])

    def get_all_games(self) -> List[GameMetadata]:
        """Get all registered games.

        Returns:
            List of all GameMetadata
        """
        return list(self.games.values())

    def search_games(self, query: str) -> List[GameMetadata]:
        """Search games by title, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching GameMetadata
        """
        query_lower = query.lower()
        results = []

        for game in self.games.values():
            if (query_lower in game.title.lower() or
                query_lower in game.description.lower() or
                any(query_lower in tag.lower() for tag in game.tags)):
                results.append(game)

        return results

    def has_games(self) -> bool:
        """Check if any games are registered.

        Returns:
            True if at least one game is registered
        """
        return len(self.games) > 0

    def get_game_count(self) -> int:
        """Get total number of registered games.

        Returns:
            Number of registered games
        """
        return len(self.games)

    def get_category_counts(self) -> Dict[GameCategory, int]:
        """Get count of games in each category.

        Returns:
            Dictionary mapping categories to counts
        """
        return {
            category: len(games)
            for category, games in self.categories.items()
        }
