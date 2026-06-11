#!/usr/bin/env python3
"""Add signal handlers to all game run() methods.

Legacy one-off script; the package it targeted is archived at
docs/archive/terminal-arcade-legacy/.
"""

import re

games = [
    'docs/archive/terminal-arcade-legacy/games/pacman/game.py',
    'docs/archive/terminal-arcade-legacy/games/galaga/game.py',
    'docs/archive/terminal-arcade-legacy/games/grandprix/game.py',
    'docs/archive/terminal-arcade-legacy/games/breakout/game.py',
    'docs/archive/terminal-arcade-legacy/demos/starfield/game.py',
    'docs/archive/terminal-arcade-legacy/demos/platonic/game.py',
    'docs/archive/terminal-arcade-legacy/tools/asciipainter/game.py',
]

for filepath in games:
    print(f"Processing {filepath}...")

    with open(filepath, 'r') as f:
        content = f.read()

    # Check if already has handler
    if 'signal.signal(signal.SIGINT' in content:
        print(f"  ✓ Already has signal handler")
        continue

    # Add signal handler after "def run(self):"
    # Pattern: def run(self):\n        """..."""\n        try:
    pattern = r'(def run\(self\):)\n(        """[^"]*""")\n(        try:)'
    replacement = r'\1\n\2\n        def signal_handler(sig, frame):\n            self.running = False\n        old_handler = signal.signal(signal.SIGINT, signal_handler)\n\n\3'

    new_content = re.sub(pattern, replacement, content)

    # Add signal restore in finally block
    pattern2 = r'(finally:)\n(            self\.renderer\.exit_fullscreen\(\))\n(            self\.input_handler\.cleanup\(\))'
    replacement2 = r'\1\n\2\n\3\n            signal.signal(signal.SIGINT, old_handler)'

    new_content = re.sub(pattern2, replacement2, new_content)

    # Alternative pattern if no input_handler
    if 'signal.signal(signal.SIGINT, old_handler)' not in new_content:
        pattern3 = r'(finally:)\n(            self\.renderer\.exit_fullscreen\(\))'
        replacement3 = r'\1\n\2\n            signal.signal(signal.SIGINT, old_handler)'
        new_content = re.sub(pattern3, replacement3, new_content)

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"  ✓ Added signal handler")
    else:
        print(f"  ⚠ Pattern not found, needs manual edit")

print("\nDone!")
