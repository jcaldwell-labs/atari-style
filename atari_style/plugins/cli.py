"""Plugin management CLI.

Provides commands for listing, installing, and validating plugins.

Usage:
    python -m atari_style.plugins.cli list
    python -m atari_style.plugins.cli validate ./my-plugin/
    python -m atari_style.plugins.cli install ./my-plugin/
    python -m atari_style.plugins.cli create my-new-effect
"""

import argparse
import json
import sys
from pathlib import Path

from .schema import PluginManifest, PluginType, PluginParameter
from .discovery import get_plugin_dirs, install_plugin, get_user_plugin_dir
from .loader import PluginManager


def cmd_list(args):
    """List available plugins."""
    manager = PluginManager()
    count = manager.discover()

    if args.json:
        plugins = [p.to_dict() for p in manager.list_plugins()]
        print(json.dumps(plugins, indent=2))
        return 0

    if count == 0:
        print("No plugins found.")
        print(f"\nPlugin directories searched:")
        for d in get_plugin_dirs():
            print(f"  {d}")
        return 0

    print(f"Found {count} plugin(s):\n")

    # Group by type
    by_type = {}
    for plugin in manager.list_plugins():
        type_name = plugin.type.value
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(plugin)

    for type_name, plugins in sorted(by_type.items()):
        print(f"{type_name.upper()}S:")
        for p in plugins:
            status = "✓" if not p.validate() else "⚠"
            print(f"  {status} {p.name} v{p.version}")
            if p.description:
                desc = p.description[:60]
                suffix = "..." if len(p.description) > 60 else ""
                print(f"      {desc}{suffix}")
            if args.verbose:
                print(f"      Author: {p.author or 'unknown'}")
                print(f"      Path: {p.plugin_dir}")
        print()

    return 0


def cmd_validate(args):
    """Validate a plugin."""
    plugin_path = Path(args.path)

    if not plugin_path.exists():
        print(f"Error: Path not found: {plugin_path}")
        return 1

    manifest_path = plugin_path / 'manifest.json'
    if not manifest_path.exists():
        print(f"Error: No manifest.json found in {plugin_path}")
        return 1

    try:
        manifest = PluginManifest.from_file(manifest_path)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in manifest: {e}")
        return 1
    except Exception as e:
        print(f"Error: Failed to load manifest: {e}")
        return 1

    errors = manifest.validate()

    if errors:
        print(f"Validation FAILED for '{manifest.name}':\n")
        for error in errors:
            print(f"  ✗ {error}")
        return 1

    print(f"Validation PASSED for '{manifest.name}' v{manifest.version}")
    print(f"\nPlugin details:")
    print(f"  Type: {manifest.type.value}")
    print(f"  Author: {manifest.author or 'not specified'}")
    print(f"  Description: {manifest.description or 'none'}")
    print(f"  Parameters: {len(manifest.parameters)}")

    if manifest.parameters:
        print("\n  Parameters:")
        for p in manifest.parameters:
            print(f"    - {p.name}: [{p.min_value}, {p.max_value}] default={p.default}")

    return 0


def cmd_install(args):
    """Install a plugin."""
    source_path = Path(args.path)

    try:
        target = install_plugin(source_path, args.name)
        print(f"✓ Installed plugin to: {target}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1


def cmd_create(args):
    """Create a new plugin from template."""
    name = args.name
    plugin_dir = get_user_plugin_dir() / name

    if plugin_dir.exists():
        print(f"Error: Plugin directory already exists: {plugin_dir}")
        return 1

    plugin_dir.mkdir(parents=True)

    # Create manifest
    manifest = PluginManifest(
        name=name,
        version="1.0.0",
        type=PluginType.SHADER,
        author="",
        description=f"Custom {name} shader effect",
        parameters=[
            PluginParameter("param_a", "Parameter A", 0.0, 1.0, 0.5, "First parameter"),
            PluginParameter("param_b", "Parameter B", 0.0, 1.0, 0.5, "Second parameter"),
            PluginParameter("param_c", "Parameter C", 0.0, 1.0, 0.5, "Third parameter"),
            PluginParameter("param_d", "Parameter D", 0.0, 1.0, 0.5, "Fourth parameter"),
        ],
        shader="shader.glsl",
        recommended_duration=10.0,
        default_color_mode=0
    )

    # Write manifest
    manifest_path = plugin_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        f.write(manifest.to_json())

    # Create shader from template
    shader_path = plugin_dir / 'shader.glsl'
    template_path = Path(__file__).parent / 'templates' / 'default_shader.glsl'

    if template_path.exists():
        with open(template_path, 'r') as f:
            shader_template = f.read()
    else:
        # Fallback inline template if file not found
        shader_template = '''#version 330 core
uniform float u_time;
uniform vec2 u_resolution;
uniform vec4 u_params;
uniform int u_color_mode;
out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    float t = u_time * u_params.x;
    vec3 color = 0.5 + 0.5 * cos(t + uv.xyx + vec3(0, 2, 4));
    fragColor = vec4(color, 1.0);
}
'''
    with open(shader_path, 'w') as f:
        f.write(shader_template)

    print(f"✓ Created plugin at: {plugin_dir}")
    print(f"\nFiles created:")
    print(f"  {manifest_path}")
    print(f"  {shader_path}")
    print(f"\nNext steps:")
    print(f"  1. Edit {shader_path} with your shader code")
    print(f"  2. Update {manifest_path} with correct metadata")
    print(f"  3. Validate: python -m atari_style.plugins.cli validate {plugin_dir}")
    print(f"  4. Test: python -m atari_style.core.gl.video_export {name} --preview")

    return 0


def cmd_dirs(args):
    """Show plugin directories."""
    print("Plugin directories (searched in order):\n")
    for d in get_plugin_dirs():
        exists = "✓" if d.exists() else "✗"
        print(f"  {exists} {d}")

    print(f"\nUser plugin directory: {get_user_plugin_dir()}")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='atari-style plugin manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s list                    List all installed plugins
  %(prog)s list --json             Output as JSON
  %(prog)s validate ./my-plugin/   Validate a plugin
  %(prog)s install ./my-plugin/    Install a plugin
  %(prog)s create my-effect        Create a new plugin from template
  %(prog)s dirs                    Show plugin directories
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # list command
    list_parser = subparsers.add_parser('list', help='List installed plugins')
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Show details')

    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a plugin')
    validate_parser.add_argument('path', help='Path to plugin directory')

    # install command
    install_parser = subparsers.add_parser('install', help='Install a plugin')
    install_parser.add_argument('path', help='Path to plugin directory')
    install_parser.add_argument('--name', help='Override plugin name')

    # create command
    create_parser = subparsers.add_parser('create', help='Create new plugin from template')
    create_parser.add_argument('name', help='Plugin name (kebab-case)')

    # dirs command
    subparsers.add_parser('dirs', help='Show plugin directories')

    args = parser.parse_args()

    if args.command == 'list':
        return cmd_list(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'install':
        return cmd_install(args)
    elif args.command == 'create':
        return cmd_create(args)
    elif args.command == 'dirs':
        return cmd_dirs(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
