"""CLI entry point for the thumbnail extractor.

Usage:
    python -m atari_style.tools.thumbnail_extractor script.json -o thumbnails/
    python -m atari_style.tools.thumbnail_extractor script.json --count 5 -o thumbnails/
"""

from .thumbnail_extractor import main

if __name__ == '__main__':
    main()
