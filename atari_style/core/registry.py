"""Content registry for unified discovery and loading of games, tools, and demos.

Provides a single registry that can discover content from metadata.json files
(auto-discovery), accept direct callable registration (for hardcoded entries),
and bridge plugin manifests into the same content model.

Key design decisions:
- Lazy resolution: module imports happen on first access, not at scan time
- Single-read: JSON files are read once and parsed in memory
- Non-fatal safety: minimum count checks log warnings, never raise
"""

import importlib
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """Categories for organizing content in the menu."""
    GAME = "game"
    VISUALIZER = "visualizer"
    TOOL = "tool"
    SHADER_DEMO = "shader_demo"


# Map terminal_arcade metadata.json category strings to ContentCategory
CATEGORY_STRING_MAP: Dict[str, ContentCategory] = {
    "arcade_game": ContentCategory.GAME,
    "game": ContentCategory.GAME,
    "visual_demo": ContentCategory.VISUALIZER,
    "visualizer": ContentCategory.VISUALIZER,
    "creative_tool": ContentCategory.TOOL,
    "tool": ContentCategory.TOOL,
    "shader_demo": ContentCategory.SHADER_DEMO,
    "shader": ContentCategory.SHADER_DEMO,
    "utility": ContentCategory.TOOL,
}


class RenderingBackend(Enum):
    """Rendering backend used by content."""
    TERMINAL = "terminal"
    GL = "gl"
    PLUGIN = "plugin"


@dataclass
class ContentMetadata:
    """Metadata for a registered piece of content.

    Attributes:
        id: Unique identifier (typically directory name or kebab-case slug)
        title: Human-readable display name
        category: Content category for menu organization
        description: Short description shown in menu/search
        run_module: Dotted module path for lazy import (e.g. 'atari_style.demos.pacman')
        run_function_name: Function name within the module (e.g. 'run_pacman')
        backend: Rendering backend
        joystick_support: Whether joystick input is supported
        keyboard_support: Whether keyboard input is supported
        controls_hint: Short controls description
        has_intro: Whether content has an intro sequence
        is_new: Flag for highlighting new content in menus
        tags: Searchable tags
        version: Content version string
        author: Content author
        source_path: Filesystem path to the content's source directory
    """
    # Required
    id: str
    title: str
    category: ContentCategory
    description: str

    # Launch spec (strings, not imports)
    run_module: Optional[str] = None
    run_function_name: Optional[str] = None

    # Cached resolved callable (excluded from repr/compare)
    _resolved_callable: Optional[Callable] = field(
        default=None, repr=False, compare=False
    )

    # Backend and capabilities
    backend: RenderingBackend = RenderingBackend.TERMINAL
    joystick_support: bool = True
    keyboard_support: bool = True
    controls_hint: str = ""
    has_intro: bool = False
    is_new: bool = False

    # Metadata
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"
    author: str = ""
    source_path: Optional[Path] = None

    @property
    def run_function(self) -> Optional[Callable]:
        """Lazily resolve the run function via importlib.

        On first access, imports the module and looks up the function.
        Caches the result for subsequent calls. Returns None if no
        module/function is specified or if import fails.
        """
        if self._resolved_callable is not None:
            return self._resolved_callable

        if not self.run_module or not self.run_function_name:
            return None

        try:
            module = importlib.import_module(self.run_module)
            fn = getattr(module, self.run_function_name)
            # Cache via object.__setattr__ since dataclass may be frozen-like
            object.__setattr__(self, '_resolved_callable', fn)
            return fn
        except (ImportError, AttributeError) as e:
            logger.warning(
                "Failed to resolve %s.%s: %s",
                self.run_module, self.run_function_name, e
            )
            return None


