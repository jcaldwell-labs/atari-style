# Educational Video Rendering Pattern

This document describes the pattern for creating educational math visualization videos in atari-style.

## Directory Structure

```
atari_style/demos/visualizers/educational/
├── __init__.py                 # Module exports
├── lissajous_explorer.py       # Interactive terminal demo
├── lissajous_terminal_gif.py   # CLI video/GIF renderer
└── unit_circle_educational.py  # Educational video renderer
```

## Pattern Components

### 1. Frame Generator

Yields PIL Image objects for each frame:

```python
def render_segment(renderer, duration: float, fps: int = 30) -> List[Image.Image]:
    frames = []
    total_frames = int(duration * fps)

    for frame in range(total_frames):
        t = frame / fps
        img, draw = renderer.new_frame()
        # Draw frame content using draw primitives
        frames.append(img)

    return frames
```

### 2. Video Renderer (ffmpeg subprocess)

Encodes frames to MP4:

```python
def encode_video(frames_dir: str, output_path: str, fps: int):
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', f'{frames_dir}/frame_%05d.png',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        output_path
    ]
    subprocess.run(cmd, check=True)
```

### 3. Educational Slides (Ghost Typing)

Terminal-style text reveals:

```python
def render_ghost_typing(draw, lines: List[dict], cursor_visible: bool):
    for line in lines:
        text = line['text'][:line.get('chars_shown', len(line['text']))]
        color = COLOR_RGB[line.get('type', 'command')]
        draw.text((x, y), text, font=font, fill=color)
```

### 4. Camera Effects

Pan, zoom, rotate transformations:

```python
def apply_camera(img: Image.Image, zoom: float, pan: Tuple[float, float]):
    # Scale and translate image
    pass
```

## CLI Pattern

All educational visualizers follow this CLI pattern:

```bash
# Video export
python -m atari_style.demos.visualizers.educational.unit_circle_educational

# GIF with options
python -m atari_style.demos.visualizers.educational.lissajous_terminal_gif \
    --sweep circle trefoil -o lissajous.gif

# Interactive mode
python -m atari_style.demos.visualizers.educational.lissajous_explorer
```

## Integration with Main Menu

Educational demos are accessible from the main menu via `MenuItem`:

```python
from .demos.visualizers.educational import run_lissajous_explorer

menu_items.append(MenuItem("Lissajous Explorer", run_lissajous_explorer))
```

## Memory Management

For long videos, save frames to disk incrementally:

```python
def _save_segment_frames(frames: List[Image.Image], frames_dir: str, start_index: int) -> int:
    for i, frame in enumerate(frames):
        frame_path = os.path.join(frames_dir, f"frame_{start_index + i:05d}.png")
        frame.save(frame_path)
    return start_index + len(frames)
```

## Related Issues

- #28 - Educational Video System: Architecture & Directory Structure
- #29 - Lissajous Educational Video Series
- #30 - Video Scripting CLI Framework
- #31 - GPU-Accelerated Educational Video Rendering
