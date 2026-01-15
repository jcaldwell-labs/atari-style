# jcaldwell-labs Ecosystem Integration

This document defines how jcaldwell-labs projects work together, documenting shared patterns, integration points, and recommended development workflows.

## Project Dependency Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        jcaldwell-labs Ecosystem                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────┐         ┌───────────────────┐                       │
│  │   atari-style     │         │    boxes-live     │                       │
│  │  ─────────────    │         │   ───────────     │                       │
│  │  Terminal games,  │ ──────► │  Terminal canvas  │                       │
│  │  visualizers &    │ storyboard2canvas           │                       │
│  │  creative tools   │ ◄────── │  with joystick    │                       │
│  │                   │ shared controls              │                       │
│  └───────────────────┘         └───────────────────┘                       │
│          │                              │                                   │
│          │                              │                                   │
│          └──────────┬───────────────────┘                                   │
│                     │                                                       │
│                     ▼                                                       │
│          ┌───────────────────┐                                             │
│          │  Shared Patterns  │                                             │
│          │  ───────────────  │                                             │
│          │  • Joystick ctrl  │                                             │
│          │  • Unix pipelines │                                             │
│          │  • Terminal UI    │                                             │
│          │  • AI-native dev  │                                             │
│          └───────────────────┘                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Project Overview

| Project            | Purpose                                               | Status     |
| ------------------ | ----------------------------------------------------- | ---------- |
| **atari-style**    | Terminal games, visualizers, and creative tools       | Active     |
| **boxes-live**     | Terminal canvas with joystick support                 | Active     |
| **terminal-stars** | Original starfield project (evolved into atari-style) | Historical |

### Data Flow

```
atari-style                    boxes-live
─────────────────────────      ─────────────────────────

 Storyboard JSON  ──────────►  BOXES_CANVAS_V1 format
 (keyframes,                   (boxes, positions,
  parameters,                   colors, content)
  timing)

 Control scheme   ◄──────────►  Control scheme
 (Button 0 = A,                (Button 0 = A,
  Button 1 = B,                 Button 1 = B,
  stick = move)                 stick = pan)
```

## Shared Patterns

### 1. Unified Joystick Control Scheme

All jcaldwell-labs projects share a consistent control mapping for predictable user experience:

| Control          | Function           | atari-style           | boxes-live                  |
| ---------------- | ------------------ | --------------------- | --------------------------- |
| **Left Stick**   | Primary navigation | Movement / Parameters | Pan canvas / Move selection |
| **Button 0 (A)** | Primary action     | Select / Fire         | Select box / Confirm        |
| **Button 1 (B)** | Cancel / Back      | Back / Cancel         | Deselect / Exit focus       |
| **Button 2 (X)** | Secondary action   | Tool cycle            | Quick action                |
| **Button 3 (Y)** | Toggle help        | Help overlay          | Help overlay                |
| **D-Pad**        | Fine control       | Alt navigation        | Fine movement               |

**Technical Implementation:**

```python
# Shared constants (15% deadzone)
DEADZONE = 0.15
DIGITAL_THRESHOLD = 0.5

# Edge detection pattern
if is_pressed and not was_pressed:
    handle_button_press()
```

See [docs/joystick-controls.md](./joystick-controls.md) for complete specification.

### 2. Unix Pipeline Composability

Projects follow Unix philosophy for tool composition:

**Required CLI Conventions:**

```bash
# Input from file
tool input.json -o output.mp4

# Output to stdout (text formats)
tool input.json

# Input from stdin
tool -
cat input.json | tool -

# Full pipeline
cat params.json | tool - | next-tool - > output.txt
```

**Active Pipelines:**

```bash
# Storyboard visualization pipeline
python -m atari_style.connectors.storyboard2canvas storyboard.json | boxes-live --load -

# Frame export pipeline
python -m atari_style.core.gl.video_export flux_spiral --frames ./out/
convert ./out/*.png -delay 3 animation.gif

# Batch conversion
ls storyboards/*.json | while read f; do
    python -m atari_style.connectors.storyboard2canvas "$f" > "${f%.json}.canvas"
done
```

### 3. Terminal UI Patterns

Consistent terminal rendering approach:

| Pattern                     | Description                               |
| --------------------------- | ----------------------------------------- |
| **Double buffering**        | Buffer-based rendering to prevent flicker |
| **Aspect ratio correction** | Y × 0.5 for circles in character cells    |
| **Box-drawing characters**  | `─│┌┐└┘├┤┬┴┼` for borders                 |
| **Block characters**        | `▀▄█▌▐░▒▓` for graphics                   |
| **Color palette**           | Standard + bright variants (14 colors)    |

### 4. AI-Native Development

All projects are designed for human-AI collaboration:

| File                        | Purpose                                   |
| --------------------------- | ----------------------------------------- |
| `CLAUDE.md`                 | AI assistant context for development      |
| `llms.txt`                  | AI discoverability (12 required sections) |
| `.github/ORG-GUIDELINES.md` | Organization-wide standards               |
| `PHILOSOPHY.md`             | Core principles guiding decisions         |

