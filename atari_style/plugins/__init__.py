"""Plugin system for atari-style.

Provides extensibility through user-defined shaders, effects, and connectors.

Plugin Types:
    - shader: GLSL fragment shaders for visual effects
    - composite: Combinations of multiple shaders
    - connector: Export/import format handlers
    - explorer: Parameter space exploration algorithms

Usage:
    from atari_style.plugins import PluginManager

    # Discover and load plugins
    manager = PluginManager()
    manager.discover()

    # List available plugins
    for plugin in manager.list_plugins():
        print(f"{plugin.name} ({plugin.type})")

    # Get a shader plugin
    shader = manager.get_shader('my-custom-effect')
"""

from .schema import PluginManifest, PluginType, PluginParameter
from .loader import PluginManager
from .discovery import discover_plugins, get_plugin_dirs

__all__ = [
    'PluginManifest',
    'PluginType',
    'PluginParameter',
    'PluginManager',
    'discover_plugins',
    'get_plugin_dirs',
]
