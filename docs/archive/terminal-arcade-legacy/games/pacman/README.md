# Pac-Man

Classic maze chase game with intelligent ghost AI.

## Overview

Navigate through the maze collecting all pellets while avoiding four ghost enemies. Eat power pellets to temporarily turn the tables and chase the ghosts for bonus points!

## Gameplay

- **Objective**: Collect all 240 regular pellets and 4 power pellets to complete the level
- **Lives**: Start with 3 lives
- **Power-ups**: Eating a power pellet makes ghosts vulnerable for a limited time
- **Scoring**:
  - Regular pellet: 10 points
  - Power pellet: 50 points
  - Eating ghosts (escalating): 200, 400, 800, 1600 points

## Ghost AI

Each ghost has a unique personality that affects its behavior:

### Blinky (Red) - "The Chaser"
- **Strategy**: Direct pursuit
- **Behavior**: Always targets Pac-Man's current position
- **Difficulty**: High threat in open areas

### Pinky (Pink) - "The Ambusher"
- **Strategy**: Anticipation
- **Behavior**: Targets 4 tiles ahead of Pac-Man's direction
- **Difficulty**: Dangerous when you're not paying attention

### Inky (Cyan) - "The Flanker"
- **Strategy**: Coordinated attack
- **Behavior**: Uses both Blinky's position and Pac-Man's position for complex targeting
- **Difficulty**: Unpredictable and strategic

### Clyde (Orange) - "The Shy One"
- **Strategy**: Hit-and-run
- **Behavior**: Chases when far away, retreats when close (8 tile threshold)
- **Difficulty**: Creates patterns and coverage

## Game Modes

Ghosts switch between three behavioral modes:

1. **Chase Mode**: Ghosts actively pursue Pac-Man using their individual strategies
2. **Scatter Mode**: Ghosts retreat to their home corners
3. **Frightened Mode**: Activated when Pac-Man eats a power pellet - ghosts become vulnerable and flee

## Controls

- **Arrow Keys** or **WASD**: Move Pac-Man
- **ESC** or **Q**: Return to menu
- **Joystick**: Full analog stick support

## Technical Details

- **Pathfinding**: BFS (Breadth-First Search) algorithm for ghost navigation
- **Frame Rate**: ~30 FPS
- **Maze Size**: 28x27 tiles
- **Tunnel Wrapping**: Screen edges wrap around for strategic escapes

## Features

- ✓ Classic maze layout inspired by the original
- ✓ 4 distinct ghost AI personalities
- ✓ Mode switching (Chase/Scatter/Frightened/Dead)
- ✓ Lives system with respawning
- ✓ Level progression when all pellets collected
- ✓ Score tracking with combo system
- ✓ Smooth character animation
- ✓ Full keyboard and joystick support

## Strategy Tips

1. **Learn the Patterns**: Each ghost has predictable behavior - use it to your advantage
2. **Use Power Pellets Wisely**: Save them for when you're cornered or want to rack up points
3. **Corner Strategy**: Lure ghosts into corners before eating a power pellet
4. **Tunnel Advantage**: The wrap-around tunnels slow ghosts down - use for escapes
5. **Watch Clyde**: His scatter behavior creates unexpected challenges

## Version History

- **v1.0** - Initial release with all 4 ghosts and classic gameplay
