# Video Export Integration Test Plan (Issue #88)

**Status**: Ready for execution after Agent 2 completes refactoring  
**Created**: 2025-01-24  
**Branch**: `feature/unified-video-export-88`

## Overview

Integration testing plan for unified GL and terminal video export pipelines. Tests verify that both exporters correctly use the shared base classes from `video_base.py` while maintaining backward compatibility.

## Pre-requisites

1. Agent 2 has completed refactoring:
   - `atari_style/core/gl/video_export.py` uses `FFmpegEncoder` via composition
   - `atari_style/core/demo_video.py` (`DemoVideoExporter`) uses `FFmpegEncoder` via composition
   - Both use shared `FFmpegEncoder`, `PresetManager`, and `VideoFormat` from `video_base.py`

2. All unit tests passing:
   ```bash
   python -m unittest tests.test_video_base -v  # 39 tests
   ```

3. FFmpeg available:
   ```bash
   ffmpeg -version
   ```

## Test Cases

### TC1: GL Video Export - Basic MP4

**Objective**: Verify GL exporter creates valid MP4 using base infrastructure

**Steps**:
```bash
cd /workspaces/atari-style

# Export plasma animation
python -c "
from atari_style.core.gl.video_export import VideoExporter
exporter = VideoExporter()
exporter.export_composite('plasma', 'test_plasma.mp4', duration=3.0)
"
```

**Expected Results**:
- Console shows progress: "Rendering N frames at 60 FPS"
- Console shows: "✓ Rendered N frames"
- Console shows: "Encoding video..."
- Console shows: "✓ Video saved: test_plasma.mp4"
- File exists: `test_plasma.mp4`
- File size > 100 KB
- Video playable: `ffplay test_plasma.mp4` (3 seconds, 60 FPS)

**Pass/Fail**: ___________

---

### TC2: GL Video Export - Format Preset (YouTube Shorts)

**Objective**: Verify preset system works with GL exporter

**Steps**:
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter, VIDEO_FORMATS

# Use format preset
fmt = VIDEO_FORMATS['youtube_shorts']
print(f'Resolution: {fmt.width}x{fmt.height}')
print(f'FPS: {fmt.fps}')

exporter = VideoExporter()
exporter.export_with_format('plasma', 'test_shorts.mp4', 'youtube_shorts', duration=5.0)
"
```

**Expected Results**:
- Console: "Resolution: 1080x1920"
- Console: "FPS: 30"
- File: `test_shorts.mp4` is 1080x1920 vertical video
- Duration: 5 seconds
- Playable in portrait mode

**Pass/Fail**: ___________

---

### TC3: GL Video Export - Animated GIF

**Objective**: Verify GIF export works with GL exporter

**Steps**:
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter
exporter = VideoExporter()
exporter.create_gif('lissajous', 'test_lissajous.gif', duration=2.0, fps=15)
"
```

**Expected Results**:
- Console: "Encoding GIF..."
- File: `test_lissajous.gif` exists
- GIF format confirmed: `file test_lissajous.gif` shows "GIF image data"
- Animated (30 frames = 2.0s * 15 FPS)
- Playable: Opens in browser/viewer as animated GIF

**Pass/Fail**: ___________

---

### TC4: Terminal Demo Export - Basic MP4

**Objective**: Verify terminal exporter creates valid MP4 using base infrastructure

**Note**: DemoVideoExporter requires a script file (JSON) that defines input keyframes and timing.
This is designed for terminal demos with recorded/scripted joystick input.

**Steps**:
```bash
# First, verify a demo script exists
ls scripts/demos/starfield-demo.json

python -c "
from atari_style.core.demo_video import DemoVideoExporter

exporter = DemoVideoExporter(
    demo_name='starfield',
    script_path='scripts/demos/starfield-demo.json',
    output_path='test_starfield.mp4'
)
exporter.export()
"
```

**Expected Results**:
- Console shows: "Rendering: [progress bar]"
- Console shows: "✓ Video exported to: test_starfield.mp4"
- File exists: `test_starfield.mp4`
- Video playable with terminal-style ASCII graphics

**Pass/Fail**: ___________

---

### TC5: Terminal Demo Export - Format Preset (TikTok)

**Objective**: Verify preset system works with terminal exporter

**Note**: DemoVideoExporter uses PresetManager to get format dimensions.
Preset is applied via width/height constructor parameters.

