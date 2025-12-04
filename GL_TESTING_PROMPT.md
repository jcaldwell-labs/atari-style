# Testing Prompt for GL-Capable Session (Issue #88 / PR #99)

**Context**: Agent 1 and Agent 2 have completed unifying the GL and terminal video export pipelines. All unit tests pass in headless environment, but we need to validate GL video export functionality in an environment with OpenGL support.

## Your Mission

Test the unified video export system with actual GL rendering to verify:
1. GL video export still works after refactoring
2. Preset system integration is functional
3. No regressions in video quality or performance

## Setup

```bash
# Clone and checkout the feature branch
git clone https://github.com/jcaldwell-labs/atari-style.git
cd atari-style
git checkout feature/unified-video-export-88
git pull origin feature/unified-video-export-88

# Install dependencies
pip install -r requirements.txt

# Verify ffmpeg is available
ffmpeg -version
```

## Test Cases to Execute

### TC1: Basic GL Export (MP4)
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter

print('=== Test 1: Basic GL Export ===')
exporter = VideoExporter()
exporter.export_composite('plasma', 'test_plasma_3s.mp4', duration=3.0)
print('✓ Export completed')
"

# Verify output
ls -lh test_plasma_3s.mp4
ffprobe test_plasma_3s.mp4 2>&1 | grep -E "Duration|Video:|Stream"
```

**Expected**:
- File created: `test_plasma_3s.mp4`
- Duration: ~3 seconds
- Video codec: h264
- Resolution: 1920x1080 (default)
- File size: >500 KB

### TC2: Preset System (YouTube Shorts)
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter, VIDEO_FORMATS

print('=== Test 2: YouTube Shorts Preset ===')
fmt = VIDEO_FORMATS['youtube_shorts']
print(f'Resolution: {fmt.width}x{fmt.height}')
print(f'FPS: {fmt.fps}')

exporter = VideoExporter()
exporter.export_with_format('lissajous', 'test_shorts_5s.mp4', 'youtube_shorts', duration=5.0)
print('✓ Export completed')
"

# Verify output
ffprobe test_shorts_5s.mp4 2>&1 | grep -E "Duration|Video:|Stream|1080x1920"
```

**Expected**:
- Console: "Resolution: 1080x1920"
- Console: "FPS: 30"
- File: `test_shorts_5s.mp4` is vertical (1080x1920)
- Duration: ~5 seconds

### TC3: GIF Export
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter

print('=== Test 3: GIF Export ===')
exporter = VideoExporter()
exporter.create_gif('mandelbrot_zoom', 'test_mandelbrot_2s.gif', duration=2.0, fps=15)
print('✓ Export completed')
"

# Verify output
file test_mandelbrot_2s.gif
ls -lh test_mandelbrot_2s.gif
```

**Expected**:
- File type: "GIF image data"
- Animated (verify it loops)
- File size varies (typically 1-5 MB)

### TC4: Multiple Presets
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter

print('=== Test 4: Multiple Format Presets ===')
exporter = VideoExporter()

# TikTok vertical
exporter.export_with_format('plasma_lissajous', 'test_tiktok.mp4', 'tiktok', duration=2.0)
print('✓ TikTok export complete')

# Instagram square
exporter.export_with_format('flux_spiral', 'test_instagram.mp4', 'instagram_square', duration=2.0)
print('✓ Instagram export complete')

# Twitter landscape
exporter.export_with_format('spiral', 'test_twitter.mp4', 'twitter', duration=2.0)
print('✓ Twitter export complete')
"

# Verify all created
ls -lh test_tiktok.mp4 test_instagram.mp4 test_twitter.mp4
```

**Expected**:
- All 3 files created
- Different resolutions (1080x1920, 1080x1080, 1280x720)

