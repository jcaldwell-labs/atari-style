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

    # --- Visualizers: string-based lazy resolution ---
    _viz = "atari_style.demos.visualizers"
    for viz_id, title, desc, module_suffix, func in [
        ("flux-control", "Flux Control",
         "Parametric visual controller", "flux_control", "run_flux_control"),
        ("flux-patterns", "Flux Control: Patterns",
         "Pattern-based flux modes", "flux_control_patterns", "run_pattern_flux"),
        ("flux-rhythm", "Flux Control: Rhythm",
         "Rhythm-driven flux modes", "flux_control_rhythm", "run_rhythm_flux"),
        ("flux-zen", "Flux Control: Zen",
         "Meditative flux modes", "flux_control_zen", "run_flux_zen"),
        ("flux-explorer", "Flux Control: Explorer",
         "Interactive flux parameter explorer",
         "flux_control_explorer", "run_flux_explorer"),
        ("starfield", "Starfield",
         "3D space flight with parallax layers", "starfield", "run_starfield"),
        ("screensaver", "Screen Saver",
         "8 parametric animations", "screensaver", "run_screensaver"),
        ("gl-mandelbrot", "GPU Mandelbrot",
         "GPU-accelerated Mandelbrot explorer",
         "gl_mandelbrot", "run_gl_mandelbrot"),
        ("lissajous", "Lissajous Explorer",
         "Educational Lissajous curve explorer",
         "educational", "run_lissajous_explorer"),
        ("platonic-solids", "Platonic Solids",
         "Interactive 3D geometry viewer",
         "platonic_solids", "run_platonic_solids"),
    ]:
        reg.register_metadata(ContentMetadata(
            id=viz_id, title=title, category=ContentCategory.VISUALIZER,
            description=desc, run_module=f"{_viz}.{module_suffix}",
            run_function_name=func,
        ))

    # --- Tools: string-based lazy resolution ---
    _tools = "atari_style.demos.tools"
    for tool_id, title, desc, module_suffix, func in [
        ("ascii-painter", "ASCII Painter",
         "Full-featured drawing program", "ascii_painter", "run_ascii_painter"),
        ("canvas-explorer", "Canvas Explorer",
         "Canvas exploration tool", "canvas_explorer", "run_canvas_explorer"),
        ("joystick-test", "Joystick Test",
         "Connection verification and axis testing",
         "joystick_test", "run_joystick_test"),
    ]:
        reg.register_metadata(ContentMetadata(
            id=tool_id, title=title, category=ContentCategory.TOOL,
            description=desc, run_module=f"{_tools}.{module_suffix}",
            run_function_name=func,
        ))

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
            run_fn = content.run_function
            if run_fn is None:
                continue
            items.append(MenuItem(
                content.title,
                run_fn,
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
