# GPU Visualizer CLI Guide

This guide covers common commands for using the GPU-accelerated visualizers, including interactive shader control, GIF/video export, and storyboard-based animations.

## Quick Reference

| Task | Command |
|------|---------|
| Interactive shader | `python -m atari_style.core.gl.shader_controller` |
| GIF preview | `python -m atari_style.core.gl.gif_preview` |
| Export video | `python -m atari_style.core.gl.video_export` |
| Storyboard render | `python -m atari_style.core.gl.storyboard render <file>` |

## Interactive Shader Controller

Launch an interactive window to explore GPU effects with real-time parameter control.

### Basic Usage

```bash
# Default: plasma effect at 800x600
python -m atari_style.core.gl.shader_controller

# Specific effect
python -m atari_style.core.gl.shader_controller --effect mandelbrot
python -m atari_style.core.gl.shader_controller --effect tunnel
python -m atari_style.core.gl.shader_controller --effect plasma

# Custom resolution
python -m atari_style.core.gl.shader_controller --width 1280 --height 720

# Fullscreen mode
python -m atari_style.core.gl.shader_controller --fullscreen
```

### Available Effects

| Effect | Description |
|--------|-------------|
| `plasma` | Classic plasma animation with color cycling |
| `mandelbrot` | Fractal zoom with configurable iterations |
| `tunnel` | 3D tunnel fly-through effect |

### Controls (Interactive Mode)

| Input | Action |
|-------|--------|
| Left Stick X/Y | Adjust parameters 1-2 |
| Right Stick X/Y | Adjust parameters 3-4 |
| D-Pad Left/Right | Cycle color modes |
| D-Pad Up/Down | Adjust speed |
| Button A (0) | Reset parameters |
| Button B (1) | Exit |
| Arrow Keys | Alternative parameter control |
| ESC | Exit |

## GIF Preview

Create animated GIF previews of shader effects for quick sharing.

### Basic Usage

```bash
# Default GIF (plasma, 3 seconds, 320x240)
python -m atari_style.core.gl.gif_preview

# Specific effect with custom duration
python -m atari_style.core.gl.gif_preview --effect mandelbrot --duration 5

# Higher resolution
python -m atari_style.core.gl.gif_preview --width 480 --height 360 --fps 30

# Output to specific file
python -m atari_style.core.gl.gif_preview -o my-animation.gif
```

### Common Options

| Option | Default | Description |
|--------|---------|-------------|
| `--effect` | plasma | Effect to render |
| `--duration` | 3 | Length in seconds |
| `--fps` | 15 | Frames per second |
| `--width` | 320 | Output width |
| `--height` | 240 | Output height |
| `-o, --output` | preview.gif | Output filename |

### Examples

```bash
# Quick Mandelbrot zoom preview
python -m atari_style.core.gl.gif_preview --effect mandelbrot --duration 10 -o mandelbrot.gif

# High-quality tunnel for sharing
python -m atari_style.core.gl.gif_preview --effect tunnel --width 640 --height 480 --fps 24 -o tunnel.gif
```

## Video Export

Export high-quality MP4 videos with GPU rendering.

### Basic Usage

```bash
# List available formats
python -m atari_style.core.gl.video_export --list-formats

# Export YouTube Shorts (1080x1920, 30s max)
python -m atari_style.core.gl.video_export --shorts -o output.mp4

# Export standard 1080p
python -m atari_style.core.gl.video_export --format youtube_1080p --duration 60 -o output.mp4

# Export with specific effect
python -m atari_style.core.gl.video_export --effect plasma_lissajous --duration 30 -o composite.mp4
```

### Video Format Presets

| Format | Resolution | Aspect | Max Duration |
|--------|------------|--------|--------------|
| `youtube_shorts` | 1080x1920 | 9:16 | 60s |
| `tiktok` | 1080x1920 | 9:16 | 180s |
| `instagram_reels` | 1080x1920 | 9:16 | 90s |
| `instagram_story` | 1080x1920 | 9:16 | 15s |
| `instagram_square` | 1080x1080 | 1:1 | 60s |
| `youtube_1080p` | 1920x1080 | 16:9 | unlimited |
| `youtube_720p` | 1280x720 | 16:9 | unlimited |
| `youtube_4k` | 3840x2160 | 16:9 | unlimited |

