#!/bin/bash
# Quick test script for Terminal Arcade improvements

echo "════════════════════════════════════════"
echo "  Terminal Arcade - Improvement Tests  "
echo "════════════════════════════════════════"
echo ""

# Activate virtual environment
source venv/bin/activate

echo "Test 1: Import verification..."
python3 -c "
from terminal_arcade.games.pacman import run_pacman
from terminal_arcade.games.mandelbrot import run_mandelbrot
print('✓ All imports successful')
"

if [ $? -eq 0 ]; then
    echo "✓ Imports OK"
else
    echo "✗ Import failed"
    exit 1
fi

echo ""
echo "Test 2: Pac-Man intro check..."
echo "  (Will show intro for 5 seconds)"
python3 -c "
from terminal_arcade.engine.renderer import Renderer
from terminal_arcade.games.pacman.intro import show_intro

renderer = Renderer()
print('Showing Pac-Man intro...')
show_intro(renderer, duration=5.0)
print('✓ Pac-Man intro completed')
"

if [ $? -eq 0 ]; then
    echo "✓ Pac-Man intro OK"
else
    echo "✗ Pac-Man intro failed"
fi

echo ""
echo "Test 3: Mandelbrot color palettes..."
python3 -c "
from terminal_arcade.games.mandelbrot.game import MandelbrotExplorer

explorer = MandelbrotExplorer()
palettes = list(explorer.PALETTES.keys())
print(f'Available palettes: {len(palettes)}')
for p in palettes:
    colors = explorer.PALETTES[p]
    print(f'  - {p}: {len(colors)} colors')

print(f'✓ Default palette: {explorer.current_palette}')
"

echo ""
echo "════════════════════════════════════════"
echo "  All tests complete!                  "
echo "════════════════════════════════════════"
echo ""
echo "To test the full launcher, run:"
echo "  ./run_terminal_arcade.py"
echo ""
