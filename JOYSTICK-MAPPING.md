# Joystick Mapping - Screen Saver

## Opposite Direction Pairs Control Same Parameter

The screen saver uses an intuitive mapping where **opposite joystick directions control the same parameter** - one direction increases it, the opposite direction decreases it.

## Visual Mapping

```
        UP-LEFT          UP          UP-RIGHT
        (Param 4+)    (Param 1+)    (Param 3+)
              ↖           ↑           ↗
               \          |          /
                \         |         /
    LEFT ←-------+--------•--------+------→ RIGHT
    (Param 2-)   |                 |    (Param 2+)
                /         |         \
               /          |          \
              ↙           ↓           ↘
        DOWN-LEFT        DOWN        DOWN-RIGHT
        (Param 3-)    (Param 1-)    (Param 4-)
```

## Parameter Pairs

### Pair 1: Vertical Axis (UP ↔ DOWN)
**Controls: Parameter 1**
- Push stick **UP** (↑) → Increase Parameter 1
- Push stick **DOWN** (↓) → Decrease Parameter 1

*Examples:*
- Lissajous: Frequency X (1-10)
- Spiral: Number of spirals (1-8)
- Wave Circles: Number of circles (5-30)
- Plasma: X frequency (0.01-0.3)

---

### Pair 2: Horizontal Axis (RIGHT ↔ LEFT)
**Controls: Parameter 2**
- Push stick **RIGHT** (→) → Increase Parameter 2
- Push stick **LEFT** (←) → Decrease Parameter 2

*Examples:*
- Lissajous: Frequency Y (1-10)
- Spiral: Rotation speed (0.1-5.0x)
- Wave Circles: Wave amplitude (0.5-8.0)
- Plasma: Y frequency (0.01-0.3)

---

### Pair 3: Diagonal Axis (UP-RIGHT ↔ DOWN-LEFT)
**Controls: Parameter 3**
- Push stick **UP-RIGHT** (↗) → Increase Parameter 3
- Push stick **DOWN-LEFT** (↙) → Decrease Parameter 3

*Examples:*
- Lissajous: Phase offset (0-2π)
- Spiral: Tightness (2-15)
- Wave Circles: Wave frequency (0.1-2.0)
- Plasma: Diagonal frequency (0.01-0.3)

---

### Pair 4: Diagonal Axis (UP-LEFT ↔ DOWN-RIGHT)
**Controls: Parameter 4**
- Push stick **UP-LEFT** (↖) → Increase Parameter 4
- Push stick **DOWN-RIGHT** (↘) → Decrease Parameter 4

*Examples:*
- Lissajous: Resolution/Points (100-1000)
- Spiral: Scale/Size (0.2-0.8)
- Wave Circles: Circle spacing (1-6)
- Plasma: Radial frequency (0.01-0.3)

---

## Why This Mapping?

**Intuitive Control**:
- Natural opposition: Push up to increase, down to decrease
- Symmetrical layout: Diagonals work the same way
- Easy to remember: Opposite = same parameter

**Physical Ergonomics**:
- Easier to feel opposite directions
- Natural push-pull motion
- Reduced cognitive load

**Parameter Relationships**:
- Allows simultaneous control of complementary parameters
- No conflict between different parameter types
- Clear visual feedback on screen

---

## Mode Switching

**Button-based (not directional)**:
- **Button 0** (A/Cross): Next animation mode
- **Button 1** (B/Circle): Exit to menu
- **Space** (keyboard): Next animation mode
- **ESC/Q** (keyboard): Exit to menu

This keeps mode switching separate from parameter adjustment, preventing accidental mode changes while tweaking parameters.

---

## Threshold and Sensitivity

- **Activation threshold**: 0.3 (30% deflection)
- **Deadzone**: 0.15 (built into input handler)
- **Adjustment delay**: 50ms after each parameter change

This prevents:
- Accidental adjustments from stick drift
- Too-rapid parameter changes
- Unintended diagonal detection

---

## Usage Tips

1. **Start with cardinals** (UP/DOWN, LEFT/RIGHT) - easier to control
2. **Try diagonals** once comfortable with basic parameters
3. **Watch parameter display** (top-left) to see changes
4. **Small deflections** are often enough - no need to max out the stick
5. **Combine with mode switching** to explore all 16 parameters (4 per animation × 4 animations)

---

## Quick Reference Table

| Direction | Param | Lissajous | Spiral | Wave Circles | Plasma |
|-----------|-------|-----------|--------|--------------|--------|
| ↑ UP | 1+ | Freq X+ | Spirals+ | Circles+ | Freq X+ |
| ↓ DOWN | 1- | Freq X- | Spirals- | Circles- | Freq X- |
| → RIGHT | 2+ | Freq Y+ | Speed+ | Amplitude+ | Freq Y+ |
| ← LEFT | 2- | Freq Y- | Speed- | Amplitude- | Freq Y- |
| ↗ UP-RIGHT | 3+ | Phase+ | Tight+ | Wave Freq+ | Freq Diag+ |
| ↙ DOWN-LEFT | 3- | Phase- | Tight- | Wave Freq- | Freq Diag- |
| ↖ UP-LEFT | 4+ | Points+ | Scale+ | Spacing+ | Freq Rad+ |
| ↘ DOWN-RIGHT | 4- | Points- | Scale- | Spacing- | Freq Rad- |
