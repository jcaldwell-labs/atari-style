# Storyboards

This directory contains storyboard definitions for video animations.

## What is a Storyboard?

A storyboard is a JSON file that defines keyframes with parameters for GPU-rendered composite animations. This enables:

1. **Planning**: Define keyframes with specific parameters and timing
2. **Review**: Preview individual frames before full render
3. **Iteration**: Adjust timing and transitions via JSON edits
4. **Documentation**: Describe creative intent with notes

## Quick Start

```bash
# Validate a storyboard
python -m atari_style.core.gl.storyboard validate storyboards/plasma-lissajous-short.json

# Preview keyframes as PNGs
python -m atari_style.core.gl.storyboard preview storyboards/plasma-lissajous-short.json -o keyframes/

# Generate contact sheet for PR review
python -m atari_style.core.gl.storyboard grid storyboards/plasma-lissajous-short.json -o contact.png

# Render full video with interpolation
python -m atari_style.core.gl.storyboard render storyboards/plasma-lissajous-short.json -o output.mp4
```

## Storyboard Format

```json
{
  "version": "1.0",
  "title": "My Animation",
  "description": "Optional description",
  "composite": "plasma_lissajous",
  "format": "youtube_shorts",
  "fps": 30,
  "transitions": "ease_in_out",
  "default_color_mode": 0,
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

## Fields

### Required
- `title`: Human-readable name
- `composite`: Default composite animation (`plasma_lissajous`, `flux_spiral`, `lissajous_plasma`)
- `keyframes`: Array of keyframe objects

### Optional
- `version`: Schema version (default: "1.0")
- `description`: Longer description
- `format`: Video format preset (default: "youtube_shorts")
- `fps`: Frames per second (default: 30)
- `transitions`: Interpolation type (default: "linear")
- `default_params`: Default parameters for keyframes
- `default_color_mode`: Default color mode (default: 0)

### Keyframe Fields
- `id`: Unique identifier (required)
- `time`: Time in seconds (required)
- `params`: 4-tuple of parameters (inherits default if omitted)
- `composite`: Override composite for this keyframe
- `color_mode`: Override color mode
- `note`: Human-readable description

## Transition Types

- `linear`: Straight interpolation between keyframes
- `ease_in_out`: Smooth acceleration/deceleration (3t² - 2t³)
- `step`: Jump to next keyframe values (no interpolation)

## Video Format Presets

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

## Available Composites

| Composite | Parameters |
|-----------|------------|
| `plasma_lissajous` | plasma_freq, liss_base_freq, modulation, trail |
| `flux_spiral` | wave_freq, base_rotation, modulation, num_spirals |
| `lissajous_plasma` | liss_speed, plasma_intensity, curve_influence, color_shift |

## Example Workflow

1. Create storyboard JSON with keyframes
2. Run `validate` to check for errors
3. Run `preview` to export keyframe PNGs
4. Run `grid` to create contact sheet for review
5. Submit PR with storyboard + contact sheet
6. After approval, run `render` for final video
