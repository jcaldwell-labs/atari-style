"""Tests for atari_style.core.registry module."""

import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from atari_style.core.registry import (
    CATEGORY_STRING_MAP,
    ContentCategory,
    ContentMetadata,
    ContentRegistry,
    RenderingBackend,
)


class TestContentCategory(unittest.TestCase):
    """Tests for ContentCategory enum."""

    def test_enum_values(self):
        self.assertEqual(ContentCategory.GAME.value, "game")
        self.assertEqual(ContentCategory.VISUALIZER.value, "visualizer")
        self.assertEqual(ContentCategory.TOOL.value, "tool")
        self.assertEqual(ContentCategory.SHADER_DEMO.value, "shader_demo")

    def test_category_string_map_covers_terminal_arcade_strings(self):
        """All known terminal_arcade category strings should map."""
        ta_strings = ["arcade_game", "visual_demo", "creative_tool", "utility"]
        for s in ta_strings:
            self.assertIn(s, CATEGORY_STRING_MAP, f"Missing mapping for '{s}'")

    def test_category_string_map_values_are_valid(self):
        for v in CATEGORY_STRING_MAP.values():
            self.assertIsInstance(v, ContentCategory)


class TestRenderingBackend(unittest.TestCase):
    """Tests for RenderingBackend enum."""

    def test_enum_values(self):
        self.assertEqual(RenderingBackend.TERMINAL.value, "terminal")
        self.assertEqual(RenderingBackend.GL.value, "gl")
        self.assertEqual(RenderingBackend.PLUGIN.value, "plugin")


class TestContentMetadata(unittest.TestCase):
    """Tests for ContentMetadata dataclass."""

    def test_creation_with_required_fields(self):
        m = ContentMetadata(
            id="test", title="Test", category=ContentCategory.GAME,
            description="A test"
        )
        self.assertEqual(m.id, "test")
        self.assertEqual(m.title, "Test")
        self.assertEqual(m.category, ContentCategory.GAME)
        self.assertEqual(m.description, "A test")

    def test_defaults(self):
        m = ContentMetadata(
            id="t", title="T", category=ContentCategory.TOOL, description=""
        )
        self.assertIsNone(m.run_module)
        self.assertIsNone(m.run_function_name)
        self.assertIsNone(m._resolved_callable)
        self.assertEqual(m.backend, RenderingBackend.TERMINAL)
        self.assertTrue(m.joystick_support)
        self.assertTrue(m.keyboard_support)
        self.assertEqual(m.tags, [])
        self.assertEqual(m.version, "1.0")

    def test_run_function_returns_none_without_module(self):
        m = ContentMetadata(
            id="t", title="T", category=ContentCategory.GAME, description=""
        )
        self.assertIsNone(m.run_function)

    @patch("atari_style.core.registry.importlib.import_module")
    def test_lazy_resolution(self, mock_import):
        """run_function should import on first access and cache."""
        fake_fn = MagicMock()
        fake_module = MagicMock()
        fake_module.my_func = fake_fn
        mock_import.return_value = fake_module

        m = ContentMetadata(
            id="t", title="T", category=ContentCategory.GAME,
            description="", run_module="some.module",
            run_function_name="my_func",
        )

        # First access triggers import
        result = m.run_function
        self.assertIs(result, fake_fn)
        mock_import.assert_called_once_with("some.module")

        # Second access uses cache (no additional import call)
        result2 = m.run_function
        self.assertIs(result2, fake_fn)
        mock_import.assert_called_once()  # still only one call

    @patch("atari_style.core.registry.importlib.import_module")
    def test_lazy_resolution_import_error(self, mock_import):
        """Failed imports should return None and log warning."""
        mock_import.side_effect = ImportError("no such module")

        m = ContentMetadata(
            id="t", title="T", category=ContentCategory.GAME,
            description="", run_module="bad.module",
            run_function_name="fn",
        )

        with self.assertLogs("atari_style.core.registry", level="WARNING"):
            result = m.run_function

        self.assertIsNone(result)

    @patch("atari_style.core.registry.importlib.import_module")
    def test_lazy_resolution_attribute_error(self, mock_import):
        """Missing function name on module should return None and warn."""
        fake_module = MagicMock(spec=[])  # no attributes
        mock_import.return_value = fake_module

        m = ContentMetadata(
            id="t", title="T", category=ContentCategory.GAME,
            description="", run_module="good.module",
            run_function_name="nonexistent_func",
        )

        with self.assertLogs("atari_style.core.registry", level="WARNING"):
            result = m.run_function

        self.assertIsNone(result)

    def test_preresolved_callable(self):
        """If _resolved_callable is set, run_function returns it directly."""
        fn = lambda: None
        m = ContentMetadata(
            id="t", title="T", category=ContentCategory.GAME,
            description="", _resolved_callable=fn,
        )
        self.assertIs(m.run_function, fn)


