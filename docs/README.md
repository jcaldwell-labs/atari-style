# Documentation

Welcome to the atari-style documentation. This directory contains guides, references, and architecture documentation for the project.

## Getting Started

New to atari-style? Start here:

| Document | Description |
|----------|-------------|
| [Quick Start](getting-started/QUICK_START.md) | Installation and first run |
| [Controls](getting-started/CONTROLS.md) | Keyboard and controller basics |
| [Joystick Mapping](getting-started/JOYSTICK-MAPPING.md) | Controller button assignments |
| [Button Remapping](getting-started/BUTTON-REMAPPING.md) | Customizing controls |
| [Control Scheme Standard](getting-started/CONTROL_SCHEME_STANDARD.md) | Cross-project control patterns |

## Guides

Step-by-step guides for specific tasks:

| Guide | Description |
|-------|-------------|
| [GPU Visualizer CLI](guides/gpu-visualizer-guide.md) | Interactive shaders, GIF/video export, storyboards |
| [Visual Regression Testing](guides/visual-regression-guide.md) | Automated visual regression testing framework |
| [Joystick Controls](joystick-controls.md) | Detailed controller documentation |

## Reference

Quick references for features and animations:

| Document | Description |
|----------|-------------|
| [Features at a Glance](reference/FEATURES-AT-A-GLANCE.md) | Overview of all features |
| [Animation Summary](reference/ANIMATION-SUMMARY.md) | List of available animations |
| [Animations Visual Guide](reference/ANIMATIONS-VISUAL-GUIDE.md) | Visual preview of animations |
| [New Animations](reference/NEW-ANIMATIONS.md) | Recently added animations |
| [Composite Animations](reference/COMPOSITE_ANIMATIONS.md) | Multi-effect composites |
| [Composite Animation Analysis](reference/COMPOSITE_ANIMATION_ANALYSIS.md) | Technical analysis |
| [Visual Guide Composites](reference/VISUAL_GUIDE_COMPOSITES.md) | Visual composite reference |
| [Mandelbrot Quick Reference](reference/MANDELBROT_QUICK_REFERENCE.md) | Mandelbrot controls and params |

## Architecture

Technical design and implementation details:

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design overview |
| [Shader Roadmap](shader-roadmap.md) | GPU shader implementation plan |

## Archive

Historical documentation from development:

- [Session Summaries](archive/session-summaries/) - Development session notes
- [Implementation Notes](archive/implementation-notes/) - Feature implementation details
- [Fix Logs](archive/fix-logs/) - Bug fix documentation

## Directory Structure

```
docs/
├── README.md                 # This file
├── architecture.md           # System architecture
├── joystick-controls.md      # Controller documentation
├── shader-roadmap.md         # GPU implementation plan
├── getting-started/          # New user documentation
├── guides/                   # How-to guides
├── reference/                # Quick reference docs
├── architecture/             # Detailed architecture docs
└── archive/                  # Historical documentation
    ├── session-summaries/    # Dev session notes
    ├── implementation-notes/ # Feature implementation
    └── fix-logs/             # Bug fix documentation
```

## Contributing Documentation

When adding new documentation:

1. **Guides** go in `guides/` - step-by-step instructions for tasks
2. **References** go in `reference/` - quick lookup information
3. **Architecture** docs go in `architecture/` - system design
4. **Session notes** go in `archive/session-summaries/` - development logs

Keep the root `docs/` directory clean - only index files and major cross-cutting docs belong here.
