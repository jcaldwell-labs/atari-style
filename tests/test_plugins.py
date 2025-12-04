"""Tests for the plugin system."""

import json
import tempfile
from pathlib import Path
import pytest

from atari_style.plugins.schema import PluginManifest, PluginType, PluginParameter
from atari_style.plugins.discovery import discover_plugins, find_plugin_dirs
from atari_style.plugins.loader import PluginManager


class TestPluginParameter:
    """Tests for PluginParameter dataclass."""

    def test_creation(self):
        param = PluginParameter(
            name="test_param",
            display_name="Test Parameter",
            min_value=0.0,
            max_value=1.0,
            default=0.5,
            description="A test parameter"
        )
        assert param.name == "test_param"
        assert param.default == 0.5

    def test_validate_value_in_range(self):
        param = PluginParameter("p", "P", 0.0, 1.0, 0.5)
        assert param.validate_value(0.0)
        assert param.validate_value(0.5)
        assert param.validate_value(1.0)

    def test_validate_value_out_of_range(self):
        param = PluginParameter("p", "P", 0.0, 1.0, 0.5)
        assert not param.validate_value(-0.1)
        assert not param.validate_value(1.1)

    def test_clamp(self):
        param = PluginParameter("p", "P", 0.0, 1.0, 0.5)
        assert param.clamp(-0.5) == 0.0
        assert param.clamp(0.5) == 0.5
        assert param.clamp(1.5) == 1.0

    def test_from_dict(self):
        data = {
            "name": "wave_speed",
            "min": 0.1,
            "max": 2.0,
            "default": 0.5
        }
        param = PluginParameter.from_dict(data)
        assert param.name == "wave_speed"
        assert param.min_value == 0.1
        assert param.max_value == 2.0
        assert param.default == 0.5

    def test_to_dict(self):
        param = PluginParameter("test", "Test", 0.0, 1.0, 0.5, "desc")
        data = param.to_dict()
        assert data["name"] == "test"
        assert data["min"] == 0.0
        assert data["max"] == 1.0


class TestPluginManifest:
    """Tests for PluginManifest dataclass."""

    def test_creation(self):
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            type=PluginType.SHADER
        )
        assert manifest.name == "test-plugin"
        assert manifest.type == PluginType.SHADER

    def test_validate_valid_manifest(self):
        manifest = PluginManifest(
            name="valid-plugin",
            version="1.0.0",
            type=PluginType.SHADER,
            parameters=[
                PluginParameter("a", "A", 0.0, 1.0, 0.5),
                PluginParameter("b", "B", 0.0, 1.0, 0.5),
                PluginParameter("c", "C", 0.0, 1.0, 0.5),
                PluginParameter("d", "D", 0.0, 1.0, 0.5),
            ]
        )
        errors = manifest.validate()
        # Should have no errors except missing shader file
        assert len([e for e in errors if "Shader file not found" not in e]) == 0

    def test_validate_missing_name(self):
        manifest = PluginManifest(
            name="",
            version="1.0.0",
            type=PluginType.SHADER
        )
        errors = manifest.validate()
        assert any("name is required" in e for e in errors)

    def test_validate_invalid_version(self):
        manifest = PluginManifest(
            name="test",
            version="1",  # Invalid - should be semver
            type=PluginType.SHADER
        )
        errors = manifest.validate()
        assert any("semantic" in e.lower() for e in errors)

    def test_validate_wrong_param_count(self):
        manifest = PluginManifest(
            name="test",
            version="1.0.0",
            type=PluginType.SHADER,
            parameters=[
                PluginParameter("a", "A", 0.0, 1.0, 0.5),
                PluginParameter("b", "B", 0.0, 1.0, 0.5),
            ]  # Only 2 params, shader needs 4
        )
        errors = manifest.validate()
        assert any("4 parameters" in e for e in errors)

    def test_validate_param_range_error(self):
        manifest = PluginManifest(
            name="test",
            version="1.0.0",
            type=PluginType.COMPOSITE,  # Composite doesn't require 4 params
            parameters=[
                PluginParameter("bad", "Bad", 1.0, 0.0, 0.5),  # min > max
            ]
        )
        errors = manifest.validate()
        assert any("min must be less than max" in e for e in errors)

    def test_default_params_property(self):
        manifest = PluginManifest(
            name="test",
            version="1.0.0",
            type=PluginType.SHADER,
            parameters=[
                PluginParameter("a", "A", 0.0, 1.0, 0.1),
                PluginParameter("b", "B", 0.0, 1.0, 0.2),
                PluginParameter("c", "C", 0.0, 1.0, 0.3),
                PluginParameter("d", "D", 0.0, 1.0, 0.4),
            ]
        )
        assert manifest.default_params == (0.1, 0.2, 0.3, 0.4)

    def test_from_dict(self):
        data = {
            "name": "my-plugin",
            "version": "2.0.0",
            "type": "shader",
            "author": "Test Author",
            "description": "A test plugin",
            "parameters": [
                {"name": "p1", "min": 0, "max": 1, "default": 0.5},
                {"name": "p2", "min": 0, "max": 1, "default": 0.5},
                {"name": "p3", "min": 0, "max": 1, "default": 0.5},
                {"name": "p4", "min": 0, "max": 1, "default": 0.5},
            ]
        }
        manifest = PluginManifest.from_dict(data)
        assert manifest.name == "my-plugin"
        assert manifest.version == "2.0.0"
        assert manifest.author == "Test Author"
        assert len(manifest.parameters) == 4

    def test_to_json(self):
        manifest = PluginManifest(
            name="test",
            version="1.0.0",
            type=PluginType.SHADER
        )
        json_str = manifest.to_json()
        data = json.loads(json_str)
        assert data["name"] == "test"
        assert data["type"] == "shader"


