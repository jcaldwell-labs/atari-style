#!/usr/bin/env python3
"""Test new animations."""

from atari_style.demos.screensaver import ScreenSaver

def main():
    print("Testing new screen saver animations...")
    s = ScreenSaver()

    print(f"\n✓ Screen saver initialized with {len(s.animations)} animations:\n")
    for i, name in enumerate(s.animation_names, 1):
        print(f"  {i}. {name}")
        anim = s.animations[i-1]
        if hasattr(anim, 'get_param_info'):
            params = anim.get_param_info()
            for param in params:
                print(f"     - {param}")

    print("\n✓ All animations loaded successfully!")

if __name__ == "__main__":
    main()
