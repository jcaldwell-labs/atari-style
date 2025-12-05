# GitHub Copilot Instructions

This file provides guidance to GitHub Copilot when working with code in this repository.

## Project Overview

Atari-style is a comprehensive collection of terminal-based interactive games, creative tools, and visual demos inspired by classic Atari aesthetics. Features playable arcade experiences using ASCII/ANSI terminal graphics with full joystick and keyboard support.

**Status**: Active development
**Language**: Python 3.8+
**Dependencies**: pygame (joystick), blessed (terminal rendering), moderngl (GPU shaders)

Key features:
- Classic arcade games: Pac-Man, Galaga, Grand Prix, Breakout
- ASCII art painting tool with 6 drawing tools
- Visual demos: Starfield, Screen Saver, Platonic Solids, Flux Control
- GPU-accelerated shaders with CRT post-processing
- Educational video export system for YouTube content
- Full joystick support with keyboard fallback
- Double-buffered rendering for smooth 30-60 FPS animation

## Build System

```bash
# Setup virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .

# Run the application
python run.py
# or
python -m atari_style.main

# Run tests
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## ⚠️ CRITICAL: Security Requirements

**ALL code must follow these security rules. These are non-negotiable.**

### HTML Output - Always Escape User Data

When generating HTML that includes ANY external data (filenames, JSON content, user input):

```python
import html

# ✅ CORRECT - Always escape
filename_safe = html.escape(filename)
json_safe = html.escape(json.dumps(data))
effect_safe = html.escape(scene.get('effect', 'unknown'))

# ❌ WRONG - Never do this
f'<h2>{filename}</h2>'  # XSS vulnerability
f'<pre>{json_str}</pre>'  # XSS vulnerability
```

### Path Traversal - Validate All File Paths

When serving files from user-provided paths:

```python
# ✅ CORRECT - Validate path is within allowed directory
requested_path = (base_dir / user_path).resolve()
allowed_dir = base_dir.resolve()

if not str(requested_path).startswith(str(allowed_dir)):
    return error_forbidden()

# ❌ WRONG - Direct path construction
file_path = base_dir / user_path  # Path traversal vulnerability
```

### File Operations - Stream Large Files

When serving media files:

```python
# ✅ CORRECT - Stream in chunks
CHUNK_SIZE = 8192
with open(path, 'rb') as f:
    while chunk := f.read(CHUNK_SIZE):
        self.wfile.write(chunk)

# ❌ WRONG - Load entire file into memory
content = open(path, 'rb').read()  # Memory exhaustion for large files
```

---

## Code Quality Standards

### Constants - No Magic Numbers

Extract numeric values as named constants:

```python
# ✅ CORRECT
DIGITAL_THRESHOLD = 0.5
DEADZONE = 0.1
MAX_RETRIES = 3

if value > DIGITAL_THRESHOLD:
    return 1.0

# ❌ WRONG
if value > 0.5:  # Magic number
    return 1.0
```

### Imports - Remove Unused

Only import what you use:

```python
# ✅ CORRECT - Only used imports
from typing import Dict, List, Optional

# ❌ WRONG - Unused imports
from typing import Dict, List, Optional, Tuple  # Tuple not used
from dataclasses import dataclass, asdict  # asdict not used
```

### Type Hints - Always Include

All public functions must have type hints:

```python
# ✅ CORRECT
def process_file(path: Path, options: Dict[str, Any]) -> Optional[MediaFile]:
    ...

# ❌ WRONG
def process_file(path, options):  # Missing type hints
    ...
```

### Docstrings - Document Public APIs

```python
# ✅ CORRECT
def scan_directory(path: Path, recursive: bool = True) -> List[MediaFile]:
    """Scan directory for media files.

    Args:
        path: Directory to scan
        recursive: Whether to scan subdirectories

    Returns:
        List of MediaFile objects found
    """

# ❌ WRONG - No docstring
def scan_directory(path: Path, recursive: bool = True) -> List[MediaFile]:
    files = []
    ...
```

---

## Testing Standards

### Test Coverage Requirements

- **Core modules**: Minimum 80% coverage
- **CLI tools**: Minimum 70% coverage
- **Integration tests**: Required for all public APIs

### Test File Naming

Test data should match what's being tested:

```python
# ✅ CORRECT - Consistent test data
mf = MediaFile(
    path=Path('/test/video.mp4'),
    filename='video.mp4',
    file_type='video',
    extension='.mp4',
)

# ❌ WRONG - Inconsistent (audio file with video type)
mf = MediaFile(
    path=Path('/test/audio.mp3'),
    filename='audio.mp3',
    file_type='video',  # Doesn't match filename
)
```

### Integration Tests Required

When testing modes/features, include integration tests:

```python
# ✅ CORRECT - Unit test + Integration test
def test_quantize_positive(self):
    """Unit test for quantization."""
    self.assertEqual(recorder._quantize(0.75), 1.0)

