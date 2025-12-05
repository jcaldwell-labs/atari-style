# Visual Regression Testing Guide

## Overview

Visual regression testing catches unintended changes to terminal rendering by comparing current output against baseline reference images. This is critical for:

- Detecting rendering bugs before merge
- Ensuring font/color changes don't break demos
- Validating cross-platform compatibility
- CI/CD quality gates

## Quick Start

### 1. Generate Baselines

Create reference images for key frames:

```bash
# Generate baselines for joystick_test demo
python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10

# Output:
# Generating baselines for joystick_test...
# Frames: [0, 5, 10]
# Output directory: /workspaces/atari-style/baselines/joystick_test
#   Saved: frame_0000.png
#   Saved: frame_0005.png
#   Saved: frame_0010.png
# Generated 3 baseline images
```

Baselines are saved to `baselines/<demo_name>/` and should be committed to git.

### 2. Run Comparison

Compare current render against baselines:

```bash
python -m atari_style.core.visual_test compare joystick_test

# Output on success:
# ============================================================
# VISUAL REGRESSION TEST RESULTS
# ============================================================
# ✓ PASS Frame    0: diff=0.0000
# ✓ PASS Frame    5: diff=0.0000
# ✓ PASS Frame   10: diff=0.0000
# ============================================================
# Total: 3 | Passed: 3 | Failed: 0
# ============================================================
```

Exit code 0 = all tests passed, 1 = failures detected.

### 3. Review Failures

When visual differences are detected:

```bash
python -m atari_style.core.visual_test compare joystick_test --save-diff
```

Diff images are saved to `baselines/diffs/<demo_name>/` showing:
- **Left panel**: Baseline (reference)
- **Middle panel**: Current render
- **Right panel**: Diff (red highlights changes)

## Advanced Usage

### Custom Threshold

Adjust pixel difference tolerance:

```bash
# Strict (0.1% tolerance)
python -m atari_style.core.visual_test compare joystick_test --threshold 0.001

# Relaxed (5% tolerance)
python -m atari_style.core.visual_test compare joystick_test --threshold 0.05
```

Default is 0.01 (1%).

### Disable Anti-aliasing Tolerance

For pixel-perfect comparison:

```bash
python -m atari_style.core.visual_test compare joystick_test --no-antialiasing
```

By default, minor differences (<10/255 per channel) are ignored to handle anti-aliasing variations across systems.

### Custom Frame Selection

```bash
# Test specific critical frames
python -m atari_style.core.visual_test generate joystick_test --frames 0,30,60,90

# Test animation transitions
python -m atari_style.core.visual_test generate starfield --frames 0,15,30,45
```

Choose frames that represent:
- Initial state (frame 0)
- Mid-animation
- Complex rendering (many objects)
- Edge cases

### Custom Baseline Directory

```bash
# Use custom baseline location
python -m atari_style.core.visual_test generate joystick_test \
    --frames 0,5,10 \
    --baseline-dir /path/to/custom/baselines
```

## CI Integration

### GitHub Actions

Add to `.github/workflows/python.yml`:

```yaml
- name: Run visual regression tests
  run: |
    # Generate baselines
    python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10
    # Compare (fail build if diff detected)
    python -m atari_style.core.visual_test compare joystick_test
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run visual regression tests before commit
python -m atari_style.core.visual_test compare joystick_test
if [ $? -ne 0 ]; then
    echo "Visual regression detected! Review diffs in baselines/diffs/"
    exit 1
fi
```

## Pytest Integration

Run with pytest for detailed reporting:

```bash
pytest test_visual_regression.py -v

# Output:
# test_joystick_test_baseline_generation PASSED
# test_joystick_test_comparison_match PASSED
# test_missing_baseline PASSED
# test_unknown_demo PASSED
```

Or standalone:

```bash
python test_visual_regression.py
```

## Workflow

### Initial Setup

1. **Create baseline for new demo**:
   ```bash
   python -m atari_style.core.visual_test generate my_demo --frames 0,10,20
   ```

2. **Commit baselines**:
   ```bash
   git add baselines/my_demo/
   git commit -m "Add visual baselines for my_demo"
   ```

3. **Add to CI**:
   Update `.github/workflows/python.yml` to include your demo.

### During Development

1. **Make code changes** to renderer, colors, or demo logic

2. **Run comparison**:
   ```bash
   python -m atari_style.core.visual_test compare my_demo --save-diff
   ```

3. **Review diffs** in `baselines/diffs/my_demo/`