class TestContentRegistry(unittest.TestCase):
    """Tests for ContentRegistry basic operations."""

    def test_empty_registry(self):
        reg = ContentRegistry()
        self.assertEqual(reg.count(), 0)
        self.assertIsNone(reg.get("anything"))
        self.assertEqual(reg.get_all(), [])

    def test_register_and_get(self):
        reg = ContentRegistry()
        m = ContentMetadata(
            id="pacman", title="Pac-Man", category=ContentCategory.GAME,
            description="Maze game"
        )
        reg.register_metadata(m)
        self.assertEqual(reg.count(), 1)
        self.assertIs(reg.get("pacman"), m)

    def test_duplicate_overwrites(self):
        reg = ContentRegistry()
        m1 = ContentMetadata(
            id="game1", title="V1", category=ContentCategory.GAME,
            description="First"
        )
        m2 = ContentMetadata(
            id="game1", title="V2", category=ContentCategory.GAME,
            description="Second"
        )
        reg.register_metadata(m1)
        reg.register_metadata(m2)
        self.assertEqual(reg.count(), 1)
        self.assertEqual(reg.get("game1").title, "V2")
        # Category list should also have exactly one entry
        self.assertEqual(len(reg.get_by_category(ContentCategory.GAME)), 1)

    def test_duplicate_overwrite_different_category(self):
        """Overwriting with a different category should move the entry."""
        reg = ContentRegistry()
        m1 = ContentMetadata(
            id="x", title="X", category=ContentCategory.GAME, description=""
        )
        m2 = ContentMetadata(
            id="x", title="X", category=ContentCategory.TOOL, description=""
        )
        reg.register_metadata(m1)
        reg.register_metadata(m2)
        self.assertEqual(len(reg.get_by_category(ContentCategory.GAME)), 0)
        self.assertEqual(len(reg.get_by_category(ContentCategory.TOOL)), 1)

    def test_get_by_category(self):
        reg = ContentRegistry()
        game = ContentMetadata(
            id="g", title="G", category=ContentCategory.GAME, description=""
        )
        tool = ContentMetadata(
            id="t", title="T", category=ContentCategory.TOOL, description=""
        )
        reg.register_metadata(game)
        reg.register_metadata(tool)
        self.assertEqual(len(reg.get_by_category(ContentCategory.GAME)), 1)
        self.assertEqual(len(reg.get_by_category(ContentCategory.TOOL)), 1)
        self.assertEqual(len(reg.get_by_category(ContentCategory.VISUALIZER)), 0)

    def test_category_counts(self):
        reg = ContentRegistry()
        for i in range(3):
            reg.register_metadata(ContentMetadata(
                id=f"g{i}", title=f"G{i}", category=ContentCategory.GAME,
                description=""
            ))
        reg.register_metadata(ContentMetadata(
            id="t1", title="T1", category=ContentCategory.TOOL, description=""
        ))
        counts = reg.category_counts()
        self.assertEqual(counts[ContentCategory.GAME], 3)
        self.assertEqual(counts[ContentCategory.TOOL], 1)
        self.assertEqual(counts[ContentCategory.VISUALIZER], 0)

    def test_register_callable(self):
        reg = ContentRegistry()
        fn = lambda: "hello"
        m = reg.register_callable(
            "demo", "Demo", ContentCategory.VISUALIZER, "A demo", fn,
            tags=["test"],
        )
        self.assertEqual(reg.count(), 1)
        self.assertIs(m.run_function, fn)
        self.assertEqual(m.tags, ["test"])


