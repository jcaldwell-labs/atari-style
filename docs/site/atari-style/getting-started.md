---
title: "Getting Started with atari-style"
weight: 1
---

# Getting Started with atari-style

atari-style is a collection of terminal-based arcade games, creative tools, and visual demos inspired by classic Atari aesthetics. Everything runs in your terminal using ASCII and ANSI graphics.

## Prerequisites

- **Python 3.8 or newer** — check with `python3 --version`
- **A terminal with 256-color support** — most modern terminals qualify (iTerm2, GNOME Terminal, Windows Terminal, Alacritty, kitty)
- **Terminal size of at least 80x24** — larger is better; many demos benefit from a full-screen terminal
- **Optional**: A USB gamepad or joystick for full analog control

## Installation

```bash
# Clone the repository
git clone https://github.com/jcaldwell-labs/atari-style.git
cd atari-style

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Dependencies installed:

| Package | Purpose |
|---|---|
| `pygame>=2.5.0` | Joystick input handling |
| `blessed>=1.20.0` | Terminal rendering and control |
| `Pillow>=10.0.0` | Screenshot export (optional feature) |
| `moderngl>=5.8.0` | GPU-accelerated demos |
| `numpy>=1.20.0` | Numerical operations for GL demos |

## First Launch

```bash
python run.py
```

This opens the interactive menu. Navigate with arrow keys (or WASD), press Enter or Space to launch a demo, and press Escape or Q to return to the menu.

You can also launch individual demos directly:

```bash
# Games
python -c "from atari_style.demos.games.pacman import run_pacman; run_pacman()"
python -c "from atari_style.demos.games.galaga import run_galaga; run_galaga()"
python -c "from atari_style.demos.games.claugger import run_claugger; run_claugger()"

# Visual demos
python -c "from atari_style.demos.visualizers.starfield import run_starfield; run_starfield()"
```

## Try These First

**For visuals**: Start with **Starfield**. It demonstrates the rendering engine at its best — 3D parallax layers, nebulae, warp tunnel, and asteroid mode. Use the joystick or left/right arrows to drift sideways.

**For gameplay**: Try **Pac-Man**. It's the most complete game in the collection, with four ghost AI personalities, power-ups, and level progression that gives you an immediate sense of what the engine can do.

**For something different**: **Claugger** is a Frogger tribute where you guide a chicken across traffic. It's the most recently added game and a good example of how to build a new demo from scratch.

**For creative work**: **ASCII Painter** is a full drawing program with six tools, undo/redo, and file export. Press H in-game for the help overlay.

## Controls

All demos respond to both keyboard and joystick:

| Keyboard | Joystick | Action |
|---|---|---|
| Arrow keys or WASD | Left analog stick | Navigate / Move |
| Enter or Space | Button 0 (A/Cross) | Select / Fire / Action |
| Escape or Q | Button 1 (B/Circle) | Back / Exit |
| X | — | Force quit |

## Troubleshooting

**No joystick detected**

The joystick is optional. The message "No joystick detected. Using keyboard only." at startup is informational, not an error. If you plug in a joystick mid-session, the input handler attempts reconnection automatically (roughly once per second).

**Terminal too small**

Some demos check terminal dimensions and may render incorrectly in small windows. Maximize your terminal or set it to at least 120x40 for the best experience. Grand Prix and the 3D demos benefit most from extra space.

**Missing fonts for screenshots**

Screenshot export (`save_screenshot`) uses Pillow to render a PNG. It looks for DejaVu Sans Mono, Liberation Mono, or Ubuntu Mono. If none are found it falls back to PIL's built-in bitmap font. Install a font package for better results:

```bash
# Debian/Ubuntu
sudo apt install fonts-dejavu

# Fedora
sudo dnf install dejavu-sans-mono-fonts
```

**Colors look wrong**

Make sure your terminal is set to use 256-color or truecolor mode. For bash/zsh, ensure `$TERM` is set to `xterm-256color` or similar:

```bash
export TERM=xterm-256color
```

**Import errors on startup**

Confirm you activated the virtual environment and installed requirements:

```bash
source venv/bin/activate
pip install -r requirements.txt
```