### Common Options

| Option | Description |
|--------|-------------|
| `--format` | Video format preset |
| `--shorts` | Shortcut for `--format youtube_shorts` |
| `--duration` | Video length in seconds |
| `--fps` | Frames per second (default: 30) |
| `--effect` | Effect or composite to render |
| `-o, --output` | Output filename |

## Storyboard System

Create planned animations with keyframes for precise control over timing and parameters.

### Workflow

1. **Create** storyboard JSON with keyframes
2. **Validate** to check for errors
3. **Preview** to export keyframe PNGs
4. **Grid** to create contact sheet for review
5. **Render** final video

### Commands

```bash
# Validate storyboard syntax
python -m atari_style.core.gl.storyboard validate storyboards/plasma-lissajous-short.json

# Preview keyframes as individual PNGs
python -m atari_style.core.gl.storyboard preview storyboards/plasma-lissajous-short.json -o keyframes/

# Generate contact sheet (all keyframes in one image)
python -m atari_style.core.gl.storyboard grid storyboards/plasma-lissajous-short.json -o contact.png

# Render full video with interpolation
python -m atari_style.core.gl.storyboard render storyboards/plasma-lissajous-short.json -o output.mp4
```

### Storyboard JSON Format

```json
{
  "version": "1.0",
  "title": "My Animation",
  "description": "Optional description",
  "composite": "plasma_lissajous",
  "format": "youtube_shorts",
  "fps": 30,
  "transitions": "ease_in_out",
  "keyframes": [
    {
      "id": "intro",
      "time": 0.0,
      "params": [0.1, 0.3, 0.5, 0.7],
      "note": "Opening state"
    },
    {
      "id": "peak",
      "time": 30.0,
      "params": [0.5, 0.7, 0.9, 1.0],
      "note": "Maximum intensity"
    }
  ]
}
```

### Available Composites

| Composite | Parameters |
|-----------|------------|
| `plasma_lissajous` | plasma_freq, liss_base_freq, modulation, trail |
| `flux_spiral` | wave_freq, base_rotation, modulation, num_spirals |
| `lissajous_plasma` | liss_speed, plasma_intensity, curve_influence, color_shift |

### Transition Types

| Type | Description |
|------|-------------|
| `linear` | Straight interpolation |
| `ease_in_out` | Smooth acceleration/deceleration |
| `step` | Jump to next values (no interpolation) |

## Composite Animations

Run composite animations that combine multiple effects.

### Interactive Mode

```bash
# Run composite manager interactively
python -m atari_style.core.gl.composite_manager

# Specific composite
python -m atari_style.core.gl.composite_manager --composite plasma_lissajous
```

### Export Composites

```bash
# Export composite as video
python -m atari_style.core.gl.video_export --effect plasma_lissajous --duration 30 -o composite.mp4

# Export as GIF
python -m atari_style.core.gl.gif_preview --effect plasma_lissajous --duration 5 -o composite.gif
```

## Troubleshooting

### "No module named moderngl"

Install the GPU rendering dependencies:

```bash
pip install moderngl pygame pillow imageio imageio-ffmpeg
```

### "OpenGL context creation failed"

- Ensure you have a GPU with OpenGL 3.3+ support
- Update graphics drivers
- On WSL2, ensure GPU passthrough is configured

### Video export produces no output

- Check that FFmpeg is installed and in PATH
- Verify output directory exists and is writable
- Check console for error messages

### Poor performance

- Reduce resolution with `--width` and `--height`
- Lower FPS with `--fps`
- Close other GPU-intensive applications

## Related Documentation

- [Joystick Controls](../joystick-controls.md) - Controller button mappings
- [Architecture](../architecture.md) - System design overview
- [Shader Roadmap](../shader-roadmap.md) - GPU implementation details
- [Storyboards README](../../storyboards/README.md) - Storyboard format reference
