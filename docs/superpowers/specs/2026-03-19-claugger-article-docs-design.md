# Design Spec: Claugger Game + Linux Journal Article + Project Docs

**Date**: 2026-03-19
**Status**: Approved
**Issue**: #144 (Enhance project visibility and discoverability)

---

## Overview

Three interconnected deliverables to boost atari-style's visibility and onboard new developers:

1. **Claugger** — A Frogger-style terminal game starring an ASCII chicken
2. **Blog article** — A late-90s Linux Journal-style manifesto + tutorial
3. **Project documentation** — 5-page doc set published to jcaldwell-labs.github.io

The article is the spine. The game exists to prove the article's thesis. The docs exist so readers who arrive via the article can go deeper.

---

## 1. Claugger — The Game

### Concept

"Why did the chicken cross the road?" — a Frogger clone with an over-the-top ASCII chicken, egg-laying bonuses, and chicken puns throughout. The name is a hat tip to Claude Code.

### Gameplay

**Layout** (13 logical lanes, bottom to top — each lane renders as 3 terminal rows to accommodate sprites):
- Lane 1: Start zone (henhouse)
- Lanes 2-6: Road lanes (vehicles scroll horizontally)
- Lane 7: Safe median (sidewalk art)
- Lanes 8-12: River lanes (logs and turtles scroll horizontally)
- Lane 13: Goal zone (5 home nests to fill)

