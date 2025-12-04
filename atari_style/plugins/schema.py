"""Plugin manifest schema definitions.

Defines the structure of plugin manifests and validation rules.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import json


class PluginType(Enum):
    """Types of plugins supported by atari-style."""
    SHADER = "shader"
    COMPOSITE = "composite"
    CONNECTOR = "connector"
    EXPLORER = "explorer"


@dataclass
class PluginParameter:
    """A configurable parameter for a plugin.

    Attributes:
        name: Parameter identifier (snake_case)
        display_name: Human-readable name
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        default: Default value
        description: Parameter description
    """
    name: str
    display_name: str
    min_value: float
    max_value: float
    default: float
    description: str = ""

    def validate_value(self, value: float) -> bool:
        """Check if a value is within the valid range."""
        return self.min_value <= value <= self.max_value

    def clamp(self, value: float) -> float:
        """Clamp a value to the valid range."""
        return max(self.min_value, min(self.max_value, value))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginParameter':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            name=data['name'],
            display_name=data.get('display_name', data['name'].replace('_', ' ').title()),
            min_value=float(data.get('min', 0.0)),
            max_value=float(data.get('max', 1.0)),
            default=float(data.get('default', 0.5)),
            description=data.get('description', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (JSON serialization)."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'min': self.min_value,
            'max': self.max_value,
            'default': self.default,
            'description': self.description
        }


@dataclass
class PluginManifest:
    """Plugin manifest containing metadata and configuration.

    The manifest.json file in each plugin directory must conform to this schema.

    Required fields:
        name: Unique plugin identifier (kebab-case)
        version: Semantic version string
        type: Plugin type (shader, composite, connector, explorer)

    Optional fields:
        author: Plugin author name
        description: Plugin description
        parameters: List of configurable parameters
        shader: Path to GLSL shader file (relative to plugin dir)
        preview: Path to preview image (relative to plugin dir)
        recommended_duration: Suggested animation duration in seconds
        default_color_mode: Default color palette (0-3)
    """
    name: str
    version: str
    type: PluginType
    author: str = ""
    description: str = ""
    parameters: List[PluginParameter] = field(default_factory=list)
    shader: str = "shader.glsl"
    preview: Optional[str] = None
    recommended_duration: float = 10.0
    default_color_mode: int = 0

    # Runtime fields (set during loading)
    plugin_dir: Optional[Path] = field(default=None, repr=False)

    @property
    def shader_path(self) -> Optional[Path]:
        """Full path to shader file."""
        if self.plugin_dir and self.shader:
            return self.plugin_dir / self.shader
        return None

    @property
    def preview_path(self) -> Optional[Path]:
        """Full path to preview image."""
        if self.plugin_dir and self.preview:
            return self.plugin_dir / self.preview
        return None

    @property
    def default_params(self) -> Tuple[float, ...]:
        """Default parameter values as tuple."""
        return tuple(p.default for p in self.parameters)

    @property
    def param_names(self) -> Tuple[str, ...]:
        """Parameter names as tuple."""
        return tuple(p.name for p in self.parameters)

    @property
    def param_ranges(self) -> Tuple[Tuple[float, float], ...]:
        """Parameter ranges as tuple of (min, max)."""
        return tuple((p.min_value, p.max_value) for p in self.parameters)

    def validate(self) -> List[str]:
        """Validate the manifest and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Name validation
        if not self.name:
            errors.append("Plugin name is required")
        elif not self.name.replace('-', '').replace('_', '').isalnum():
            errors.append(f"Plugin name must be alphanumeric with hyphens/underscores: {self.name}")

        # Version validation
        if not self.version:
            errors.append("Plugin version is required")
        else:
            parts = self.version.split('.')
            if len(parts) < 2:
                errors.append(f"Version must be semantic (e.g., 1.0.0): {self.version}")

        # Type-specific validation
        if self.type == PluginType.SHADER:
            if self.shader_path and not self.shader_path.exists():
                errors.append(f"Shader file not found: {self.shader_path}")

            if len(self.parameters) != 4:
                errors.append(f"Shader plugins must have exactly 4 parameters, found {len(self.parameters)}")

        # Parameter validation
        for i, param in enumerate(self.parameters):
            if param.min_value > param.max_value:
                errors.append(f"Parameter {param.name}: min must be less than max")
            if not param.validate_value(param.default):
                errors.append(f"Parameter {param.name}: default {param.default} outside range [{param.min_value}, {param.max_value}]")

        return errors

    @classmethod
    def from_dict(cls, data: Dict[str, Any], plugin_dir: Optional[Path] = None) -> 'PluginManifest':
        """Create from dictionary (JSON deserialization).

        Args:
            data: Dictionary from JSON manifest
            plugin_dir: Path to plugin directory (for resolving relative paths)
        """
        # Parse plugin type
        type_str = data.get('type', 'shader')
        try:
            plugin_type = PluginType(type_str)
        except ValueError:
            plugin_type = PluginType.SHADER

        # Parse parameters
        params_data = data.get('parameters', [])
        parameters = [PluginParameter.from_dict(p) for p in params_data]

        return cls(
            name=data.get('name', 'unnamed'),
            version=data.get('version', '0.0.0'),
            type=plugin_type,
            author=data.get('author', ''),
            description=data.get('description', ''),
            parameters=parameters,
            shader=data.get('shader', 'shader.glsl'),
            preview=data.get('preview'),
            recommended_duration=float(data.get('recommended_duration', 10.0)),
            default_color_mode=int(data.get('default_color_mode', 0)),
            plugin_dir=plugin_dir
        )

    @classmethod
    def from_file(cls, manifest_path: Path) -> 'PluginManifest':
        """Load manifest from JSON file.

        Args:
            manifest_path: Path to manifest.json file

        Returns:
            PluginManifest instance

        Raises:
            FileNotFoundError: If manifest file doesn't exist
            json.JSONDecodeError: If manifest is invalid JSON
        """
        with open(manifest_path) as f:
            data = json.load(f)
        return cls.from_dict(data, manifest_path.parent)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (JSON serialization)."""
        return {
            'name': self.name,
            'version': self.version,
            'type': self.type.value,
            'author': self.author,
            'description': self.description,
            'parameters': [p.to_dict() for p in self.parameters],
            'shader': self.shader,
            'preview': self.preview,
            'recommended_duration': self.recommended_duration,
            'default_color_mode': self.default_color_mode
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
