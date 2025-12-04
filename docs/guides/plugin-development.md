# Plugin Development Guide

This guide explains how to create, install, and manage plugins for atari-style.

## Overview

Plugins extend atari-style with custom shaders, effects, and visualizations. The plugin system follows these principles:

- **AI-authorable**: Clear schema, validation, and templates
- **Discoverable**: Automatic plugin detection from standard directories
- **Composable**: Plugins integrate with existing tools and pipelines
- **Safe**: GLSL runs in GPU sandbox; validation before loading

## Plugin Types

| Type | Description | Example |
|------|-------------|---------|
| `shader` | GLSL fragment shader | New visual effect |
| `composite` | Combination of shaders | Layered effects |
| `connector` | Export/import format | New integrations |
| `explorer` | Parameter search algorithm | Novel discovery methods |

## Quick Start

### Create a New Plugin

```bash
# Generate from template
python -m atari_style.plugins.cli create my-cool-effect

# Files created:
# ~/.atari-style/plugins/my-cool-effect/
#   manifest.json
#   shader.glsl
```

### Validate Your Plugin

```bash
python -m atari_style.plugins.cli validate ~/.atari-style/plugins/my-cool-effect
```

### List Available Plugins

```bash
python -m atari_style.plugins.cli list
```

## Plugin Structure

```
my-plugin/
├── manifest.json    # Required: Plugin metadata and configuration
├── shader.glsl      # Required for shader plugins: GLSL code
└── preview.png      # Optional: Preview image for gallery
```

## Manifest Schema

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "type": "shader",
  "author": "Your Name",
  "description": "Description of what this plugin does",
  "parameters": [
    {
      "name": "param_a",
      "display_name": "Parameter A",
      "min": 0.0,
      "max": 1.0,
      "default": 0.5,
      "description": "What this parameter controls"
    },
    // ... 3 more parameters for shader plugins
  ],
  "shader": "shader.glsl",
  "preview": "preview.png",
  "recommended_duration": 10.0,
  "default_color_mode": 0
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier (kebab-case) |
| `version` | string | Semantic version (e.g., "1.0.0") |
| `type` | string | Plugin type ("shader", "composite", etc.) |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `author` | string | "" | Plugin author |
| `description` | string | "" | Plugin description |
| `parameters` | array | [] | Configurable parameters |
| `shader` | string | "shader.glsl" | Path to GLSL file |
| `preview` | string | null | Path to preview image |
| `recommended_duration` | float | 10.0 | Suggested animation length |
| `default_color_mode` | int | 0 | Default color palette (0-3) |

### Parameter Schema

Shader plugins must have exactly 4 parameters (mapped to `u_params.xyzw`):

```json
{
  "name": "wave_speed",
  "display_name": "Wave Speed",
  "min": 0.0,
  "max": 2.0,
  "default": 0.5,
  "description": "Speed of wave animation"
}
```

## GLSL Shader Requirements

Shaders receive these uniforms from atari-style:

```glsl
uniform float u_time;        // Animation time in seconds
uniform vec2 u_resolution;   // Render resolution
uniform vec4 u_params;       // param_a, param_b, param_c, param_d
uniform int u_color_mode;    // Color palette (0-3)

out vec4 fragColor;          // Output color
```

### Shader Template

```glsl
#version 330 core

uniform float u_time;
uniform vec2 u_resolution;
uniform vec4 u_params;
uniform int u_color_mode;

out vec4 fragColor;

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / min(u_resolution.x, u_resolution.y);

    // Unpack parameters
    float param_a = u_params.x;
    float param_b = u_params.y;
    float param_c = u_params.z;
    float param_d = u_params.w;

    // Your effect code here
    vec3 color = vec3(0.5 + 0.5 * cos(u_time + uv.xyx + vec3(0, 2, 4)));

    fragColor = vec4(color, 1.0);
}
```

## Plugin Directories

Plugins are discovered from these directories (in order):

1. **Built-in**: `atari_style/plugins/builtin/`
2. **User**: `~/.atari-style/plugins/`
3. **Environment**: `$ATARI_STYLE_PLUGINS` (colon-separated paths)

```bash
# Show plugin directories
python -m atari_style.plugins.cli dirs
```

## CLI Reference

```bash
# List all plugins
python -m atari_style.plugins.cli list
python -m atari_style.plugins.cli list --json
python -m atari_style.plugins.cli list --verbose

# Validate a plugin
python -m atari_style.plugins.cli validate ./my-plugin/

# Install a plugin
python -m atari_style.plugins.cli install ./my-plugin/
python -m atari_style.plugins.cli install ./my-plugin/ --name custom-name

# Create from template
python -m atari_style.plugins.cli create my-new-effect

# Show plugin directories
python -m atari_style.plugins.cli dirs
```

## Using Plugins in Code

```python
from atari_style.plugins import PluginManager

# Discover all plugins
manager = PluginManager()
manager.discover()

# List plugins
for plugin in manager.list_plugins():
    print(f"{plugin.name}: {plugin.description}")

# Get a specific shader
shader = manager.get_shader('aurora-waves')
if shader:
    print(f"Shader path: {shader.shader_path}")
    print(f"Parameters: {shader.param_names}")
```

## Testing Your Plugin

1. **Validate**: `python -m atari_style.plugins.cli validate ./my-plugin`
2. **Preview**: `python -m atari_style.core.gl.video_export my-plugin --preview`
3. **Full render**: `python -m atari_style.core.gl.video_export my-plugin -o output.mp4`

## Best Practices

1. **Naming**: Use kebab-case for plugin names (`my-cool-effect`)
2. **Parameters**: Name parameters descriptively (`wave_speed` not `p1`)
3. **Defaults**: Set sensible defaults that produce interesting output
4. **Ranges**: Use appropriate min/max ranges for each parameter
5. **Description**: Write clear descriptions for the plugin and each parameter
6. **Preview**: Include a preview.png showing typical output

## Troubleshooting

### Plugin Not Found

- Check plugin is in a valid directory (`dirs` command)
- Ensure `manifest.json` exists and is valid JSON
- Run `validate` to check for errors

### Shader Errors

- Check GLSL version compatibility (`#version 330 core`)
- Verify all uniforms are used correctly
- Test with simpler shaders first

### Parameter Issues

- Shader plugins require exactly 4 parameters
- Ensure default values are within min/max range
- Check parameter names match usage in shader
