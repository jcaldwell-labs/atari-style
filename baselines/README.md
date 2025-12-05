# Visual Regression Test Baselines

This directory contains reference images for visual regression testing.

## Structure

```
baselines/
├── README.md              # This file
├── <demo_name>/           # Per-demo baseline directory
│   ├── metadata.json      # Test configuration
│   ├── frame_0000.png     # Baseline frames
│   ├── frame_0005.png
│   └── ...
└── diffs/                 # Generated diff images (gitignored)
    └── <demo_name>/
        └── diff_frame_0000.png
```

## Usage

### Generate Baselines

Create reference images for a demo:

```bash
python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10
```

Options:
- `--frames`: Comma-separated frame numbers to capture
- `--script`: Path to input script (default: scripts/demos/joystick-demo.json)
- `--baseline-dir`: Custom baseline directory

### Compare Against Baselines

Check if current renders match baselines:

```bash
python -m atari_style.core.visual_test compare joystick_test
```

Exit codes:
- `0`: All frames match (within threshold)
- `1`: Differences detected or error occurred

Options:
- `--save-diff`: Always save diff images (normally only on failure)
- `--threshold`: Maximum allowed pixel difference ratio (default: 0.01)
- `--no-antialiasing`: Strict pixel-perfect comparison

### View Results

Failed comparisons generate side-by-side diff images in `baselines/diffs/`:
- Left: Baseline (reference)
- Middle: Current render
- Right: Diff (red highlights show changes)

## CI Integration

### With pytest

```bash
pytest test_visual_regression.py -v
```

### Manual Check

```bash
# Generate baselines once (commit to repo)
python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10

# In CI pipeline, compare against baselines
python -m atari_style.core.visual_test compare joystick_test || {
    echo "Visual regression detected!"
    exit 1
}
```

## Configuration

### Threshold

The default threshold of `0.01` means 1% of pixels can differ. Adjust based on your needs:

```bash
# Strict comparison (0.1% tolerance)
python -m atari_style.core.visual_test compare joystick_test --threshold 0.001

# Relaxed comparison (5% tolerance)
python -m atari_style.core.visual_test compare joystick_test --threshold 0.05
```

### Anti-aliasing Tolerance

By default, minor differences (<10/255 per channel) are ignored to handle anti-aliasing variations:

```bash
# Disable anti-aliasing tolerance (pixel-perfect)
python -m atari_style.core.visual_test compare joystick_test --no-antialiasing
```

## Best Practices

1. **Select Key Frames**: Choose frames that represent different states:
   - Initial state (frame 0)
   - Mid-animation (frame 30)
   - Complex state (frame 60)

2. **Commit Baselines**: Check baseline images into version control so all developers and CI use the same reference.

3. **Update on Intent**: If a visual change is intentional, regenerate baselines:
   ```bash
   python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10
   git add baselines/joystick_test/
   git commit -m "Update visual baselines for joystick_test"
   ```

4. **Review Diffs**: When tests fail, check `baselines/diffs/` to understand what changed.

## Troubleshooting

### "No baseline found"

Generate baselines first:
```bash
python -m atari_style.core.visual_test generate <demo_name> --frames 0,5,10
```

### "PIL/Pillow is required"

Install dependencies:
```bash
pip install Pillow numpy
```

### Font differences across systems

Different systems may have different default fonts, causing minor rendering differences. Solutions:
- Increase threshold slightly
- Use anti-aliasing tolerance (default)
- Specify explicit font in `HeadlessRenderer` configuration

### High diff ratio on identical code

Possible causes:
- Font rendering differences
- System color profile differences
- Random number generation (ensure demos use fixed seeds)

Increase threshold or use anti-aliasing tolerance to handle system variations.

## Technical Details

### Image Comparison

The comparison algorithm:
1. Converts both images to RGB
2. Calculates per-pixel max channel difference
3. With anti-aliasing tolerance, ignores diffs <10/255
4. Reports ratio of significantly different pixels

### Diff Visualization

Diff images show:
- **Baseline**: Original reference
- **Current**: New render
- **Diff**: Current render with red highlights on changed pixels

This makes it easy to spot regressions at a glance.

### Performance

Visual regression tests are fast:
- Rendering: ~0.1-1s per demo (headless)
- Comparison: ~0.01s per frame
- Typical full suite: <5s

Safe to run in CI on every commit.