### TC5: Backward Compatibility - VIDEO_FORMATS
```bash
python -c "
from atari_style.core.gl.video_export import VIDEO_FORMATS, VideoExporter

print('=== Test 5: Backward Compatibility ===')

# Old-style format access (VIDEO_FORMATS dict)
fmt = VIDEO_FORMATS['youtube_4k']
print(f'YouTube 4K: {fmt.width}x{fmt.height} @ {fmt.fps}fps')

# Use format with VideoExporter
exporter = VideoExporter(width=fmt.width, height=fmt.height, fps=fmt.fps)
exporter.export_composite('plasma', 'test_4k_1s.mp4', duration=1.0)
print('✓ Backward compatibility verified')
"

# Verify 4K output
ffprobe test_4k_1s.mp4 2>&1 | grep "3840x2160"
```

**Expected**:
- Console: "YouTube 4K: 3840x2160 @ 60fps"
- File created at 4K resolution

### TC6: Composite Animations
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter

print('=== Test 6: Composite Animations ===')
exporter = VideoExporter()

# Test each composite
composites = ['plasma_lissajous', 'lissajous_plasma', 'flux_spiral']

for comp in composites:
    output = f'test_{comp}.mp4'
    exporter.export_composite(comp, output, duration=1.0)
    print(f'✓ {comp} export complete')
"

ls -lh test_plasma_lissajous.mp4 test_lissajous_plasma.mp4 test_flux_spiral.mp4
```

**Expected**:
- All 3 composite videos created
- No errors during rendering

### TC7: Progress Reporting
```bash
python -c "
from atari_style.core.gl.video_export import VideoExporter

print('=== Test 7: Progress Reporting ===')
exporter = VideoExporter(fps=30)
exporter.export_composite('plasma', 'test_progress_5s.mp4', duration=5.0)
" | tee progress_output.txt

# Check progress format
grep "Rendering" progress_output.txt
grep "Frame.*/" progress_output.txt
grep "All frames rendered" progress_output.txt
grep "Encoding video" progress_output.txt
```

**Expected**:
- Console: "Rendering plasma: 150 frames at 30 FPS"
- Console: "Frame X/150 (Y%)" progress updates
- Console: "All frames rendered. Encoding video..."
- Console: "Success! Video saved to: test_progress_5s.mp4"

## Validation Checklist

After running all tests, verify:

- [ ] All test videos created successfully
- [ ] No errors or exceptions during export
- [ ] Video files are playable (use `ffplay` or media player)
- [ ] Preset resolutions match expected (vertical/square/landscape)
- [ ] GIF files animate correctly
- [ ] Progress output is clear and informative
- [ ] File sizes are reasonable (not empty, not excessively large)

## Report Results

Copy this template and fill in results:

```markdown
## GL Video Export Test Results (PR #99)

**Environment**: [OS, Python version, GPU info]
**Date**: [Date]
**Commit**: 69cfae5

### Test Results

- [ ] TC1: Basic GL Export (MP4) - PASS/FAIL
- [ ] TC2: Preset System (YouTube Shorts) - PASS/FAIL
- [ ] TC3: GIF Export - PASS/FAIL
- [ ] TC4: Multiple Presets - PASS/FAIL
- [ ] TC5: Backward Compatibility - PASS/FAIL
- [ ] TC6: Composite Animations - PASS/FAIL
- [ ] TC7: Progress Reporting - PASS/FAIL

### Sample Outputs

[Attach screenshots or ffprobe outputs]

### Issues Found

[List any issues, or write "None"]

### Performance Notes

[Any observations about speed, file sizes, quality]

### Conclusion

✅ GL video export working correctly after unification
or
❌ Issues found (see above)
```

## Cleanup

```bash
# Remove test files
rm -f test_*.mp4 test_*.gif progress_output.txt
```

## What to Post

1. Post the completed test results template as a comment to PR #99
2. If any issues found, create new issues and reference them
3. If all tests pass, approve the PR with comment: "GL video export validated - all tests passing"

---

**Note**: This testing validates the GL-specific functionality that couldn't be tested in the headless dev container where the initial work was done.
