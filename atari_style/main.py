"""Main entry point for Atari-style terminal demos."""

import sys
from .core.menu import Menu, MenuItem
from .core.registry import ContentCategory, ContentRegistry


def _build_registry() -> ContentRegistry:
    """Populate the content registry with all available demos.

    Uses register_callable() for each demo. In Phase 3 these will migrate
    to metadata.json auto-discovery via scan_directory().
    """
    reg = ContentRegistry(expected_minimum=17)

    # Games
    from .demos.games.pacman import run_pacman
    from .demos.games.galaga import run_galaga
    from .demos.games.grandprix import run_grandprix
    from .demos.games.breakout import run_breakout

    reg.register_callable("pacman", "Pac-Man", ContentCategory.GAME,
                          "Classic maze chase game with ghost AI", run_pacman)
    reg.register_callable("galaga", "Galaga", ContentCategory.GAME,
                          "Space shooter with dive attacks", run_galaga)
    reg.register_callable("grandprix", "Grand Prix", ContentCategory.GAME,
                          "First-person 3D racing", run_grandprix)
    reg.register_callable("breakout", "Breakout", ContentCategory.GAME,
                          "Paddle and ball physics game", run_breakout)

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
