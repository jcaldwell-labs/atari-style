# UAT: GIF Export Feature (Issue #80)

**Tester**: _______________
**Date**: _______________
**Platform**: Windows / WSL2 / Linux / macOS
**ffmpeg version**: _______________

## Pre-Test Setup

1. Verify ffmpeg is installed:
   ```bash
   ffmpeg -version
   ```
   Version: _______________

2. Verify the demo script exists:
   ```bash
   ls scripts/demos/joystick-demo.json
   ```

---

## Test Cases

### TC-01: CLI Help Shows GIF Options

**Command:**
```bash
python -m atari_style.core.demo_video --help
```

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| `--gif` flag visible | Yes | | |
| `--gif-fps` option visible | Yes, default 15 | | |
| `--gif-scale` option visible | Yes, default 480 | | |
| GIF example in examples | Yes | | |

**Notes**: _______________

---

### TC-02: Basic GIF Export (Default Settings)

**Command:**
```bash
python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json --gif -o /tmp/test-default.gif
```

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| Command completes without error | Yes | | |
| Output file created | `/tmp/test-default.gif` exists | | |
| File is valid GIF | Opens in image viewer | | |
| File size reasonable | < 5MB for short clip | | |
| Animation plays | Loops properly | | |

**File size**: _______________ bytes
**Notes**: _______________

---

### TC-03: Custom FPS Setting

**Command:**
```bash
python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json --gif --gif-fps 10 -o /tmp/test-10fps.gif
```

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| Command completes | Yes | | |
| Animation appears slower | Fewer frames visible | | |
| File smaller than default | Fewer frames = smaller | | |

**File size**: _______________ bytes (compare to TC-02)
**Notes**: _______________

---

### TC-04: Custom Scale Setting

**Command:**
```bash
python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json --gif --gif-scale 320 -o /tmp/test-320px.gif
```

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| Command completes | Yes | | |
| GIF width is ~320px | Check with `file` or image viewer | | |
| File smaller than default | Smaller resolution = smaller | | |

**Actual dimensions**: _______________ x _______________
**File size**: _______________ bytes
**Notes**: _______________

---

### TC-05: High Quality Export

**Command:**
```bash
python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json --gif --gif-fps 24 --gif-scale 640 -o /tmp/test-hq.gif
```

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| Command completes | Yes | | |
| Animation smoother | Higher FPS visible | | |
| GIF width is ~640px | Check dimensions | | |
| Quality acceptable | No severe banding/dithering | | |

**Actual dimensions**: _______________ x _______________
**File size**: _______________ bytes
**Notes**: _______________

---

### TC-06: Auto-Generated Output Filename

**Command:**
```bash
python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json --gif
```

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| Output filename auto-generated | `joystick_test-joystick-demo.gif` | | |
| Extension is `.gif` not `.mp4` | Yes | | |

**Generated filename**: _______________
**Notes**: _______________

---

### TC-07: Progress Display Shows GIF Mode

**Command:**
```bash
python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json --gif -o /tmp/test.gif
```

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| "Exporting ... as GIF" message | Yes | | |
| GIF settings displayed | Shows fps and scale | | |
| "GIF exported to" at end | Yes | | |

**Notes**: _______________

---

### TC-08: MP4 Export Still Works

**Command:**
```bash
python -m atari_style.core.demo_video joystick_test scripts/demos/joystick-demo.json -o /tmp/test.mp4
```

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| Command completes | Yes | | |
| Output is MP4 (not GIF) | Valid MP4 file | | |
| No GIF settings shown | Says "video" not "GIF" | | |

**Notes**: _______________

---

### TC-09: Error Handling - Missing ffmpeg

(Optional - only if you can temporarily rename ffmpeg)

| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| Clear error message | "ffmpeg not found" | | |
| Exits gracefully | No crash/traceback | | |

**Notes**: _______________

---

## Summary

| Test Case | Result |
|-----------|--------|
| TC-01: CLI Help | |
| TC-02: Basic GIF Export | |
| TC-03: Custom FPS | |
| TC-04: Custom Scale | |
| TC-05: High Quality | |
| TC-06: Auto Filename | |
| TC-07: Progress Display | |
| TC-08: MP4 Still Works | |
| TC-09: Error Handling | |

**Overall Pass/Fail**: _______________

## Issues Found

| Issue # | Description | Severity (High/Med/Low) |
|---------|-------------|-------------------------|
| 1 | | |
| 2 | | |
| 3 | | |

## File Size Comparison

| Test | Settings | File Size | Duration |
|------|----------|-----------|----------|
| TC-02 | Default (15fps, 480px) | | |
| TC-03 | 10fps, 480px | | |
| TC-04 | 15fps, 320px | | |
| TC-05 | 24fps, 640px | | |

**Target**: < 5MB for 5-10 second clips

## Visual Quality Notes

| Aspect | Rating (1-5) | Notes |
|--------|--------------|-------|
| Color accuracy | | |
| Animation smoothness | | |
| Dithering quality | | |
| Text readability | | |

## Additional Notes

_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