class ContentRegistry:
    """Registry for discovering and managing available content.

    Supports three registration paths:
    1. Auto-discovery via scan_directory() reading metadata.json files
    2. Direct callable registration via register_callable()
    3. Plugin bridge via bridge_plugin()

    Args:
        expected_minimum: If > 0, log a warning when content count is below
            this threshold after scan operations.
    """

    def __init__(self, expected_minimum: int = 0) -> None:
        self._content: Dict[str, ContentMetadata] = {}
        self._by_category: Dict[ContentCategory, List[ContentMetadata]] = {
            cat: [] for cat in ContentCategory
        }
        self._expected_minimum = expected_minimum

    def register_metadata(self, metadata: ContentMetadata) -> None:
        """Register content metadata. Overwrites on duplicate id.

        Args:
            metadata: ContentMetadata instance to register
        """
        # Remove old entry from category index if overwriting
        if metadata.id in self._content:
            old = self._content[metadata.id]
            cat_list = self._by_category[old.category]
            self._by_category[old.category] = [
                m for m in cat_list if m.id != metadata.id
            ]

        self._content[metadata.id] = metadata
        self._by_category[metadata.category].append(metadata)

    def register_callable(
        self,
        id: str,
        title: str,
        category: ContentCategory,
        description: str,
        run_fn: Callable,
        **kwargs,
    ) -> ContentMetadata:
        """Register a callable directly without a metadata.json file.

        Derives run_module and run_function_name from the callable for
        introspection, and stores the callable in _resolved_callable
        so no lazy import is needed.

        Args:
            id: Unique content identifier
            title: Display name
            category: Content category
            description: Short description
            run_fn: The callable to invoke
            **kwargs: Additional ContentMetadata fields

        Returns:
            The created ContentMetadata instance
        """
        metadata = ContentMetadata(
            id=id,
            title=title,
            category=category,
            description=description,
            run_module=getattr(run_fn, '__module__', None),
            run_function_name=getattr(run_fn, '__name__', None),
            _resolved_callable=run_fn,
            **kwargs,
        )
        self.register_metadata(metadata)
        return metadata

    def scan_directory(
        self,
        directory: Path,
        default_category: ContentCategory = ContentCategory.GAME,
    ) -> int:
        """Scan a directory for subdirectories containing metadata.json.

        Each subdirectory with a valid metadata.json is parsed and registered.
        Malformed JSON files are logged as warnings and skipped.

        Args:
            directory: Parent directory to scan
            default_category: Category to use when metadata doesn't specify one

        Returns:
            Number of content items successfully registered from this scan
        """
        if not directory.is_dir():
            logger.warning("Scan directory does not exist: %s", directory)
            self.check_minimum()
            return 0

        count = 0
        for subdir in sorted(directory.iterdir()):
            if not subdir.is_dir():
                continue

            metadata_file = subdir / "metadata.json"
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(
                    "Malformed metadata in %s: %s", metadata_file, e
                )
                continue

            metadata = self._parse_metadata(data, subdir, default_category)
            self.register_metadata(metadata)
            count += 1

        self.check_minimum()
        return count

    def _parse_metadata(
        self,
        data: dict,
        source_dir: Path,
        default_category: ContentCategory,
    ) -> ContentMetadata:
        """Parse a metadata dict into a ContentMetadata instance.

        Args:
            data: Parsed JSON dictionary
            source_dir: Directory the metadata was loaded from
            default_category: Fallback category if not specified in data

        Returns:
            ContentMetadata instance (with lazy resolution, not eagerly imported)
        """
        # Resolve category from string
        category_str = data.get("category", "")
        category = CATEGORY_STRING_MAP.get(category_str, default_category)

        # Extract run function spec
        run_spec = data.get("run_function", {})
        run_module = run_spec.get("module") if isinstance(run_spec, dict) else None
        run_function_name = run_spec.get("function") if isinstance(run_spec, dict) else None

        return ContentMetadata(
            id=source_dir.name,
            title=data.get("title", source_dir.name),
            category=category,
            description=data.get("description", ""),
            run_module=run_module,
            run_function_name=run_function_name,
            backend=RenderingBackend.TERMINAL,
            joystick_support=data.get("joystick_support", True),
            keyboard_support=data.get("keyboard_support", True),
            controls_hint=data.get("controls_hint", ""),
            has_intro=data.get("has_intro", False),
            is_new=data.get("is_new", False),
            tags=data.get("tags", []),
            version=data.get("version", "1.0"),
            author=data.get("author", ""),
            source_path=source_dir,
        )

    def bridge_plugin(self, manifest) -> ContentMetadata:
        """Bridge a PluginManifest into the content registry.

        Import of PluginManifest is deferred to method level to avoid
        circular imports between core and plugins packages.

        Args:
            manifest: A PluginManifest instance

        Returns:
            The created ContentMetadata instance
        """
        metadata = ContentMetadata(
            id=f"plugin-{manifest.name}",
            title=manifest.name.replace('-', ' ').replace('_', ' ').title(),
            category=ContentCategory.SHADER_DEMO,
            description=manifest.description,
            backend=RenderingBackend.PLUGIN,
            version=manifest.version,
            author=manifest.author,
            source_path=manifest.plugin_dir,
        )
        self.register_metadata(metadata)
        return metadata

    def bridge_all_plugins(self, plugin_manager) -> int:
        """Bridge all plugins from a plugin manager into the registry.

        Args:
            plugin_manager: Object with a .plugins dict of {name: PluginManifest}

        Returns:
            Number of plugins bridged
        """
        count = 0
        for manifest in plugin_manager.plugins.values():
            self.bridge_plugin(manifest)
            count += 1
        return count

    # --- Query API ---

    def get(self, id: str) -> Optional[ContentMetadata]:
        """Get content metadata by id.

        Args:
            id: Content identifier

        Returns:
            ContentMetadata or None
        """
        return self._content.get(id)

    def get_by_category(
        self, category: ContentCategory
    ) -> List[ContentMetadata]:
        """Get all content in a category.

        Args:
            category: Category to filter by

        Returns:
            List of ContentMetadata in that category
        """
        return list(self._by_category.get(category, []))

    def get_all(self) -> List[ContentMetadata]:
        """Get all registered content.

        Returns:
            List of all ContentMetadata
        """
        return list(self._content.values())

    def search(self, query: str) -> List[ContentMetadata]:
        """Search content by title, description, or tags.

        Case-insensitive substring matching.

        Args:
            query: Search string

        Returns:
            List of matching ContentMetadata
        """
        q = query.lower()
        return [
            m for m in self._content.values()
            if (q in m.title.lower()
                or q in m.description.lower()
                or any(q in tag.lower() for tag in m.tags))
        ]

    def count(self) -> int:
        """Get total number of registered content items."""
        return len(self._content)

    def category_counts(self) -> Dict[ContentCategory, int]:
        """Get count of content in each category.

        Returns:
            Dict mapping each ContentCategory to its item count
        """
        return {
            cat: len(items) for cat, items in self._by_category.items()
        }

    # --- Safety ---

    def check_minimum(self) -> None:
        """Log a warning if content count is below expected_minimum."""
        if self._expected_minimum > 0 and self.count() < self._expected_minimum:
            logger.warning(
                "Registry has %d items, expected at least %d",
                self.count(), self._expected_minimum,
            )