4. **If change is intentional**:
   ```bash
   # Regenerate baselines
   python -m atari_style.core.visual_test generate my_demo --frames 0,10,20
   git add baselines/my_demo/
   git commit -m "Update visual baselines after renderer improvement"
   ```

5. **If change is unintended**:
   Fix the bug and re-test until comparison passes.

### Updating Baselines

When you intentionally change visual output:

```bash
# Regenerate baselines
python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10

# Verify new baselines
python -m atari_style.core.visual_test compare joystick_test

# Commit if correct
git add baselines/joystick_test/
git commit -m "Update baselines: improved joystick rendering"
```

## Troubleshooting

### "No baseline found"

Generate baselines first:
```bash
python -m atari_style.core.visual_test generate <demo_name> --frames 0,5,10
```

### High diff ratio despite identical code

**Possible causes:**
- Font rendering differences across systems
- Random number generation (use fixed seeds)
- System color profiles

**Solutions:**
- Increase `--threshold`
- Use anti-aliasing tolerance (default enabled)
- Ensure demos use deterministic rendering

### Font differences across systems

Different OSes have different default fonts. To ensure consistency:

1. **Increase threshold slightly** (0.01 → 0.02)
2. **Use anti-aliasing tolerance** (default)
3. **Specify explicit font** in renderer config (future enhancement)

### Tests pass locally but fail in CI

Check:
- Font availability on CI runner
- Virtual display configuration
- Baseline images committed to git

## Technical Details

### Comparison Algorithm

```python
def compare_images(baseline, current, allow_antialiasing=True):
    # 1. Convert to RGB
    # 2. Calculate per-pixel channel difference
    # 3. If allow_antialiasing, ignore diffs < 10/255
    # 4. Count significantly different pixels
    # 5. Return ratio = diff_pixels / total_pixels
```

### Diff Visualization

Three-panel layout:
- **Baseline**: Original reference (what we expect)
- **Current**: New render (what we got)
- **Diff**: Current with red highlights on changed pixels

Makes visual inspection fast and intuitive.

### Performance

Visual regression tests are efficient:
- **Baseline generation**: ~0.1-1s per demo
- **Frame comparison**: ~0.01s per frame
- **Typical test suite**: <5 seconds

Safe to run in CI on every commit.

## Best Practices

### 1. Choose Representative Frames

Select frames that cover:
- Initial render (frame 0)
- Animation mid-point
- Complex states (many objects, full buffers)
- Edge cases (wraparound, boundaries)

### 2. Keep Frame Count Reasonable

- **Demos**: 3-5 frames sufficient
- **Games**: 5-10 frames to cover game states
- **Tools**: 2-3 frames for different modes

More frames = longer tests, diminishing returns.

### 3. Commit Baselines to Git

Baselines must be in version control so:
- All developers use same reference
- CI can run comparisons
- Changes are reviewed in PRs

### 4. Review Diffs Carefully

Don't blindly regenerate baselines. Review diff images to understand:
- Is the change intentional?
- Does it improve or degrade quality?
- Are there unintended side effects?

### 5. Update Baselines with Intent

When regenerating baselines, include in commit message:
- What changed visually
- Why the change was made
- PR/issue reference

Example:
```
Update visual baselines: improved color rendering

- Enhanced color contrast in joystick_test
- Fixed anti-aliasing artifacts
- Related to #123
```

## Examples

### Add New Demo to Visual Tests

```bash
# 1. Generate baselines
python -m atari_style.core.visual_test generate my_new_demo \
    --script scripts/demos/my-demo.json \
    --frames 0,15,30

# 2. Verify comparison works
python -m atari_style.core.visual_test compare my_new_demo \
    --script scripts/demos/my-demo.json

# 3. Commit baselines
git add baselines/my_new_demo/
git commit -m "Add visual baselines for my_new_demo"

# 4. Add to CI workflow
# Edit .github/workflows/python.yml
```

### Debug Visual Regression

```bash
# 1. Generate diff images
python -m atari_style.core.visual_test compare joystick_test --save-diff

# 2. View diff images
# baselines/diffs/joystick_test/diff_frame_*.png

# 3. If intentional, update baselines
python -m atari_style.core.visual_test generate joystick_test --frames 0,5,10

# 4. If bug, fix code and re-test
# ... fix code ...
python -m atari_style.core.visual_test compare joystick_test
```

## See Also

- [baselines/README.md](../../baselines/README.md) - Baseline directory structure
- [GPU Visualizer Guide](gpu-visualizer-guide.md) - Video export system
- [Architecture](../architecture.md) - Overall system design