class TestScanDirectory(unittest.TestCase):
    """Tests for ContentRegistry.scan_directory()."""

    def _write_metadata(self, game_dir: Path, data: dict) -> None:
        game_dir.mkdir(parents=True, exist_ok=True)
        (game_dir / "metadata.json").write_text(json.dumps(data))

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = ContentRegistry()
            count = reg.scan_directory(Path(tmpdir))
            self.assertEqual(count, 0)
            self.assertEqual(reg.count(), 0)

    def test_nonexistent_directory(self):
        reg = ContentRegistry()
        with self.assertLogs("atari_style.core.registry", level="WARNING"):
            count = reg.scan_directory(Path("/nonexistent/path/12345"))
        self.assertEqual(count, 0)

    def test_valid_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_metadata(Path(tmpdir) / "mygame", {
                "title": "My Game",
                "description": "Fun game",
                "category": "arcade_game",
                "tags": ["fun"],
                "run_function": {
                    "module": "some.module",
                    "function": "run_game"
                }
            })
            reg = ContentRegistry()
            count = reg.scan_directory(Path(tmpdir))
            self.assertEqual(count, 1)
            m = reg.get("mygame")
            self.assertIsNotNone(m)
            self.assertEqual(m.title, "My Game")
            self.assertEqual(m.category, ContentCategory.GAME)
            self.assertEqual(m.run_module, "some.module")
            self.assertEqual(m.run_function_name, "run_game")
            self.assertEqual(m.tags, ["fun"])

    def test_skips_files_not_dirs(self):
        """Files in the scan directory should be ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "readme.txt").write_text("hello")
            reg = ContentRegistry()
            count = reg.scan_directory(Path(tmpdir))
            self.assertEqual(count, 0)

    def test_skips_dirs_without_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "no_meta").mkdir()
            reg = ContentRegistry()
            count = reg.scan_directory(Path(tmpdir))
            self.assertEqual(count, 0)

    def test_non_dict_run_function(self):
        """A string run_function value should result in None module/name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_metadata(Path(tmpdir) / "oddgame", {
                "title": "Odd", "description": "d",
                "run_function": "some.module.run_game"
            })
            reg = ContentRegistry()
            reg.scan_directory(Path(tmpdir))
            m = reg.get("oddgame")
            self.assertIsNone(m.run_module)
            self.assertIsNone(m.run_function_name)

    def test_malformed_json_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            game_dir = Path(tmpdir) / "bad"
            game_dir.mkdir()
            (game_dir / "metadata.json").write_text("{invalid json")

            reg = ContentRegistry()
            with self.assertLogs("atari_style.core.registry", level="WARNING"):
                count = reg.scan_directory(Path(tmpdir))
            self.assertEqual(count, 0)

    def test_single_read_per_file(self):
        """JSON should be read once per directory, not re-read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_metadata(Path(tmpdir) / "g1", {
                "title": "G1", "description": "d", "category": "game"
            })

            reg = ContentRegistry()
            with patch("builtins.open", wraps=open) as mock_open:
                reg.scan_directory(Path(tmpdir))
                # open should be called exactly once for the one metadata file
                json_opens = [
                    c for c in mock_open.call_args_list
                    if "metadata.json" in str(c)
                ]
                self.assertEqual(len(json_opens), 1)

    @patch("atari_style.core.registry.importlib.import_module")
    def test_lazy_resolution_not_triggered_during_scan(self, mock_import):
        """Scanning should NOT trigger any module imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_metadata(Path(tmpdir) / "g1", {
                "title": "G1", "description": "d",
                "run_function": {"module": "foo.bar", "function": "run"}
            })
            reg = ContentRegistry()
            reg.scan_directory(Path(tmpdir))
            mock_import.assert_not_called()

    def test_default_category_applied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_metadata(Path(tmpdir) / "viz", {
                "title": "Viz", "description": "d"
                # no "category" key
            })
            reg = ContentRegistry()
            reg.scan_directory(Path(tmpdir), ContentCategory.VISUALIZER)
            m = reg.get("viz")
            self.assertEqual(m.category, ContentCategory.VISUALIZER)