def test_digital_mode_integration(self):
    """Integration test - digital mode quantizes during recording."""
    recorder = InputRecorder(duration=0.1, fps=10, digital=True)
    # Mock joystick returning 0.75
    # Verify recorded keyframe has 1.0, not 0.75

# ❌ WRONG - Only unit tests, no integration
def test_quantize(self):
    """Only tests internal method, not actual usage."""
```

### Edge Cases to Test

Always include tests for:
- Empty inputs / no data
- Missing dependencies (e.g., no joystick connected)
- Error conditions
- Boundary values

---

## Architecture

### Directory Structure

```
atari-style/
├── atari_style/
│   ├── core/                  # Core framework
│   │   ├── renderer.py        # Terminal rendering
│   │   ├── input_handler.py   # Input abstraction
│   │   ├── demo_video.py      # Video export
│   │   ├── overlay.py         # Text overlays
│   │   └── gl/                # GPU rendering
│   ├── demos/                 # Games and demos
│   │   ├── games/             # Arcade games
│   │   ├── visualizers/       # Visual effects
│   │   └── tools/             # Utilities
│   ├── preview/               # Web preview server
│   └── plugins/               # Plugin system
├── tests/                     # Test files
├── storyboards/               # JSON storyboard files
├── baselines/                 # Visual regression baselines
└── docs/                      # Documentation
```

### Core Components

**Renderer** (`core/renderer.py`):
- Double-buffered terminal rendering
- Color constants: RED, GREEN, BLUE, YELLOW, MAGENTA, CYAN, WHITE, BRIGHT_*
- Methods: `set_pixel()`, `draw_text()`, `draw_box()`, `render()`

**InputHandler** (`core/input_handler.py`):
- Unified keyboard and joystick input
- Auto-joystick detection with deadzone handling
- Input types: UP, DOWN, LEFT, RIGHT, SELECT, BACK, QUIT

**Video Export** (`core/demo_video.py`, `core/gl/video_export.py`):
- Frame-by-frame video generation
- Support for MP4, GIF, PNG sequences
- Resolution presets and CRT effects

---

## Common Development Tasks

### Adding a New Demo

1. Create file in `atari_style/demos/` (or appropriate subdirectory)
2. Follow the game loop pattern:

```python
class MyDemo:
    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.running = True

    def run(self):
        try:
            self.renderer.enter_fullscreen()
            while self.running:
                self.handle_input()
                self.update()
                self.renderer.clear_buffer()
                self.draw()
                self.renderer.render()
                time.sleep(0.033)  # ~30 FPS
        finally:
            self.renderer.exit_fullscreen()
            self.input_handler.cleanup()

def run_my_demo():
    demo = MyDemo()
    demo.run()
```

3. Add to menu in `atari_style/main.py`
4. Add tests in `tests/test_my_demo.py`

### Adding a New CLI Tool

1. Create module with `main()` function using argparse
2. Add `__main__.py` entry point
3. Include `--help` documentation
4. Add unit tests for argument parsing
5. Add integration tests for actual functionality

---

## Before Committing (Required Steps)

```bash
# 1. Lint check
ruff check atari_style/ tests/

# 2. Run tests
python -m unittest discover -s tests -p "test_*.py" -v

# 3. Verify no unused imports
# Check for: Tuple, asdict, or other imports not used

# 4. Security check
# Search for: html.escape, .resolve(), path validation
```

---

## Pull Request Standards

**Required PR format:**
```markdown
## Summary
[2-3 sentences describing what and why]

Fixes #[issue-number]

## Changes
- [Actual change 1]
- [Actual change 2]

## Security Checklist
- [ ] All HTML output uses html.escape() for user data
- [ ] File paths validated against path traversal
- [ ] Large files streamed, not loaded into memory

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests for new features
- [ ] Edge cases covered (empty, error, boundary)
- [ ] All tests pass

## Type
- [ ] New feature | Bug fix | Refactor | Docs | CI
```

---

## Quick Reference: Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| `f'<div>{user_data}</div>'` | `f'<div>{html.escape(user_data)}</div>'` |
| `path = base / user_input` | Validate with `.resolve()` and prefix check |
| `content = file.read()` | Stream with chunked reads for large files |
| `if value > 0.5:` | `if value > THRESHOLD_CONSTANT:` |
| `from typing import X, Y, Z` | Remove unused type imports |
| Test only unit, not integration | Add integration tests for features |
| Inconsistent test fixtures | Match test data types to what's being tested |
