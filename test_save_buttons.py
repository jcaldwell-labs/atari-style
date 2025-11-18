#!/usr/bin/env python3
"""Test save button detection."""

import pygame
import time

def main():
    print("Testing Save Button Detection...")
    print("=" * 60)

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("❌ No joystick detected!")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    print(f"✓ Joystick: {joystick.get_name()}")
    print(f"✓ Total buttons: {joystick.get_numbuttons()}")
    print()

    if joystick.get_numbuttons() < 6:
        print(f"⚠️  Warning: Only {joystick.get_numbuttons()} buttons available")
        print(f"   Buttons 2-5 need at least 6 buttons (0-5)")
        print()

    print("Button mapping for save system:")
    print("  Button 2 → Slot [2]")
    print("  Button 3 → Slot [3]")
    print("  Button 4 → Slot [4]")
    print("  Button 5 → Slot [5]")
    print()

    print("Testing button detection...")
    print("Press buttons 2, 3, 4, 5 (or any buttons you have)")
    print("Press Ctrl+C to exit")
    print("-" * 60)

    try:
        while True:
            pygame.event.pump()

            for i in range(joystick.get_numbuttons()):
                if joystick.get_button(i):
                    print(f"Button {i} PRESSED", end="")
                    if i in [2, 3, 4, 5]:
                        print(f" ← Save/Load button detected!")
                    else:
                        print()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("✓ Test complete")

    pygame.quit()

if __name__ == "__main__":
    main()
