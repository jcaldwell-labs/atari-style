"""Main entry point for Atari-style terminal demos."""

import sys
from pathlib import Path
from .core.menu import Menu, MenuItem
from .core.registry import ContentCategory, ContentRegistry


def _build_registry() -> ContentRegistry:
    """Populate the content registry with all available demos.

    Registration order matters: register_callable() entries for atari_style/
    demos are registered first, then scan_directory() discovers terminal_arcade/
    games. Since register_metadata() overwrites on duplicate id, the scanned
    entries for shared games (pacman, galaga, etc.) will replace the callable
    entries — giving them lazy resolution instead of eager imports.

    Content unique to atari_style/ (flux control variants, tools) stays as
    register_callable() since those directories lack metadata.json.
    """
    reg = ContentRegistry(expected_minimum=17)

    # --- Games: registered with string-based lazy resolution ---
    # These use run_module/run_function_name strings so no eager import happens.
    # If terminal_arcade/games/ exists, scan_directory() will overwrite shared
    # entries with its own module paths.
    from .core.registry import ContentMetadata

    for game_id, title, desc, module, func in [
        ("pacman", "Pac-Man", "Classic maze chase game with ghost AI",
         "atari_style.demos.games.pacman", "run_pacman"),
        ("galaga", "Galaga", "Space shooter with dive attacks",
         "atari_style.demos.games.galaga", "run_galaga"),
        ("grandprix", "Grand Prix", "First-person 3D racing",
         "atari_style.demos.games.grandprix", "run_grandprix"),
        ("breakout", "Breakout", "Paddle and ball physics game",
         "atari_style.demos.games.breakout", "run_breakout"),
    ]:
        reg.register_metadata(ContentMetadata(
            id=game_id, title=title, category=ContentCategory.GAME,
            description=desc, run_module=module, run_function_name=func,
        ))

    # Visualizers
    from .demos.visualizers.flux_control import run_flux_control
    from .demos.visualizers.flux_control_patterns import run_pattern_flux
    from .demos.visualizers.flux_control_rhythm import run_rhythm_flux
    from .demos.visualizers.flux_control_zen import run_flux_zen
    from .demos.visualizers.flux_control_explorer import run_flux_explorer
    from .demos.visualizers.starfield import run_starfield
    from .demos.visualizers.screensaver import run_screensaver
    from .demos.visualizers.gl_mandelbrot import run_gl_mandelbrot
    from .demos.visualizers.platonic_solids import run_platonic_solids
    from .demos.visualizers.educational import run_lissajous_explorer

    reg.register_callable("flux-control", "Flux Control",
                          ContentCategory.VISUALIZER,
                          "Parametric visual controller", run_flux_control)
    reg.register_callable("flux-patterns", "Flux Control: Patterns",
                          ContentCategory.VISUALIZER,
                          "Pattern-based flux modes", run_pattern_flux)
    reg.register_callable("flux-rhythm", "Flux Control: Rhythm",
                          ContentCategory.VISUALIZER,
                          "Rhythm-driven flux modes", run_rhythm_flux)
    reg.register_callable("flux-zen", "Flux Control: Zen",
                          ContentCategory.VISUALIZER,
                          "Meditative flux modes", run_flux_zen)
    reg.register_callable("flux-explorer", "Flux Control: Explorer",
                          ContentCategory.VISUALIZER,
                          "Interactive flux parameter explorer", run_flux_explorer)
    reg.register_callable("starfield", "Starfield",
                          ContentCategory.VISUALIZER,
                          "3D space flight with parallax layers", run_starfield)
    reg.register_callable("screensaver", "Screen Saver",
                          ContentCategory.VISUALIZER,
                          "8 parametric animations", run_screensaver)
    reg.register_callable("gl-mandelbrot", "GPU Mandelbrot",
                          ContentCategory.VISUALIZER,
                          "GPU-accelerated Mandelbrot explorer", run_gl_mandelbrot)
    reg.register_callable("lissajous", "Lissajous Explorer",
                          ContentCategory.VISUALIZER,
                          "Educational Lissajous curve explorer", run_lissajous_explorer)
    reg.register_callable("platonic-solids", "Platonic Solids",
                          ContentCategory.VISUALIZER,
                          "Interactive 3D geometry viewer", run_platonic_solids)

    # Tools
    from .demos.tools.ascii_painter import run_ascii_painter
    from .demos.tools.joystick_test import run_joystick_test
    from .demos.tools.canvas_explorer import run_canvas_explorer

    reg.register_callable("ascii-painter", "ASCII Painter",
                          ContentCategory.TOOL,
                          "Full-featured drawing program", run_ascii_painter)
    reg.register_callable("canvas-explorer", "Canvas Explorer",
                          ContentCategory.TOOL,
                          "Canvas exploration tool", run_canvas_explorer)
    reg.register_callable("joystick-test", "Joystick Test",
                          ContentCategory.TOOL,
                          "Connection verification and axis testing", run_joystick_test)

    # --- Auto-discovery from terminal_arcade/games/ ---
    # Scans for metadata.json files in per-game subdirectories.
    # Games that share ids with register_callable() entries above (pacman,
    # galaga, breakout, grandprix) will overwrite them, gaining lazy
    # resolution. Games unique to terminal_arcade/ (spaceship, targetshooter,
    # mandelbrot, oscilloscope) are added as new entries.
    ta_games = Path(__file__).resolve().parent.parent / "terminal_arcade" / "games"
    if ta_games.is_dir():
        reg.scan_directory(ta_games, default_category=ContentCategory.GAME)

    return reg


def _registry_to_menu_items(registry: ContentRegistry) -> list:
    """Convert registry content to MenuItem list for the menu system.

    Groups items by category in display order: Games, Visualizers, Tools,
    Shader Demos. Appends Exit as the final entry.
    """
    display_order = [
        ContentCategory.GAME,
        ContentCategory.VISUALIZER,
        ContentCategory.TOOL,
        ContentCategory.SHADER_DEMO,
    ]

    items = []
    for category in display_order:
        for content in registry.get_by_category(category):
            items.append(MenuItem(
                content.title,
                content.run_function,
                content.description,
            ))

    items.append(MenuItem("Exit", sys.exit))
    return items


def main():
    """Main entry point."""
    registry = _build_registry()
    menu_items = _registry_to_menu_items(registry)

    menu = Menu("ATARI-STYLE TERMINAL DEMOS", menu_items)

    try:
        menu.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("\nThanks for playing!")


if __name__ == "__main__":
    main()