## Integration Points

### storyboard2canvas Connector

**Location:** `atari_style/connectors/storyboard2canvas.py`

Converts atari-style storyboard JSON to boxes-live canvas format:

```bash
# Direct pipeline
python -m atari_style.connectors.storyboard2canvas story.json | boxes-live --load -

# Save to file
python -m atari_style.connectors.storyboard2canvas story.json -o canvas.txt
```

**Input Format (Storyboard JSON):**

```json
{
  "title": "My Animation",
  "composite": "plasma_lissajous",
  "fps": 30,
  "keyframes": [
    {
      "id": "kf_intro",
      "time": 0.0,
      "params": [0.3, 0.5, 0.2, 0.1],
      "note": "Opening"
    },
    {
      "id": "kf_peak",
      "time": 5.0,
      "params": [0.8, 0.9, 0.7, 0.6],
      "note": "Climax"
    }
  ]
}
```

**Output Format (BOXES_CANVAS_V1):**

```
BOXES_CANVAS_V1
2000 800
3
1 80 50 38 8 0 6
My Animation
4
Composite: plasma_lissajous
Format: video
FPS: 30
Keyframes: 2
...
```

**Color Mapping:**
| Parameter Intensity | Color | Meaning |
|---------------------|-------|---------|
| `< 0.3` (low) | Blue (4) | Calm |
| `0.3-0.5` (medium) | Green (2) | Balanced |
| `0.5-0.7` (high) | Yellow (3) | Energetic |
| `> 0.7` (peak) | Red (1) | Intense |

### Text Interchange Formats

| Format         | Extension       | Usage                                    |
| -------------- | --------------- | ---------------------------------------- |
| Storyboard     | `.json`         | Animation keyframes and parameters       |
| Parameters     | `.json`         | Configuration and settings               |
| Canvas         | `.canvas`       | boxes-live box layouts (BOXES_CANVAS_V1) |
| Frame Manifest | `manifest.json` | Video export frame sequences             |

## Recommended Development Workflow

### Setting Up for Cross-Project Development

```bash
# Clone both projects in same parent directory
cd ~/projects
git clone https://github.com/jcaldwell-labs/atari-style.git
git clone https://github.com/jcaldwell-labs/boxes-live.git

# Set up virtual environments
cd atari-style && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cd ../boxes-live && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Testing Integration

```bash
# Verify storyboard connector
cd ~/projects/atari-style
python -m atari_style.connectors.storyboard2canvas storyboards/plasma-lissajous-short.json

# Test full pipeline (requires boxes-live)
python -m atari_style.connectors.storyboard2canvas storyboards/plasma-lissajous-short.json | \
    ../boxes-live/venv/bin/python -m boxes_live --load -
```

### Adding New Integration Points

1. **Design the interface** - Define input/output formats (prefer JSON/text)
2. **Create connector module** - Add to `atari_style/connectors/`
3. **Follow CLI conventions** - Support `-` for stdin, `-o` for output file
4. **Document the pipeline** - Update this file and README
5. **Test bidirectionally** - Verify data flows correctly both ways

### Contribution Checklist

When contributing cross-project features:

- [ ] Follows shared control scheme (joystick mapping)
- [ ] Uses text-based interchange formats (JSON, BOXES_CANVAS_V1)
- [ ] Supports Unix pipeline conventions (`-` for stdin)
- [ ] Updates both project READMEs with integration docs
- [ ] Tests pipeline end-to-end
- [ ] Updates `llms.txt` in both projects for AI discoverability

## Future Integration Opportunities

### Planned Connectors

| Source                  | Target      | Purpose                                 |
| ----------------------- | ----------- | --------------------------------------- |
| atari-style screenshots | boxes-live  | Import ASCII art as box content         |
| boxes-live exports      | atari-style | Load canvas layouts as overlays         |
| Parameter presets       | Both        | Shared parameter format for visualizers |

### Shared Libraries (Potential)

Consider extracting into shared packages:

- `jcaldwell-input` - Unified joystick/keyboard handling
- `jcaldwell-terminal` - Common terminal rendering primitives
- `jcaldwell-formats` - Shared format parsers/generators

## Reference

### Related Documentation

- [PHILOSOPHY.md](../PHILOSOPHY.md) - Core design principles
- [.github/ORG-GUIDELINES.md](../.github/ORG-GUIDELINES.md) - Organization standards
- [docs/joystick-controls.md](./joystick-controls.md) - Complete control specification
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guidelines

### External Links

- [boxes-live repository](https://github.com/jcaldwell-labs/boxes-live)
- [jcaldwell-labs organization](https://github.com/jcaldwell-labs)

---

**Last Updated:** 2026-01-14
**Applies To:** All jcaldwell-labs projects with cross-project integration
