"""Plugin loader and manager.

Handles loading, registration, and access to plugins.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .schema import PluginManifest, PluginType
from .discovery import discover_plugins, get_plugin_dirs


class PluginManager:
    """Manages plugin discovery, loading, and access.

    The PluginManager maintains a registry of all available plugins
    and provides access to them by name or type.

    Usage:
        manager = PluginManager()
        manager.discover()

        # List all plugins
        for plugin in manager.list_plugins():
            print(plugin.name)

        # Get a specific shader
        shader = manager.get_shader('my-effect')
        if shader:
            print(f"Shader path: {shader.shader_path}")
    """

    def __init__(self):
        """Initialize the plugin manager."""
        self._plugins: Dict[str, PluginManifest] = {}
        self._loaded = False

    def discover(self, plugin_dirs: Optional[List[Path]] = None) -> int:
        """Discover and load all available plugins.

        Args:
            plugin_dirs: Directories to search (defaults to standard paths)

        Returns:
            Number of plugins loaded
        """
        if plugin_dirs is None:
            plugin_dirs = get_plugin_dirs()

        plugins = discover_plugins(plugin_dirs)

        for manifest in plugins:
            self._plugins[manifest.name] = manifest

        self._loaded = True
        return len(self._plugins)

    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        auto_discover: bool = True
    ) -> List[PluginManifest]:
        """List all loaded plugins.

        Args:
            plugin_type: Filter by type (None for all)
            auto_discover: If True, auto-discover plugins if not loaded (default True)

        Returns:
            List of plugin manifests
        """
        if auto_discover and not self._loaded:
            self.discover()

        if plugin_type is None:
            return list(self._plugins.values())

        return [p for p in self._plugins.values() if p.type == plugin_type]

    def get_plugin(self, name: str) -> Optional[PluginManifest]:
        """Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin manifest or None if not found
        """
        if not self._loaded:
            self.discover()

        return self._plugins.get(name)

    def get_shader(self, name: str) -> Optional[PluginManifest]:
        """Get a shader plugin by name.

        Args:
            name: Plugin name

        Returns:
            Shader plugin manifest or None
        """
        plugin = self.get_plugin(name)
        if plugin and plugin.type == PluginType.SHADER:
            return plugin
        return None

    def get_composite(self, name: str) -> Optional[PluginManifest]:
        """Get a composite plugin by name.

        Args:
            name: Plugin name

        Returns:
            Composite plugin manifest or None
        """
        plugin = self.get_plugin(name)
        if plugin and plugin.type == PluginType.COMPOSITE:
            return plugin
        return None

    def register_plugin(self, manifest: PluginManifest, warn_overwrite: bool = True) -> None:
        """Manually register a plugin.

        Args:
            manifest: Plugin manifest to register
            warn_overwrite: If True, log a warning when overwriting an existing plugin
        """
        import logging
        logger = logging.getLogger(__name__)

        errors = manifest.validate()
        if errors:
            raise ValueError(f"Invalid plugin: {'; '.join(errors)}")

        if warn_overwrite and manifest.name in self._plugins:
            logger.warning(f"Overwriting existing plugin: {manifest.name}")

        self._plugins[manifest.name] = manifest

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin by name.

        Args:
            name: Plugin name

        Returns:
            True if removed, False if not found
        """
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False

    def to_composite_configs(self) -> Dict:
        """Convert shader plugins to CompositeConfig format.

        Returns a dictionary compatible with the COMPOSITES registry
        in atari_style.core.gl.composites.

        Returns:
            Dict mapping plugin names to CompositeConfig instances
        """
        from ..core.gl.composites import CompositeConfig

        configs = {}

        for plugin in self.list_plugins(PluginType.SHADER):
            if plugin.shader_path and plugin.shader_path.exists():
                config = CompositeConfig(
                    name=plugin.name,  # Use original plugin name for consistency
                    shader_path=str(plugin.shader_path),
                    description=plugin.description,
                    default_params=plugin.default_params,
                    param_names=plugin.param_names,
                    param_ranges=plugin.param_ranges,
                    recommended_duration=plugin.recommended_duration,
                    default_color_mode=plugin.default_color_mode
                )
                configs[plugin.name] = config

        return configs

    @property
    def plugin_count(self) -> int:
        """Number of loaded plugins."""
        return len(self._plugins)

    @property
    def shader_count(self) -> int:
        """Number of shader plugins."""
        return len(self.list_plugins(PluginType.SHADER))


# Global plugin manager instance (singleton)
_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance.

    This function returns a singleton PluginManager instance.
    On first call, it creates the manager and discovers plugins.
    The instance persists for the lifetime of the process.

    Use `reset_plugin_manager()` to clear the singleton for test isolation
    or to reload plugins after installation.

    Returns:
        The global PluginManager instance
    """
    global _manager
    if _manager is None:
        _manager = PluginManager()
        _manager.discover()
    return _manager


def reset_plugin_manager() -> None:
    """Reset the global plugin manager instance.

    This clears the singleton, so the next call to `get_plugin_manager()`
    will create a new instance and re-discover plugins.

    Useful for:
    - Test isolation (each test gets a fresh manager)
    - Reloading plugins after installation
    - Clearing cached plugin state
    """
    global _manager
    _manager = None
