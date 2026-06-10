# Architecture Guide

Decision record resolving the structural questions in issue #155. This is the
"I want to add X — where does it go?" reference for contributors (human and AI).

**Last updated:** 2026-06-10

## Project Identity

atari-style started as a collection of retro game clones. That is no longer the
center of gravity. The project's primary product is a **parametric visualization
engine**: animations with live-adjustable parameters (keyboard/joystick), a
GPU shader pipeline with cross-modulated composites and post-processing, and a
video export toolchain that feeds the @jcaldwell-labs YouTube channel.

Games remain as content and examples — they exercise the renderer, input
handling, and registry — but new investment should default to the engine,
visualizers, and video tooling.

```
                         ┌─────────────────────────┐
                         │      ContentRegistry     │  ← single discovery point
                         └───────────┬─────────────┘
              ┌──────────────────────┼──────────────────────┐
        visualizers (primary)   games (content)        tools (utility)
              │                      │                      │
   ┌──────────┴──────────┐    terminal renderer       terminal renderer
   │                     │    (blessed, interactive)
 GL pipeline       terminal renderer
 (moderngl,        (blessed, interactive)
  video export)
```

## Decisions

### 1. `atari_style/` is the canonical package

`terminal_arcade/` is **deprecated** (its `main` already warns). Disposition:

- All new code goes in `atari_style/`.
- `terminal_arcade/games/` remains a **read-only content source**: its per-game
  directories with `metadata.json` are auto-discovered by `ContentRegistry` at
  startup (`atari_style/main.py`). Treat them as data, not code.
- `terminal_arcade/engine/` and `terminal_arcade/launcher/` receive no fixes.
  Known divergences (e.g., its `input_handler.py` still has a bare `except`
  that was fixed in `atari_style` by #158) are intentionally left as-is.
- Migration end-state: when a `terminal_arcade` game needs real work, port it
  to `atari_style/demos/games/` and delete the original.

**Rationale:** `atari_style/` has all active development (GL pipeline, video
tooling, plugins, ContentRegistry, 150+ commits in 2026 vs. zero meaningful
ones in `terminal_arcade/`), and `ContentRegistry` (issue #156) already
subsumed the one good idea in `terminal_arcade` — metadata-driven discovery.

### 2. GL pipeline and terminal renderer are permanent peers

They serve different outputs and neither replaces the other:

| | Terminal renderer (`core/renderer.py`) | GL pipeline (`core/gl/`) |
|---|---|---|
| Output | live interactive terminal | offscreen frames → video/GIF/thumbnails |
| Strengths | input loops, menus, games, in-terminal demos | per-pixel math, composites, post-FX (CRT/ASCII/phosphor), 1080p+ |
| Use when | a human plays/explores it live | the result is a rendered artifact |

A concept may exist in both (e.g., plasma has a terminal mode and a GL shader).
That duplication is acceptable — they are different renderings of the same
idea, not duplicated infrastructure. Shared logic (parameter definitions,
palettes) belongs in `core/`.

### 3. Where new content goes

| Adding… | Location | Registration |
|---|---|---|
| Visualizer (terminal) | `atari_style/demos/visualizers/` | register in `main.py` via ContentRegistry (lazy, string-based) |
| GL shader effect | `atari_style/shaders/effects/*.frag` + `CompositeConfig` entry in `core/gl/composites.py` | auto-discovered by CompositeManager |
| Game | `atari_style/demos/games/` | ContentRegistry in `main.py` |
| Tool | `atari_style/demos/tools/` | ContentRegistry in `main.py` |
| Post-processing effect | `atari_style/shaders/post/*.frag` + wire into `core/gl/pipeline.py` | — |

New visualizers should implement the `ParametricAnimation` protocol
(`adjust_params`, `get_param_info`, see `demos/visualizers/screensaver.py`):
**live parameter control is the product**, not an optional nicety.

### 4. Plugin system: keep, dormant

`atari_style/plugins/` (schema, loader, discovery, CLI) is complete but has no
runtime consumer — `ContentRegistry.bridge_all_plugins()` exists and is never
called. Decision:

- Do **not** require new features to be plugins.
- Do not delete it: the schema is the extension point for third-party shaders
  if/when there's an external consumer (see #161 zone-mode discussion).
- Wire `bridge_all_plugins()` into startup only when the first real plugin exists.

### 5. Testing conventions

- New tests go in `tests/` (pytest/unittest discoverable as `test_*.py`).
- Root-level `test_*.py` files are legacy; migrate opportunistically, don't add.
- Visualizers: headless smoke test via `headless_renderer.py` (renders N frames,
  asserts no exception and non-empty buffer). Visual-regression baselines in
  `baselines/` are best-effort, not CI-gating.
- GL composites: a render test that exports 1 frame per composite is sufficient
  (catches shader compile errors on llvmpipe).

### 6. Video pipeline is load-bearing

The video toolchain (`core/gl/video_export.py`, `core/demo_video.py`,
`core/video_script.py` + CLI, `core/showcase.py`, storyboards) is **not** an
experiment — it is the publishing pipeline for the YouTube channel and a core
part of the engine identity.

- A new GL composite should be exportable via
  `python -m atari_style.core.gl.video_export <name>` on the day it lands.
- Content guidance for published videos (derived from channel analytics,
  June 2026): bright/saturated beats dark/sparse, recognizable subjects beat
  abstract ones, under 60s, never include shell chrome, end on the strongest
  frame. See `.github/planning/` for the working notes.
- Storyboards (`storyboards/*.json`) are optional; use them for multi-segment
  videos, not single-composite exports.

## Quick decision tree

```
I want to add…
├─ a visual effect rendered to video        → GL shader + CompositeConfig (§3)
├─ an interactive in-terminal experience    → demos/visualizers/ + ParametricAnimation (§3)
├─ a game                                   → demos/games/ + ContentRegistry (§3)
├─ a post-processing look (CRT, ASCII…)     → shaders/post/ + pipeline.py (§3)
├─ a fix to terminal_arcade                 → don't; port the game out instead (§1)
└─ a plugin                                 → not yet; open an issue first (§4)
```

## Related

- Issue #155 (this document resolves it)
- Issue #161 — zone mode reimplementation (open decision; any new attempt
  should use ContentRegistry and a safer IPC than raw TCP `setattr`)
- `docs/architecture.md` — historical pre-GL rendering analysis (kept for context)
- `PHILOSOPHY.md` — design principles
