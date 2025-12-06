"""Configuration management for atari-style settings.

Provides persistent configuration storage for terminal rendering settings.
Config file is stored at ~/.atari-style/config.json.

Usage:
    from atari_style.core.config import Config

    # Load current config
    config = Config.load()

    # Modify and save
    config.char_aspect = 0.55
    config.save()
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Dict


CONFIG_DIR = Path.home() / '.atari-style'
CONFIG_FILE = CONFIG_DIR / 'config.json'
DEFAULT_CHAR_ASPECT = 0.5  # Width/height ratio (char height is ~2x char width)


@dataclass
class Config:
    """Application configuration settings.

    Attributes:
        char_aspect: Terminal character aspect ratio (width/height).
                    Default is 0.5 meaning chars are ~2x taller than wide.
    """

    char_aspect: float = DEFAULT_CHAR_ASPECT

    @classmethod
    def load(cls) -> 'Config':
        """Load config from file or return defaults.

        Returns:
            Config object with loaded or default values.
        """
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data: Dict[str, Any] = json.load(f)
                # Only use known fields to prevent errors from stale config
                known_fields = {f.name for f in cls.__dataclass_fields__.values()}
                filtered_data = {k: v for k, v in data.items() if k in known_fields}
                # Validate types - char_aspect must be a number
                if 'char_aspect' in filtered_data:
                    if not isinstance(filtered_data['char_aspect'], (int, float)):
                        return cls()  # Return defaults for invalid type
                return cls(**filtered_data)
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()

    def save(self) -> None:
        """Save config to file.

        Creates the config directory if it doesn't exist.
        """
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(asdict(self), f, indent=2)
