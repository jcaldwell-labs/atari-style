# GitHub Copilot Instructions

This file provides guidance to GitHub Copilot when working with code in this repository.

## Project Overview

**atari-style** is a creative pipeline for terminal-native parametric visualization, built through human-AI collaboration, following Unix philosophy principles.

> The terminal is a canvas, not a cage. Parameters are territory to explore, not just settings to configure. Small tools, composed freely.

**Status**: Active development
**Language**: Python 3.8+
**Dependencies**: pygame (joystick), blessed (terminal), moderngl (GPU), Pillow (images), imageio-ffmpeg (video)

### Two Rendering Paths

| Path | Tech | Use Case |
|------|------|----------|
| **Terminal** | blessed + ASCII/ANSI | Interactive games, real-time demos |
| **GPU** | moderngl + GLSL shaders | Video export, high-resolution effects |

### Key Features

- **Classic arcade games**: Pac-Man, Galaga, Grand Prix, Breakout
- **GPU shaders**: Plasma, Mandelbrot, Tunnel, Flux with CRT post-processing
- **Storyboard system**: Keyframe-based video scripting for YouTube export
- **Composite animations**: Effects that modulate each other (Plasma→Lissajous)
- **Full joystick support**: Analog control with keyboard fallback
- **Double-buffered rendering**: 30-60 FPS terminal animation

### Philosophy (see PHILOSOPHY.md)

1. **The Terminal is a Canvas, Not a Cage** - Embrace constraints creatively
2. **Parameters are Territory, Not Settings** - Explore the space of possibilities
3. **Small Tools, Composed Freely** - Unix philosophy via text streams
4. **Show, Don't Document** - Interactive examples over verbose docs
5. **AI-Native Development** - Human-AI collaboration patterns
6. **Play is Serious Work** - Learning through interactive exploration

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

## Unix Composability Philosophy

Every CLI tool in atari-style follows Unix philosophy: small tools that do one thing well and compose freely via text streams.

### Core Principles

- **Text in, text out**: Accept stdin, produce stdout where possible
- **Single responsibility**: Each tool does one thing well
- **Pipeline-friendly**: Tools work standalone AND integrate with pipes
- **Standard formats**: JSON for structured data, plain text for simple output

### CLI Conventions

**Standard Argument Patterns**:
```bash
tool input.json -o output.mp4    # Input from file
tool input.json                  # Output to stdout (text formats)
tool -                          # Read from stdin
cat input.json | tool - | next-tool - > output.txt  # Pipeline
```

**Required Arguments**:
- `-o, --output FILE`: Output file path (stdout for text, required for binary)
- `-h, --help`: Show help message
- `--version`: Show version
- `-v, --verbose`: Increase verbosity
- `-q, --quiet`: Suppress non-essential output

**Exit Codes**:
- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `130`: Interrupted (Ctrl+C)

**Stderr vs Stdout**:
- **stdout**: Primary output (data, results, pipeline content)
- **stderr**: Progress messages, warnings, errors, status updates

```python
# ✅ CORRECT - Data to stdout, status to stderr
print(json.dumps(result))  # stdout - can be piped
print(f"Processing: {filename}", file=sys.stderr)  # stderr - human readable

# ❌ WRONG - Mixing output streams
print(f"Processing: {filename}")  # stdout - breaks pipelines
```

### Rendering Guidelines

**Aspect Ratio Correction**:
Terminal characters are not square (typically 1:2 ratio, width:height). When drawing shapes:

```python
# ✅ CORRECT - Multiply Y coordinates by ~0.5 for circles
y_corrected = int(y * 0.5)
renderer.set_pixel(x, y_corrected, char, color)

# ❌ WRONG - Direct Y mapping produces ovals
renderer.set_pixel(x, y, char, color)  # Circle looks stretched
```

**Double Buffering**:
Always use buffer-based rendering to avoid flicker:

```python
# ✅ CORRECT - Clear buffer, draw, then render
renderer.clear_buffer()
# ... draw operations ...
renderer.render()

# ❌ WRONG - Direct terminal writes cause flicker
print(f"\033[{y};{x}H{char}")  # Flickers during complex draws
```

**Frame Rate Targeting**:
- **30 FPS**: `time.sleep(0.033)` for most animations
- **60 FPS**: `time.sleep(0.016)` for fast-paced games
- Always clean up in `finally` blocks:

```python
try:
    renderer.enter_fullscreen()
    while running:
        # ... game loop ...
        time.sleep(0.033)
finally:
    renderer.exit_fullscreen()
    input_handler.cleanup()
```

---

## GPU Rendering Pipeline (GLSL Shaders)

atari-style has TWO rendering paths: terminal (ASCII) and GPU (GLSL shaders via moderngl).

### Shadertoy-Compatible Uniforms

All effect shaders use Shadertoy-compatible uniform names:

```glsl
// ✅ CORRECT - Standard Shadertoy uniforms
uniform float iTime;           // Shader playback time (seconds)
uniform vec2 iResolution;      // Viewport resolution (pixels)
uniform vec4 iMouse;           // Mouse coordinates (if applicable)
uniform float iFrame;          // Frame number

// Custom uniforms for parametric control
uniform float param1;          // Joystick-controlled parameter
uniform float param2;
uniform float param3;
uniform float param4;
```

