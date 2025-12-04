# atari-style Philosophy

This document articulates the guiding principles that shape atari-style. These aren't constraints on creativity—they're a compass for when choices arise.

## Core Principles

### 1. The Terminal is a Canvas, Not a Cage

Terminal constraints—character cells, limited colors, text streams—aren't limitations to work around. They're the medium we've chosen. Like pixel art or haiku, constraints breed creativity.

**Implication**: Don't apologize for terminal aesthetics. Embrace them.

**Evaluation**: Does this feature celebrate terminal capabilities or try to escape them?

**Examples**:
- ASCII art isn't a fallback for "real" graphics—it's the art form
- Character-based rendering creates distinctive visual texture
- Terminal color palettes evoke specific eras and moods

---

### 2. Parameters are Territory, Not Settings

A 4-parameter animation isn't a program with 4 knobs—it's a 4-dimensional landscape to explore. Some regions are boring, some are beautiful, some are chaotic. The tool helps you navigate.

**Implication**: Build exploration tools, not just renderers.

**Evaluation**: Can the user get lost in this? Can they discover unexpected beauty?

**Examples**:
- The screensaver's parameter space holds thousands of distinct visual states
- "Edge of chaos" regions produce the most interesting patterns
- Saving parameter sets is like pinning locations on a map

---

### 3. Small Tools, Composed Freely

Every component should:
- Do one thing well
- Accept text input / produce text output where possible
- Work standalone AND integrate with pipelines

**Implication**: Connectors and formats matter as much as features.

**Evaluation**: Can this be piped? Can it be scripted?

**Examples**:
```bash
# Export frames, process externally, reassemble
python -m atari_style.core.gl.video_export flux_spiral --frames ./out/
convert ./out/*.png -delay 3 animation.gif

# Chain thumbnail generation with other tools
python -m atari_style.core.gl.video_export --all-thumbnails -o ./thumbs/
montage ./thumbs/*.png grid.png
```

---

### 4. Show, Don't Document

Educational content should be interactive demonstrations, not walls of text. Understanding emerges from manipulation, not explanation.

**Implication**: Every concept gets a visualization.

**Evaluation**: Can someone learn this by playing with it?

**Examples**:
- The Platonic solids viewer teaches 3D geometry through interaction
- Parameter exploration reveals mathematical relationships viscerally
- Games teach timing, spatial reasoning, and pattern recognition

---

### 5. AI-Native Development

This project is developed WITH AI (Claude, Copilot), not just FOR humans. The development process itself is an experiment in human-AI collaboration.

**Implication**: Design for AI readability. Document decisions for future context windows.

**Evaluation**: Can an AI agent understand and extend this code effectively?

**Examples**:
- CLAUDE.md provides project context for AI assistants
- Consistent code patterns make AI suggestions more accurate
- Decision logs capture reasoning, not just results

---

### 6. Play is Serious Work

Games, toys, and playful exploration are valid ways to learn and create. The line between "productive" and "playful" is artificial.

**Implication**: Embrace joystick controls, game mechanics, aesthetic joy.

**Evaluation**: Is this fun? Would you show it to a friend?

**Examples**:
- The joystick test utility is genuinely enjoyable to use
- Parameter exploration feels like discovering hidden worlds
- Game demos prioritize feel over feature checklists

---

## Decision Framework

When evaluating a change, ask:

1. **Philosophy** (#64): Does it align with our core principles?
2. **Aesthetic** (#71): Does it look and feel like atari-style?
3. **Composable** (#65): Does it work in pipelines? Can it be scripted?
4. **AI-Native** (#66): Is it AI-readable? Does it aid collaboration?
5. **Quality** (#73): Does it meet our performance and reliability standards?

If a change conflicts with multiple principles, discuss it. Principles in tension often reveal interesting design spaces.

---

## The Name

**atari-style** evokes:
- The Atari era's aesthetic constraints (limited palettes, character graphics)
- The exploratory joy of early personal computing
- A "style" that's distinctive but adaptable

It's not nostalgia—it's recognizing that constraints and playfulness produced lasting art.

---

## Living Document

This philosophy evolves as the project grows. Principles that don't serve the work should be questioned. New insights should be captured.

Last updated: 2025-12-03
