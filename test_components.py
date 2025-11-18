#!/usr/bin/env python3
"""Test script to verify individual components."""

import sys


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from atari_style.core.renderer import Renderer, Color
        print("  ✓ Renderer imported")

        from atari_style.core.input_handler import InputHandler, InputType
        print("  ✓ InputHandler imported")

        from atari_style.core.menu import Menu, MenuItem
        print("  ✓ Menu imported")

        from atari_style.demos.starfield import StarfieldDemo
        print("  ✓ StarfieldDemo imported")

        from atari_style.demos.screensaver import ScreenSaver
        print("  ✓ ScreenSaver imported")

        from atari_style.demos.joystick_test import JoystickTest
        print("  ✓ JoystickTest imported")

        print("\n✓ All imports successful!")
        return True
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_color_constants():
    """Test that all color constants exist."""
    print("\nTesting color constants...")
    from atari_style.core.renderer import Color

    required_colors = [
        'RED', 'GREEN', 'BLUE', 'YELLOW', 'MAGENTA', 'CYAN', 'WHITE',
        'BRIGHT_RED', 'BRIGHT_GREEN', 'BRIGHT_BLUE', 'BRIGHT_YELLOW',
        'BRIGHT_MAGENTA', 'BRIGHT_CYAN', 'BRIGHT_WHITE'
    ]

    missing = []
    for color in required_colors:
        if not hasattr(Color, color):
            missing.append(color)
        else:
            print(f"  ✓ Color.{color} exists")

    if missing:
        print(f"\n✗ Missing colors: {missing}")
        return False
    else:
        print("\n✓ All color constants present!")
        return True


def test_input_handler():
    """Test input handler initialization."""
    print("\nTesting InputHandler...")
    try:
        from atari_style.core.input_handler import InputHandler

        handler = InputHandler()
        print(f"  ✓ InputHandler created")
        print(f"  Joystick initialized: {handler.joystick_initialized}")

        if handler.joystick_initialized:
            info = handler.verify_joystick()
            print(f"  Joystick: {info['name']}")
            print(f"  Axes: {info['axes']}")
            print(f"  Buttons: {info['buttons']}")
            print(f"  Previous buttons tracked: {len(handler.previous_buttons)}")

        handler.cleanup()
        print("\n✓ InputHandler test passed!")
        return True
    except Exception as e:
        print(f"\n✗ InputHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("COMPONENT TESTS")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Color Constants", test_color_constants()))
    results.append(("InputHandler", test_input_handler()))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")

    all_passed = all(passed for _, passed in results)
    print("=" * 60)

    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