### Shader File Organization

```
shaders/
├── effects/                   # Main effect shaders
│   ├── plasma.frag           # Plasma wave interference
│   ├── mandelbrot.frag       # Fractal zoomer
│   ├── tunnel.frag           # Infinite tunnel effect
│   └── fluid.frag            # Fluid dynamics simulation
├── post/                      # Post-processing chain
│   ├── crt.frag              # CRT monitor emulation
│   ├── scanlines.frag        # Scanline overlay
│   └── barrel.frag           # Barrel distortion
└── util/                      # Shared utilities
    └── common.glsl           # Color conversion, noise functions
```

### Writing Effect Shaders

```glsl
// ✅ CORRECT - Proper effect shader structure
#version 330 core

uniform float iTime;
uniform vec2 iResolution;
uniform float param1;  // frequency
uniform float param2;  // amplitude

out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / iResolution.xy;

    // Effect logic here using uv, iTime, and params
    float value = sin(uv.x * param1 + iTime) * param2;

    fragColor = vec4(vec3(value), 1.0);
}
```

### CRT Post-Processing

Apply CRT effects as a post-process pass:

```python
# ✅ CORRECT - Apply CRT after main effect
from atari_style.core.gl import GLRenderer, PostProcessor

renderer = GLRenderer(width=1920, height=1080)
crt = PostProcessor('shaders/post/crt.frag')

frame = renderer.render_effect('plasma', time=t, params=params)
final = crt.apply(frame)  # Add scanlines, curvature, bloom
```

### Composite Animations

Composites modulate one effect with another:

```python
# ✅ CORRECT - Plasma driving Lissajous frequencies
composite = CompositeManager()
composite.set_driver('plasma', output='color_intensity')
composite.set_driven('lissajous', input='frequency', scale=2.0)
```

---

## Storyboard System (Video Scripting)

Storyboards define keyframed animations for video export:

```json
{
  "name": "plasma-intro",
  "duration": 10.0,
  "fps": 30,
  "resolution": [1920, 1080],
  "scenes": [
    {
      "effect": "plasma",
      "start": 0.0,
      "end": 5.0,
      "keyframes": [
        {"time": 0.0, "param1": 1.0, "param2": 0.5},
        {"time": 5.0, "param1": 3.0, "param2": 1.0}
      ],
      "transition": "crossfade"
    }
  ],
  "post_processing": ["crt", "scanlines"]
}
```

### Storyboard CLI

```bash
# Render storyboard to video
python -m atari_style.core.gl.storyboard render storyboard.json -o output.mp4

# Generate contact sheet (frame thumbnails)
python -m atari_style.core.gl.storyboard contact storyboard.json -o sheet.png

# Validate storyboard schema
python -m atari_style.core.gl.storyboard validate storyboard.json
```

---

## Domain Terminology

| Term | Definition |
|------|------------|
| **Flux** | Fluid dynamics-based wave patterns |
| **CRT** | Cathode Ray Tube - retro monitor emulation effect |
| **Composite** | Animation where one effect modulates another |
| **Storyboard** | JSON script defining keyframed video sequences |
| **Parameter space** | The multi-dimensional space of all possible parameter combinations |
| **Screensaver** | Interactive parametric animation with joystick control |
| **Platonic solid** | One of 5 regular polyhedra (tetrahedron, cube, octahedron, dodecahedron, icosahedron) |
| **Lissajous** | Curve formed by parametric equations x=sin(at), y=sin(bt+phase) |
| **Aspect ratio correction** | Compensating for terminal characters being ~2x taller than wide |

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

## Performance Guidelines

### Hot Path Optimization

For render loops and shaders, avoid per-frame allocations:

```python
# ✅ CORRECT - Pre-allocate outside loop
buffer = bytearray(width * height * 4)
params = {'param1': 0.0, 'param2': 0.0}

while running:
    params['param1'] = joystick.get_axis(0)
    params['param2'] = joystick.get_axis(1)
    render_to_buffer(buffer, params)

# ❌ WRONG - Allocating every frame
while running:
    params = {'param1': joystick.get_axis(0)}  # New dict each frame
    buffer = bytearray(width * height * 4)      # New buffer each frame
```

### Resource Loading

Load resources once at startup, not per-frame:

```python
# ✅ CORRECT - Load shaders once
class EffectRenderer:
    def __init__(self):
        self.shader = self._compile_shader('effects/plasma.frag')
        self.texture = self._load_texture('palette.png')

    def render(self, time):
        # Use pre-loaded resources
        pass

# ❌ WRONG - Loading inside render loop
def render(time):
    shader = compile_shader('effects/plasma.frag')  # Recompiles every frame!
```

### Frame Rate Management

Use proper frame timing, not just sleep:

```python
# ✅ CORRECT - Account for frame processing time
TARGET_FRAME_TIME = 1.0 / 60.0

while running:
    frame_start = time.perf_counter()

    update()
    render()

    elapsed = time.perf_counter() - frame_start
    sleep_time = max(0, TARGET_FRAME_TIME - elapsed)
    time.sleep(sleep_time)
```

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