class TestSearch(unittest.TestCase):
    """Tests for ContentRegistry.search()."""

    def setUp(self):
        self.reg = ContentRegistry()
        self.reg.register_metadata(ContentMetadata(
            id="pacman", title="Pac-Man", category=ContentCategory.GAME,
            description="Classic maze chase", tags=["arcade", "maze"]
        ))
        self.reg.register_metadata(ContentMetadata(
            id="painter", title="ASCII Painter", category=ContentCategory.TOOL,
            description="Drawing tool", tags=["creative", "art"]
        ))

    def test_search_by_title(self):
        results = self.reg.search("pac")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "pacman")

    def test_search_by_description(self):
        results = self.reg.search("drawing")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "painter")

    def test_search_by_tag(self):
        results = self.reg.search("maze")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "pacman")

    def test_search_case_insensitive(self):
        results = self.reg.search("PAC-MAN")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        results = self.reg.search("nonexistent")
        self.assertEqual(len(results), 0)


class TestPluginBridge(unittest.TestCase):
    """Tests for plugin bridging."""

    def test_bridge_plugin(self):
        manifest = MagicMock()
        manifest.name = "cool-shader"
        manifest.description = "A cool shader"
        manifest.version = "2.0"
        manifest.author = "dev"
        manifest.plugin_dir = Path("/plugins/cool-shader")

        reg = ContentRegistry()
        m = reg.bridge_plugin(manifest)

        self.assertEqual(m.id, "plugin-cool-shader")
        self.assertEqual(m.title, "Cool Shader")
        self.assertEqual(m.category, ContentCategory.SHADER_DEMO)
        self.assertEqual(m.backend, RenderingBackend.PLUGIN)
        self.assertEqual(reg.count(), 1)

    def test_bridge_all_plugins(self):
        pm = MagicMock()
        m1 = MagicMock()
        m1.name = "shader-a"
        m1.description = ""
        m1.version = "1.0"
        m1.author = ""
        m1.plugin_dir = None
        m2 = MagicMock()
        m2.name = "shader-b"
        m2.description = ""
        m2.version = "1.0"
        m2.author = ""
        m2.plugin_dir = None
        pm.plugins = {"a": m1, "b": m2}

        reg = ContentRegistry()
        count = reg.bridge_all_plugins(pm)
        self.assertEqual(count, 2)
        self.assertEqual(reg.count(), 2)


class TestRegistrationSafety(unittest.TestCase):
    """Tests for expected_minimum threshold and check_minimum()."""

    def test_no_warning_above_threshold(self):
        reg = ContentRegistry(expected_minimum=2)
        reg.register_metadata(ContentMetadata(
            id="a", title="A", category=ContentCategory.GAME, description=""
        ))
        reg.register_metadata(ContentMetadata(
            id="b", title="B", category=ContentCategory.GAME, description=""
        ))
        # Should not log any warning
        with self.assertRaises(AssertionError):
            # assertLogs will raise if no logs are emitted — that's what we want
            with self.assertLogs("atari_style.core.registry", level="WARNING"):
                reg.check_minimum()

    def test_warning_below_threshold(self):
        reg = ContentRegistry(expected_minimum=5)
        reg.register_metadata(ContentMetadata(
            id="a", title="A", category=ContentCategory.GAME, description=""
        ))
        with self.assertLogs("atari_style.core.registry", level="WARNING") as cm:
            reg.check_minimum()
        self.assertIn("1 items", cm.output[0])
        self.assertIn("5", cm.output[0])

    def test_zero_threshold_no_warning(self):
        reg = ContentRegistry(expected_minimum=0)
        # Should not warn even with 0 items
        with self.assertRaises(AssertionError):
            with self.assertLogs("atari_style.core.registry", level="WARNING"):
                reg.check_minimum()

    def test_scan_triggers_check(self):
        """scan_directory should call check_minimum after scanning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = ContentRegistry(expected_minimum=10)
            with self.assertLogs("atari_style.core.registry", level="WARNING"):
                reg.scan_directory(Path(tmpdir))


if __name__ == "__main__":
    unittest.main()
