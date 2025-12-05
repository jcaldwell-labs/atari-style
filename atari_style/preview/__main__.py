"""CLI entry point for the preview server.

Usage:
    python -m atari_style.preview
    python -m atari_style.preview -p 3000
    python -m atari_style.preview -d ./output -d ./storyboards
"""

from .server import main

if __name__ == '__main__':
    main()
