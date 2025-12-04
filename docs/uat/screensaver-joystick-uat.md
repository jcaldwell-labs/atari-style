# UAT: Screensaver Joystick Controls

**Tester**: _______________
**Date**: _______________
**Controller**: _______________ (Xbox/PlayStation/8BitDo/Other)
**Platform**: Windows / WSL2 / Linux / macOS

## Pre-Test Setup

1. Connect joystick before starting
2. Run joystick test to verify connection:
   ```bash
   python -c "from atari_style.demos.tools.joystick_test import run_joystick_test; run_joystick_test()"
   ```
3. Note controller name displayed: _______________
4. Verify all axes and buttons respond in test utility

## Launch Screensaver

```bash
python -c "from atari_style.demos.visualizers.screensaver import run_screensaver; run_screensaver()"
```

---

## Test Cases

### TC-01: Left Stick X - Parameter 1

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Push left stick RIGHT | Parameter 1 increases (shown in HUD) | | |
| 2 | Push left stick LEFT | Parameter 1 decreases | | |
| 3 | Release stick | Parameter 1 holds steady | | |

**Notes**: _______________

---

### TC-02: Left Stick Y - Parameter 2

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Push left stick DOWN | Parameter 2 increases | | |
| 2 | Push left stick UP | Parameter 2 decreases | | |
| 3 | Release stick | Parameter 2 holds steady | | |

**Notes**: _______________

---

### TC-03: Right Stick X - Parameter 3

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Push right stick RIGHT | Parameter 3 increases | | |
| 2 | Push right stick LEFT | Parameter 3 decreases | | |
| 3 | Release stick | Parameter 3 holds steady | | |

**Notes**: _______________

---

### TC-04: Right Stick Y - Parameter 4

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Push right stick DOWN | Parameter 4 increases | | |
| 2 | Push right stick UP | Parameter 4 decreases | | |
| 3 | Release stick | Parameter 4 holds steady | | |

**Notes**: _______________

---

### TC-05: Button 0 (A/Cross) - Cycle Animation

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Press Button 0 once | Animation changes to next mode | | |
| 2 | Press Button 0 again | Animation changes again | | |
| 3 | Press repeatedly | Cycles through all 11 animations | | |

**Animations observed** (check each):
- [ ] Lissajous
- [ ] Spirals
- [ ] Wave Circles
- [ ] Plasma
- [ ] Mandelbrot
- [ ] Fluid Lattice
- [ ] Particle Swarm
- [ ] Tunnel Vision
- [ ] Plasma→Lissajous (composite)
- [ ] Flux→Spiral (composite)
- [ ] Lissajous→Plasma (composite)

**Notes**: _______________

---

### TC-06: Button 1 (B/Circle) - Exit

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Press Button 1 | Returns to menu OR exits cleanly | | |

**Notes**: _______________

---

### TC-07: Button 2 (X/Square) - Reset Parameters

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Adjust parameters with sticks | Parameters change from defaults | | |
| 2 | Press Button 2 | All 4 parameters reset to defaults | | |

**Notes**: _______________

---

### TC-08: Button 3 (Y/Triangle) - Toggle Help

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Press Button 3 | Help overlay appears showing controls | | |
| 2 | Press Button 3 again | Help overlay disappears | | |

**Notes**: _______________

---

### TC-09: D-Pad Up/Down - Speed Adjustment

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Press D-Pad UP | Animation speed increases | | |
| 2 | Press D-Pad DOWN | Animation speed decreases | | |

**Notes**: _______________

---

### TC-10: D-Pad Left/Right - Color Mode

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Press D-Pad RIGHT | Color mode changes (check HUD) | | |
| 2 | Press D-Pad LEFT | Color mode changes back | | |

**Color modes observed**: _______________

**Notes**: _______________

---

### TC-11: Save Slots (Hold to Save)

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Adjust parameters to unique values | Parameters visible in HUD | | |
| 2 | HOLD a save button for 2+ seconds | "Saved to slot X" message appears | | |
| 3 | Change parameters again | Different values now | | |
| 4 | TAP the same save button | "Loaded slot X" - original params restored | | |

**Save button used**: _______________

**Notes**: _______________

---

### TC-12: Keyboard Fallback

| Step | Action | Expected | Actual | Pass/Fail |
|------|--------|----------|--------|-----------|
| 1 | Press Arrow Keys | Parameter control (like left stick) | | |
| 2 | Press Space/Enter | Cycle animation (like Button 0) | | |
| 3 | Press ESC or Q | Exit (like Button 1) | | |
| 4 | Press H | Toggle help (like Button 3) | | |

**Notes**: _______________

---

## Summary

| Test Case | Result |
|-----------|--------|
| TC-01: Left Stick X | |
| TC-02: Left Stick Y | |
| TC-03: Right Stick X | |
| TC-04: Right Stick Y | |
| TC-05: Button 0 - Cycle | |
| TC-06: Button 1 - Exit | |
| TC-07: Button 2 - Reset | |
| TC-08: Button 3 - Help | |
| TC-09: D-Pad Up/Down | |
| TC-10: D-Pad Left/Right | |
| TC-11: Save Slots | |
| TC-12: Keyboard Fallback | |

**Overall Pass/Fail**: _______________

## Issues Found

| Issue # | Description | Severity (High/Med/Low) |
|---------|-------------|-------------------------|
| 1 | | |
| 2 | | |
| 3 | | |

## Axis/Button Mapping Observed

Fill in the actual behavior if different from expected:

| Physical Input | Expected Mapping | Actual Behavior |
|----------------|------------------|-----------------|
| Left Stick X | Axis 0 | |
| Left Stick Y | Axis 1 | |
| Right Stick X | Axis 2 or 3 | |
| Right Stick Y | Axis 3 or 4 | |
| A/Cross | Button 0 | |
| B/Circle | Button 1 | |
| X/Square | Button 2 | |
| Y/Triangle | Button 3 | |
| D-Pad Up | Hat 0 or Button | |
| D-Pad Down | Hat 0 or Button | |
| D-Pad Left | Hat 0 or Button | |
| D-Pad Right | Hat 0 or Button | |

## Additional Notes

_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