**Steps**:
```bash
python -c "
from atari_style.core.demo_video import DemoVideoExporter
from atari_style.core.video_base import PresetManager

# Get TikTok preset dimensions
fmt = PresetManager.get_preset('tiktok')
print(f'TikTok format: {fmt.width}x{fmt.height}')

exporter = DemoVideoExporter(
    demo_name='joystick_test',
    script_path='scripts/demos/joystick-demo.json',
    output_path='test_tiktok.mp4',
    width=fmt.width,
    height=fmt.height
)
exporter.export()
"
```

**Expected Results**:
- Console: "TikTok format: 1080x1920"
- File: `test_tiktok.mp4` is 1080x1920 vertical
- Terminal graphics properly scaled to vertical format

**Pass/Fail**: ___________

---

### TC6: Terminal Demo Export - Animated GIF

**Objective**: Verify GIF export works with terminal exporter

**Note**: DemoVideoExporter supports GIF mode via `gif_mode=True` constructor parameter.

**Steps**:
```bash
python -c "
from atari_style.core.demo_video import DemoVideoExporter

exporter = DemoVideoExporter(
    demo_name='joystick_test',
    script_path='scripts/demos/joystick-demo.json',
    output_path='test_joystick.gif',
    gif_mode=True,
    gif_fps=15
)
exporter.export()
"
```

**Expected Results**:
- Console shows rendering progress
- File: `test_joystick.gif` exists
- GIF format confirmed: `file test_joystick.gif` shows "GIF image data"
- Animated terminal graphics

**Pass/Fail**: ___________

---

### TC7: Progress Reporting Consistency

**Objective**: Verify both exporters show progress output

**Note**: GL and Terminal exporters have different progress formats due to their different architectures,
but both use shared FFmpegEncoder for the encoding step.

**Steps**:
```bash
# Run both exports and compare console output
python -c "
from atari_style.core.gl.video_export import VideoExporter

print('=== GL Export ===')
exporter = VideoExporter()
exporter.export_composite('plasma', 'test_gl_progress.mp4', duration=1.0)
"

python -c "
from atari_style.core.demo_video import DemoVideoExporter

print('=== Terminal Export ===')
exporter = DemoVideoExporter(
    demo_name='joystick_test',
    script_path='scripts/demos/joystick-demo.json',
    output_path='test_term_progress.mp4'
)
exporter.export()
"
```

**Expected Results**:
- GL shows: "Rendering [composite]: N frames at M FPS" with frame progress
- GL shows: "All frames rendered. Encoding video..."
- GL shows: "Success! Video saved to: test_gl_progress.mp4"
- Terminal shows: "Rendering: [progress bar]"
- Terminal shows: "✓ Video exported to: test_term_progress.mp4"
- Both use FFmpegEncoder for final encoding step

**Pass/Fail**: ___________

---

### TC8: Error Handling - Missing FFmpeg

**Objective**: Verify graceful failure when ffmpeg unavailable

**Steps**:
```bash
# Temporarily disable ffmpeg
PATH_BACKUP="$PATH"
export PATH="/usr/bin:/bin"  # Remove ffmpeg

python -c "
from atari_style.core.gl.video_export import VideoExporter
exporter = VideoExporter()
try:
    exporter.export_composite('plasma', 'should_fail.mp4', duration=1.0)
    print('ERROR: Should have raised RuntimeError')
except RuntimeError as e:
    print(f'✓ Caught expected error: {e}')
" 2>&1

# Restore PATH
export PATH="$PATH_BACKUP"
```

**Expected Results**:
- Console: "✓ Caught expected error: ffmpeg not found"
- Error message helpful (mentions installing ffmpeg)
- No stack trace shown to user
- No partial files created

**Pass/Fail**: ___________

---

### TC9: Preset Listing

**Objective**: Verify preset discovery works for both exporters

**Steps**:
```bash
python -c "
from atari_style.core.video_base import PresetManager

print('All presets:', len(PresetManager.list_presets()))
print('Vertical presets:', PresetManager.list_presets(filter_vertical=True))
print('Horizontal/square presets:', PresetManager.list_presets(filter_vertical=False))
"
```

**Expected Results**:
- Console: "All presets: 15" (or current total)
- Vertical list includes: `youtube_shorts`, `tiktok`, `instagram_story`
- Horizontal list includes: `youtube_1080p`, `youtube_4k`, `twitter`
- No duplicates, all presets valid

