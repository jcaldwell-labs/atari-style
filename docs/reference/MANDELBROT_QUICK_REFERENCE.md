# Mandelbrot Explorer - Quick Reference Card

## 🎮 **Controls** (Press **H** in-game for help)

### **Basic Navigation**
```
Arrow Keys / WASD / Joystick  →  Pan view
Z / Button 0                   →  Zoom IN (to 1e-15!)
X / Button 1                   →  Zoom OUT (max 5.0)
```

### **Palette Control**
```
C or . or Button 2            →  Next palette ►
, or Button 3                  →  Previous palette ◄

8 Palettes Available:
  1. electric (default) - Blue gradients
  2. fire - Red/yellow heat map
  3. ocean - Cyan/blue depths
  4. sunset - Magenta/red/yellow
  5. forest - Green earth tones
  6. psychedelic - Rainbow madness!
  7. copper - Metallic warmth
  8. grayscale - Classic monochrome
```

### **Display & Detail**
```
+ or =                         →  More detail (max 1000 iterations)
-                              →  Less detail (min 10 iterations)
I                              →  Toggle coordinates on/off
```

### **Screenshot**
```
S or Button 4                  →  Save screenshot!
  ↳ Saves to: ~/.terminal-arcade/mandelbrot-screenshots/
  ↳ Format: mandelbrot_YYYYMMDD_HHMMSS.txt
  ↳ Includes metadata box with:
    • Timestamp
    • Center coordinates
    • Zoom level
    • Current palette
    • Iteration count
```

### **Bookmarks**
```
1  →  Overview (full set)
2  →  Valley (detailed structure)
3  →  Spiral (triple spiral)
4  →  Seahorse (classic valley)
5  →  Triple Spiral (complex)
6  →  Elephant (valley pattern)
```

### **Other**
```
H                              →  Toggle help overlay
R                              →  Reset to overview
ESC / Q                        →  Exit to menu
```

---

## 🎨 **Palette Showcase**

**Each palette has 16 colors for smooth gradients!**

| Palette | Colors | Best For |
|---------|--------|----------|
| **electric** | Blue → Cyan → White | General use, high contrast |
| **fire** | Red → Yellow → White | Dramatic warm effect |
| **ocean** | Cyan → Blue → White | Cool underwater |
| **sunset** | Magenta → Red → Yellow → White | Colorful shots |
| **forest** | Green → Cyan → Yellow → White | Natural tones |
| **psychedelic** | Rainbow cycle | Wild patterns! |
| **copper** | Red → Yellow → White metallic | Warm glow |
| **grayscale** | Black → White | Classic look |

---

## 📸 **Screenshot Tips**

1. Find an interesting view
2. Adjust palette (Button 2/3 or C/,)
3. Fine-tune iterations (+/-)
4. Press **S** or **Button 4**
5. Wait for confirmation message
6. Screenshot saved with metadata!

**Screenshots are plain text** - easy to share via email, chat, or version control!

---

## 🔬 **Deep Zoom Tips**

- **Start shallow**: Begin at overview (press R)
- **Find a spot**: Use arrow keys to position
- **Zoom gradually**: Press Z or Button 0 repeatedly
- **Watch iterations**: Auto-increases when deep
- **Boost manually**: Press + for more detail if needed
- **Patience**: Very deep zooms take time to render

**Zoom capability**: Can zoom to **1e-15** (0.000000000000001)!

---

## 🎯 **Recommended Exploration Path**

### **For Beginners**
1. Press **R** to reset
2. Try all palettes (Button 2 or C)
3. Visit bookmark **4** (Seahorse)
4. Zoom in with **Z** a few times
5. Take a screenshot with **S**

### **For Experienced**
1. Visit bookmark **3** (Spiral)
2. Switch to **psychedelic** palette
3. Zoom very deep (10+ times)
4. Press **+** to increase iterations
5. Fine-tune position with arrows
6. Screenshot the result

### **For Artists**
1. Start with **sunset** or **copper** palette
2. Find an interesting edge
3. Zoom to medium depth (1e-6)
4. Adjust iterations for detail
5. Take multiple screenshots with different palettes

---

## ⚡ **Performance Notes**

- **Fast**: Low iterations (10-100), shallow zoom
- **Balanced**: 100-250 iterations, medium zoom
- **Slow**: 500-1000 iterations, deep zoom (1e-10+)

If rendering is slow, press **-** to reduce iterations.

---

## 🐛 **Troubleshooting**

### "Screenshot not saving"
- Check permissions: `~/.terminal-arcade/mandelbrot-screenshots/`
- Directory is auto-created on start

### "Zoomed too deep, looks pixelated"
- **Normal!** Floating-point precision limits at ~1e-10
- Press **+** to increase iterations
- Try zooming to a different area

### "Palette cycling too fast"
- Built-in 0.2s debounce for buttons
- Use keyboard (, and .) for precise control

### "Can't zoom out far enough"
- Max zoom out is 5.0 (by design)
- Press **R** to reset to overview (1.5)

---

## 💾 **Screenshot Example**

```
╔═══════════════════════════════════╗
║ Mandelbrot Set Explorer           ║
║ Timestamp: 2025-01-18 14:30:22    ║
║ Center: -7.4500e-01 + 1.8600e-01i ║
║ Zoom: 2.5000e-03                  ║
║ Palette: sunset                   ║
║ Iterations: 250                   ║
╚═══════════════════════════════════╝

[Your beautiful fractal appears here in ASCII art!]
```

---

**Happy exploring!** 🌌

Press **H** anytime for in-game help.