Total playing field: ~39 terminal rows for lanes + 3 rows for HUD = 42 rows minimum. Requires terminal height of at least 44 rows (standard 80x24 won't suffice — game displays a "resize terminal" message if too small).

**Core mechanics**:
- Classic Frogger rules: hop across road, ride river objects, reach a nest
- Fill all 5 nests to complete a level
- 60-second timer per life (egg timer visual). Timer resets on death/respawn and on each new level. Does NOT reset when filling a nest mid-level.
- 3 lives, level progression increases speeds
- Wrap-around on screen edges for objects

**Road hazards** (5 lanes):
- Cars: 4-char ASCII sprites, colored
- Trucks: 6-char ASCII sprites
- Motorcycles: 2-char ASCII sprites
- Each lane has independent speed and direction
- Density increases with level

**River objects** (5 lanes):
- Logs: 5-8 char and 3-char variants
- Turtles: groups of 2-3 (`@` characters), periodically dive (disappear for 2 seconds, resurface for 4 seconds — cycle is fixed per group but staggered across groups so not all dive simultaneously)
- Chicken rides on objects, drowns if it falls in water
- Lane speed and direction varies

### The Chicken

**Sprite**: 3x2 character multi-directional sprite with facing changes for up/down/left/right.

**Animations**:
- Walk cycle: 2-frame leg alternation
- Idle: occasional head bob
- Death (road): squashed flat (`___`), feathers scatter
- Death (river): drowning splash (`~*~`), bubbles rise
- Death (timeout): feathers fly (`' . ' .`), alarm sound via terminal bell

### Egg-Laying Bonus

- 5% chance per hop to lay an egg in the current lane. On river lanes, eggs are laid on the object the chicken is riding (log/turtle) and scroll with it. No eggs can be laid in water or on the safe median.
- Eggs persist in the lane, worth 200 points if you complete the level
- Eggs on road lanes can be squashed by vehicles (comic splat animation: `*`). Eggs on river objects fall in water if the object scrolls off-screen.
- Collecting 10 eggs across the game awards an extra life
- "EGGS-tra life!" message displayed

### HUD & Personality

- Score: "EGGS-cellent: 1,450"
- Lives: `>Q< >Q< >Q<` (chicken face characters)
- Level: "Crossing #3"
- Timer: egg timer visual that drains
- Death messages (rotating):
  - "Fowl play!"
  - "Chicken tender!"
  - "Poultry in motion... denied!"
  - "That's not how you cross the road!"
  - "Hen-ded!"
  - "Clucked out!"
- Level complete: "Why did the chicken cross the road? FOR [score] POINTS!"
- Game over: "THE ROOST IS COOKED" with final stats

### Easter Eggs

**1. The Konami Code**
If the player enters Up-Up-Down-Down-Left-Right-Left-Right-SELECT-BACK (mapped to Enter-Esc on keyboard, Button 0-Button 1 on joystick) at the title screen or during gameplay pause, the chicken transforms into a golden rooster sprite for the remainder of the level. The golden rooster is invincible for 5 seconds, leaves a trail of golden eggs (500 points each), and the HUD briefly displays "COCKA-DOODLE-CHEAT!" The effect is one-time-use per game session.

**2. The Road Scholar**
If the player completes 3 levels without losing a single life, a brief ASCII diploma animation plays between levels: a scroll unfurls with "ROAD SCHOLAR" and the chicken wearing a tiny graduation cap. The HUD shows "Why did the chicken cross the road? To get to the other SIDE of knowledge!" and awards a 5,000 point bonus. This references both the joke and the Linux Journal educational spirit.

### Technical Implementation

- File: `atari_style/demos/games/claugger.py`
- Class: `Claugger` with standard methods: `__init__()`, `draw()`, `update()`, `handle_input()`, `run()`
- Entry function: `run_claugger()`
- Uses `Renderer` and `InputHandler` from `atari_style.core`
- Registered in `ContentRegistry` with: `id="claugger"`, `title="Claugger"`, `category=ContentCategory.GAME`, `description="Why did the chicken cross the road? A Frogger tribute."`, `run_module="atari_style.demos.games.claugger"`, `run_function_name="run_claugger"`
- Added to menu in `main.py` in the Games section
- Target: ~30 FPS (`time.sleep(0.033)`)
- Full keyboard and joystick support
- Collision model: bounding box on the chicken's full 3x2 sprite area. Any overlap between a hazard character and a chicken character is a hit. This makes the game slightly harder but feels fair given the chunky ASCII aesthetic.
- Movement between lanes is instantaneous (snap to lane center). No intermediate hop animation that spans two lanes. The chicken is always fully in one lane for collision purposes. A brief 2-frame "hop" visual plays but the logical position updates atomically on the first frame.
- Estimated size: ~900-1100 lines
- Tests: `tests/test_claugger.py` covering lane scrolling, collision detection, egg mechanics, scoring, level progression, and easter egg triggers

---

## 2. Blog Article

### Title

*"Why Did the Chicken Cross the Terminal? Building Arcade Games Where Nobody Expected Them"*

### Voice & Tone

Late-1990s Linux Journal — practical, slightly irreverent, opinionated. Assumes the reader is comfortable with a terminal but doesn't assume game development experience. References: Larry Wall's Camel Book forewords, Marcel Gagne's Linux Journal columns, ESR's accessible technical writing.

### Structure

**1. Cold Open** (~200 words)
Scene-setting. Reader boots a terminal, runs `python run.py`, and suddenly they're navigating a chicken across a highway. No X11. No Electron. Just blessed and a dream. Establishes the absurdity and the delight.

**2. The Thesis: Terminals as Canvas** (~400 words)
"The terminal is a canvas, not a cage." Draws from PHILOSOPHY.md principles. Historical context: nethack, the demoscene, ASCII art. Argument that constraints breed creativity — 80x24 is not a limitation, it's a format. References the broader atari-style project as proof.

**3. The Toolkit** (~500 words)
Introduces the two dependencies: blessed for rendering, pygame for joystick input. Explains why blessed over raw curses. Shows the Renderer abstraction (double buffering, color system, aspect ratio correction). Shows InputHandler (unified keyboard/joystick). Code snippets with commentary. References architecture docs: "For the full API, see [the docs]."

**4. Building Claugger** (~1200 words)
The centerpiece. Walks through building the game in stages:
- The chicken sprite and walk cycle (ASCII art design, animation frames)
- The lane system (data structures, scrolling mechanics)
- Collision detection ("when poultry meets Pontiac")
- The egg-laying bonus (random chance, persistence, scoring)
- HUD with personality (puns, death messages, the egg timer)
- Adding to the menu via ContentRegistry ("one import, one MenuItem, done")

Each stage has code snippets — not the full source, but enough to understand the pattern. Readers are directed to the full source on GitHub.

**5. The Bigger Picture** (~400 words)
Zooms out. Shows how Claugger is one of 5+ games in the collection. Explains the modular architecture — every game follows the same pattern. Shows what else is in the project (Pac-Man, Galaga, Grand Prix, Breakout, creative tools, visual demos). Points to the docs for the contributor guide: "clone the repo, add your own game, submit a PR."

**6. Closing** (~200 words)
Why did the chicken cross the terminal? Because the terminal was always a gaming platform — we just forgot. Invitation to try the project, contribute, and remember that the best interfaces are the ones that make you smile. Something about chickens and open source.

### Length

~2500-3500 words total.

### Format

Hugo-compatible markdown with PaperMod front matter. Lives in `docs/blog/` in this repo. Filename uses the publication date (e.g., `2026-03-20-claugger-terminal-arcade.md`). The date is set when the article is finalized, not during drafting.

### References to Docs

The article links to docs at `https://jcaldwell-labs.github.io/docs/atari-style/`:
- Architecture overview (from Section 3)
- API reference (from Section 3)
- "Building Your First Game" tutorial (from Section 4)
- Contributor guide (from Section 5)

---

## 3. Project Documentation

### Location

`docs/site/atari-style/` in this repo. Published to `https://jcaldwell-labs.github.io/docs/atari-style/` via cross-repo dispatch.

### Pages

**1. Getting Started** (`getting-started.md`)
- Prerequisites: Python 3.8+, terminal with color support
- Installation: clone, venv, pip install, run
- First launch: what you'll see (menu description)
- "Try these first" recommendations (Starfield for visuals, Pac-Man for gameplay, Claugger for fun)
- Troubleshooting: common issues (no joystick, terminal too small, missing fonts)

**2. Architecture Overview** (`architecture.md`)
- High-level diagram: core/ modules, demos/ structure, utils/
- Renderer: double-buffered terminal output, color constants, drawing primitives
- InputHandler: keyboard + joystick abstraction, deadzone handling, input types
- Menu + ContentRegistry: how demos are discovered, registered, and launched
- The game loop pattern: `__init__`, `update`, `draw`, `handle_input`, `run`
- Module dependency map

**3. API Reference** (`api-reference.md`)
- `Renderer` class: all public methods with type signatures, parameters, return values, usage examples
- `InputHandler` class: same treatment
- `Color` enum/constants: full list with terminal color codes
- `Config` dataclass: fields, validation rules, defaults
- `ContentRegistry`: registration, discovery, category filtering
- `load_monospace_font()`: utility function signature and usage

**4. Building Your First Game** (`tutorial.md`)
- Step-by-step: create a minimal bouncing ball demo
- Start from the skeleton (class, methods, entry function)
- Add rendering (draw a ball, move it, bounce off walls)
- Add input (arrow keys change direction, ESC to quit)
- Add to menu (import, MenuItem, done)
- Next steps: points to Claugger source as "a more complete example"
- Does NOT duplicate the blog article — this is a from-scratch tutorial for someone who hasn't read the article

**5. Contributor Guide** (`contributing.md`)
- Development setup (venv, pip install -e ., ruff)
- Running tests: `python -m unittest discover -s tests -p "test_*.py" -v`
- Linting: `ruff check atari_style/ tests/`
- Code conventions: constants, imports, type hints, docstrings (adapted from CLAUDE.md for human readers)
- Adding a new demo: step-by-step checklist
- PR process: branch naming, commit messages, pre-commit checklist
- Security requirements: HTML escaping, path validation, streaming

### Format

Hugo-compatible markdown with PaperMod front matter and section weights for navigation ordering.

---

## 4. Publishing Workflow

### Mechanism

Cross-repo `repository_dispatch` from atari-style to jcaldwell-labs.github.io.

### Workflow: atari-style side

File: `.github/workflows/publish-docs.yml`

Triggers on push to `master` when `docs/blog/**` or `docs/site/**` change.

Steps:
1. Checkout atari-style repo
2. Send `repository_dispatch` event to `jcaldwell-labs/jcaldwell-labs.github.io` with payload containing:
   - Source repo and ref
   - Which content changed (blog, docs, or both)

Requires: A repository secret (`DOCS_PUBLISH_TOKEN`) containing a PAT with `repo` scope on the site repo.

### Workflow: site repo side

File: `.github/workflows/receive-content.yml` (in jcaldwell-labs.github.io — **out of scope for this project**; documented here for reference)

Triggers on `repository_dispatch` event of type `publish-atari-style-docs`.

Steps:
1. Checkout site repo
2. Checkout atari-style repo
3. Copy `docs/blog/*.md` to `content/blog/`
4. Copy `docs/site/atari-style/*.md` to `content/docs/atari-style/`
5. Commit and push if changes exist
6. Hugo build triggers automatically via existing site CI

**Note**: This workflow must be created in the jcaldwell-labs.github.io repo separately. It is not a deliverable of this spec — only the atari-style side dispatch workflow is.

### Fallback

If the cross-repo dispatch isn't set up yet (missing PAT), docs can be manually copied. The workflow is a convenience, not a blocker for the content.

---

## 5. PR #143 Disposition

- **Closed** on 2026-03-19 with explanation
- **Backlog issue #161** created to hold the decision on reimplementation
- No further action needed as part of this work

---

## 6. Easter Eggs (Surprise Elements)

Two easter eggs are included in Claugger (detailed in Section 1 above):

1. **The Konami Code** — Up-Up-Down-Down-Left-Right-Left-Right-SELECT-BACK triggers golden rooster mode with temporary invincibility and golden eggs
2. **The Road Scholar** — Complete 3 levels without dying to earn a diploma animation and 5,000 point bonus

These are designed to reward exploration and repeated play while fitting the comedic tone.

---

## Delivery Order (Article-Driven)

1. **Article outline** — nail the narrative arc first
2. **Claugger game** — build the game the article will walk through
3. **Article draft** — write the full article with real code snippets from Claugger
4. **Project docs** — write the 5 doc pages the article references
5. **Publishing workflow** — GitHub Actions for cross-repo dispatch
6. **Integration** — wire Claugger into menu/registry, final testing, commit everything

---

## Success Criteria

- Claugger is playable, fun, and fits the existing game quality bar
- Article reads like authentic late-90s Linux Journal content
- A new developer can go from zero to contributing using only the docs
- Blog post is published to jcaldwell-labs.github.io/blog/
- Docs are published to jcaldwell-labs.github.io/docs/atari-style/
- Issue #144 can be closed or substantially addressed
