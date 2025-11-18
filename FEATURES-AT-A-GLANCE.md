# Screen Saver Features - At a Glance

## 🎮 Quick Reference Card

### Controls

**Keyboard**
- `H` - Toggle help modal
- `Space` - Next animation
- `ESC`/`Q` - Exit

**Joystick Buttons**
- `BTN 0` - Next animation
- `BTN 1` - Exit
- `BTN 2-5` - Save/Load slots
  - **Tap**: Load
  - **Hold 0.5s**: Save

**Joystick Directions** (All 8 Animations)
- `↑↓` - Parameter 1
- `←→` - Parameter 2
- `↗↙` - Parameter 3
- `↖↘` - Parameter 4

---

## 🎨 8 Animations

| # | Name | Type | Key Feature |
|---|------|------|-------------|
| 1 | Lissajous | Math | Frequency patterns |
| 2 | Spiral | Geo | Rotating arms |
| 3 | Wave Circles | Geo | Ripples |
| 4 | Plasma | Math | Wave interference |
| 5 | Mandelbrot | Fractal | Zoom 1000x |
| 6 | Fluid Lattice | Physics | Rain + waves |
| 7 | Particle Swarm | AI | Flocking |
| 8 | Tunnel | Demo | 3D tunnel |

---

## 💡 Quick Tips

**Help Anytime**: Press `H` - see what each direction does

**Save Your Favorites**:
1. Adjust params → Hold BTN 2-5 → Saved!
2. Want it back? → Tap that button

**Most Dramatic**:
- Fluid: Push `UP` for rain storm
- Mandelbrot: Push `UP` to zoom in
- Particles: Push `UP` for more

**Calm/Intense Toggle**:
- Save calm to Slot 2
- Save intense to Slot 3
- Tap to switch moods!

---

## 🎯 Parameter Count

- **8 animations** × **4 params** = **32 total**
- **4 save slots** = **16 presets** possible
- **8 joystick directions** = full utilization
- **60 FPS** smooth rendering

---

## 🚀 Launch Command

```bash
source venv/bin/activate
python run.py
# Select "Screen Saver"
# Press H for help!
```

---

## 📊 Bottom Screen Indicators

```
┌───────────────────────────────────────────┐
│                                           │
│         [Animation runs here]             │
│                                           │
│      Loaded Slot 2  ← Feedback (2s)      │
│                                           │
│ Slots: [2] [3] [4] [5] ← Green if saved  │
└───────────────────────────────────────────┘
```

---

## 💾 Save Slot Examples

**Slot 2**: "Rainstorm"
- Fluid Lattice
- Rain: 1.0, Speed: 0.4, Power: 15, Damping: 0.93

**Slot 3**: "Mandelbrot Deep Zoom"
- Mandelbrot Zoomer
- Zoom: 500x, Center: (-0.75, 0.1), Detail: 150

**Slot 4**: "Tight Flock"
- Particle Swarm
- Particles: 80, Speed: 2.5, Cohesion: 1.5, Separation: 0.5

**Slot 5**: "Hyperspeed Tunnel"
- Tunnel Vision
- Depth: 4.0, Rotation: 1.5, Size: 1.5, Color: 2.5

---

## ✨ What Makes This Special

- **Discoverable**: Help system reveals all controls
- **Saveable**: Never lose a great configuration
- **Intuitive**: Opposite directions = natural control
- **Diverse**: 8 completely different visual styles
- **Interactive**: 32 real-time adjustable parameters
- **Fast**: 60 FPS smooth animation

**Every parameter is at your fingertips! 🎮**