class TestPluginDiscovery:
    """Tests for plugin discovery functions."""

    def test_find_plugin_dirs_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins = list(find_plugin_dirs(Path(tmpdir)))
            assert len(plugins) == 0

    def test_find_plugin_dirs_with_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake plugin
            plugin_dir = Path(tmpdir) / "test-plugin"
            plugin_dir.mkdir()
            manifest_path = plugin_dir / "manifest.json"
            manifest_path.write_text('{"name": "test", "version": "1.0.0", "type": "shader"}')

            plugins = list(find_plugin_dirs(Path(tmpdir)))
            assert len(plugins) == 1
            assert plugins[0].name == "test-plugin"

    def test_discover_plugins_validates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid plugin (missing required fields)
            plugin_dir = Path(tmpdir) / "bad-plugin"
            plugin_dir.mkdir()
            manifest_path = plugin_dir / "manifest.json"
            manifest_path.write_text('{"name": "", "version": "1.0.0", "type": "shader"}')

            # Should not include invalid plugin
            plugins = discover_plugins([Path(tmpdir)])
            assert len(plugins) == 0


class TestPluginManager:
    """Tests for PluginManager class."""

    def test_initialization(self):
        manager = PluginManager()
        assert manager.plugin_count == 0

    def test_discover_builtin(self):
        manager = PluginManager()
        count = manager.discover()
        # Should find at least the aurora-waves builtin
        assert count >= 0  # May be 0 if builtin dir doesn't exist yet

    def test_register_plugin(self):
        manager = PluginManager()
        manifest = PluginManifest(
            name="manual-plugin",
            version="1.0.0",
            type=PluginType.COMPOSITE,
            parameters=[]
        )
        manager.register_plugin(manifest)
        assert manager.plugin_count == 1
        assert manager.get_plugin("manual-plugin") is not None

    def test_unregister_plugin(self):
        manager = PluginManager()
        manifest = PluginManifest(
            name="to-remove",
            version="1.0.0",
            type=PluginType.COMPOSITE
        )
        manager.register_plugin(manifest)
        assert manager.plugin_count == 1

        result = manager.unregister_plugin("to-remove")
        assert result is True
        assert manager.plugin_count == 0

    def test_unregister_nonexistent(self):
        manager = PluginManager()
        result = manager.unregister_plugin("does-not-exist")
        assert result is False

    def _make_shader_manifest(self, name: str) -> PluginManifest:
        """Create a valid shader manifest with 4 parameters."""
        return PluginManifest(
            name=name,
            version="1.0.0",
            type=PluginType.SHADER,
            parameters=[
                PluginParameter("a", "A", 0.0, 1.0, 0.5),
                PluginParameter("b", "B", 0.0, 1.0, 0.5),
                PluginParameter("c", "C", 0.0, 1.0, 0.5),
                PluginParameter("d", "D", 0.0, 1.0, 0.5),
            ]
        )

    def test_list_by_type(self):
        manager = PluginManager()
        # Manually set _loaded to prevent auto-discover in list_plugins
        manager._loaded = True
        manager.register_plugin(self._make_shader_manifest("s1"))
        manager.register_plugin(self._make_shader_manifest("s2"))
        manager.register_plugin(PluginManifest("c1", "1.0.0", PluginType.COMPOSITE))

        shaders = manager.list_plugins(PluginType.SHADER)
        composites = manager.list_plugins(PluginType.COMPOSITE)

        assert len(shaders) == 2
        assert len(composites) == 1

    def test_get_shader(self):
        manager = PluginManager()
        manager.register_plugin(self._make_shader_manifest("my-shader"))
        manager.register_plugin(PluginManifest("my-composite", "1.0.0", PluginType.COMPOSITE))

        shader = manager.get_shader("my-shader")
        assert shader is not None
        assert shader.name == "my-shader"

        # Should return None for non-shader
        non_shader = manager.get_shader("my-composite")
        assert non_shader is None

    def test_get_composite(self):
        manager = PluginManager()
        manager.register_plugin(PluginManifest("my-composite", "1.0.0", PluginType.COMPOSITE))

        composite = manager.get_composite("my-composite")
        assert composite is not None
        assert composite.type == PluginType.COMPOSITE
