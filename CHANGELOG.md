# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed - 2025-01-18
**Screen Saver Joystick Mapping Improvement**

- **BREAKING**: Changed joystick direction mapping to use opposite pairs
  - Previously: Each direction controlled a different operation
  - Now: Opposite directions control same parameter (increase/decrease)

- **Mapping Changes**:
  - UP ↔ DOWN now control Parameter 1 (increase/decrease)
  - RIGHT ↔ LEFT now control Parameter 2 (increase/decrease)
  - UP-RIGHT ↔ DOWN-LEFT now control Parameter 3 (increase/decrease)
  - UP-LEFT ↔ DOWN-RIGHT now control Parameter 4 (increase/decrease)

- **Mode Switching**:
  - Removed RIGHT direction from mode switching
  - Mode switching now exclusively via Button 0 (was: Button 0 or RIGHT)
  - This prevents accidental mode changes while adjusting parameters

**Rationale**:
- More intuitive: opposite = same parameter
- Better ergonomics: natural push-pull motion
- Easier to remember: symmetrical layout
- Prevents confusion between navigation and parameter control

**Migration**:
- Users accustomed to RIGHT for "next mode" should now use Button 0 (A/Cross)
- All directional input now dedicated to parameter adjustment

---

## [0.1.0] - 2025-01-18

### Added
- Initial implementation of atari-style terminal demos
- Interactive menu system with keyboard and joystick support
- Starfield demo with 3D projection and speed control
- Screen saver with 4 parametric animations
- Joystick test utility for hardware verification
- Real-time parametric control system
- 8-directional joystick input support
- Parameter value display on-screen
- Button debouncing and state tracking

### Features
- **Menu System**: Navigate demos with keyboard or joystick
- **Starfield**: 3D space flight with adjustable warp speed and 3 color modes
- **Screen Saver**: Lissajous curves, spirals, wave circles, and plasma effects
- **Joystick Test**: Real-time visualization of all axes and buttons

### Technical
- Python 3.8+ with pygame and blessed
- 60 FPS rendering for screen saver
- 30 FPS for starfield and menu
- Buffer-based terminal rendering
- Automatic joystick detection and initialization

### Documentation
- CLAUDE.md - Developer guide
- README.md - User guide
- CONTROLS.md - Complete control reference
- FIXES.md - Bug fixes and enhancements
- ENHANCEMENTS.md - Screen saver implementation details
- JOYSTICK-MAPPING.md - Detailed joystick mapping guide
- SUMMARY.md - Project overview

### Bug Fixes
- Fixed missing BRIGHT_WHITE color constant
- Fixed joystick button spam on startup
- Fixed joystick test exiting on Button 1 press
- Added button state tracking for proper debouncing
- Added initialization delays for stable startup

---

## Version History

- **v0.1.0** (2025-01-18): Initial release with 3 demos and full joystick support
- **Unreleased**: Improved joystick mapping with opposite direction pairs
