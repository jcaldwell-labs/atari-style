"""Plugin discovery and directory management.

Scans plugin directories for valid plugins and manages plugin paths.
"""

import os
from pathlib import Path
from typing import List, Iterator, Optional

from .schema import PluginManifest


def get_user_plugin_dir() -> Path:
    """Get the user's plugin directory.

    Returns ~/.atari-style/plugins/, creating it if necessary.
    """
    user_dir = Path.home() / '.atari-style' / 'plugins'
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_builtin_plugin_dir() -> Path:
    """Get the built-in plugins directory.

    Returns atari_style/plugins/builtin/ if it exists.
    """
    builtin_dir = Path(__file__).parent / 'builtin'
    builtin_dir.mkdir(parents=True, exist_ok=True)
    return builtin_dir


def get_plugin_dirs() -> List[Path]:
    """Get all plugin directories to scan.

    Returns list of directories in search order:
    1. Built-in plugins (atari_style/plugins/builtin/)
    2. User plugins (~/.atari-style/plugins/)
    3. Additional paths from ATARI_STYLE_PLUGINS env var
    """
    dirs = []

    # Built-in plugins
    builtin_dir = get_builtin_plugin_dir()
    if builtin_dir.exists():
        dirs.append(builtin_dir)

    # User plugins
    user_dir = get_user_plugin_dir()
    if user_dir.exists():
        dirs.append(user_dir)

    # Additional paths from environment
    env_paths = os.environ.get('ATARI_STYLE_PLUGINS', '')
    if env_paths:
        for path in env_paths.split(':'):
            if path:
                p = Path(path)
                if p.exists() and p.is_dir():
                    dirs.append(p)

    return dirs


def find_plugin_dirs(search_dir: Path) -> Iterator[Path]:
    """Find plugin directories within a search directory.

    A valid plugin directory contains a manifest.json file.

    Args:
        search_dir: Directory to search

    Yields:
        Paths to plugin directories
    """
    if not search_dir.exists():
        return

    for entry in search_dir.iterdir():
        if entry.is_dir():
            manifest_path = entry / 'manifest.json'
            if manifest_path.exists():
                yield entry


def discover_plugins(plugin_dirs: Optional[List[Path]] = None) -> List[PluginManifest]:
    """Discover all available plugins.

    Args:
        plugin_dirs: Directories to search (defaults to get_plugin_dirs())

    Returns:
        List of loaded plugin manifests
    """
    if plugin_dirs is None:
        plugin_dirs = get_plugin_dirs()

    plugins = []
    seen_names = set()

    for search_dir in plugin_dirs:
        for plugin_dir in find_plugin_dirs(search_dir):
            manifest_path = plugin_dir / 'manifest.json'
            try:
                manifest = PluginManifest.from_file(manifest_path)

                # Skip duplicates (first found wins)
                if manifest.name in seen_names:
                    continue

                # Validate
                errors = manifest.validate()
                if errors:
                    print(f"Warning: Plugin '{manifest.name}' has validation errors:")
                    for error in errors:
                        print(f"  - {error}")
                    continue

                plugins.append(manifest)
                seen_names.add(manifest.name)

            except Exception as e:
                print(f"Warning: Failed to load plugin from {plugin_dir}: {e}")

    return plugins


def install_plugin(source: Path, name: Optional[str] = None) -> Path:
    """Install a plugin to the user plugin directory.

    Args:
        source: Source directory containing the plugin
        name: Optional name override (defaults to directory name)

    Returns:
        Path to installed plugin directory

    Raises:
        FileNotFoundError: If source doesn't exist
        ValueError: If plugin is invalid
    """
    import shutil

    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    manifest_path = source / 'manifest.json'
    if not manifest_path.exists():
        raise ValueError(f"No manifest.json found in {source}")

    # Load and validate
    manifest = PluginManifest.from_file(manifest_path)
    errors = manifest.validate()
    if errors:
        raise ValueError(f"Plugin validation failed: {'; '.join(errors)}")

    # Determine target name
    plugin_name = name or manifest.name

    # Install to user directory
    user_dir = get_user_plugin_dir()
    target_dir = user_dir / plugin_name

    # Remove existing if present
    if target_dir.exists():
        shutil.rmtree(target_dir)

    # Copy plugin
    shutil.copytree(source, target_dir)

    return target_dir