**Pass/Fail**: ___________

---

### TC10: Backward Compatibility - CLI Export

**Objective**: Verify existing CLI scripts still work

**Steps**:
```bash
# Test existing GL export CLI
python atari_style/core/gl/video_export.py plasma --duration 2.0 --output test_cli.mp4

# Test existing demo video CLI (if exists)
python atari_style/core/demo_video.py starfield --duration 2.0 --output test_demo_cli.mp4
```

**Expected Results**:
- Both CLIs work without modification
- Arguments parsed correctly
- Videos created successfully
- Output format unchanged from previous version

**Pass/Fail**: ___________

---

## Code Quality Checks

### CQ1: No Code Duplication

**Objective**: Verify FFmpeg encoding code not duplicated

**Steps**:
```bash
# Search for duplicate ffmpeg subprocess calls
grep -n "subprocess.run.*ffmpeg" atari_style/core/gl/video_export.py
grep -n "subprocess.run.*ffmpeg" atari_style/core/demo_video.py
```

**Expected Results**:
- GL exporter: 0 matches (uses `FFmpegEncoder.encode_video()`)
- Terminal exporter: 0 matches (uses `FFmpegEncoder.encode_video()`)
- Only `video_base.py` contains actual ffmpeg calls

**Pass/Fail**: ___________

---

### CQ2: No Duplicate Progress Code

**Objective**: Verify progress reporting not duplicated

**Steps**:
```bash
# Search for duplicate progress print statements
grep -n "Rendering.*frames" atari_style/core/gl/video_export.py
grep -n "Rendering.*frames" atari_style/core/demo_video.py
```

**Expected Results**:
- GL exporter: 0 matches (uses `ProgressReporter`)
- Terminal exporter: 0 matches (uses `ProgressReporter`)
- Only `video_base.py` contains progress logic

**Pass/Fail**: ___________

---

### CQ3: Composition Verification (FFmpegEncoder)

**Objective**: Verify both exporters use shared FFmpegEncoder via composition

**Steps**:
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter as GLExporter
from atari_style.core.demo_video import DemoVideoExporter
from atari_style.core.video_base import FFmpegEncoder

# Check GL exporter has encoder attribute
gl = GLExporter()
print('GL uses FFmpegEncoder:', hasattr(gl, 'encoder') and isinstance(gl.encoder, FFmpegEncoder))

# Check Demo exporter has encoder attribute (need to create with valid params)
# DemoVideoExporter creates encoder in __init__
import inspect
sig = inspect.signature(DemoVideoExporter.__init__)
print('DemoVideoExporter constructor params:', list(sig.parameters.keys()))
"
```

**Expected Results**:
- Console: "GL uses FFmpegEncoder: True"
- Console shows DemoVideoExporter constructor requires: demo_name, script_path, output_path
- Both exporters contain FFmpegEncoder instance (composition, not inheritance)

**Pass/Fail**: ___________

---

## Performance Checks

### PC1: Export Performance - No Regression

**Objective**: Verify refactoring didn't slow down exports

**Steps**:
```bash
# Benchmark current implementation
time python -c "
from atari_style.core.gl.video_export import VideoExporter
exporter = VideoExporter()
exporter.export_composite('plasma', 'benchmark.mp4', duration=5.0)
"

# Compare to baseline (if available)
```

**Expected Results**:
- Export completes in reasonable time (~5-10s for 5s video)
- No significant slowdown vs. previous implementation
- Frame rendering time similar to before

**Pass/Fail**: ___________

---

## Success Criteria

**All tests must pass** for issue #88 to be considered complete:

- [ ] All 10 functional test cases pass
- [ ] All 3 code quality checks pass
- [ ] All 1 performance check pass
- [ ] Unit tests pass: `python -m unittest tests.test_video_base -v`
- [ ] No regressions in existing functionality

## Test Execution

**Tester**: _____________  
**Date**: _____________  
**Branch**: feature/unified-video-export-88  
**Commit**: _____________

**Overall Result**: PASS / FAIL

## Notes

(Add any additional observations, issues found, or recommendations)

---

## Cleanup

After testing, remove test files:
```bash
rm -f test_*.mp4 test_*.gif benchmark.mp4
```
