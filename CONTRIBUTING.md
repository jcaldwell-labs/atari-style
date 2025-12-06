# Contributing to atari-style

This guide covers conventions for contributing to atari-style, with emphasis on CLI tool design that enables Unix pipeline composition.

## Unix Composability Philosophy

Every atari-style CLI tool should participate in Unix pipelines. Text in, text out. Composable by default.

> "This is the Unix philosophy: Write programs that do one thing and do it well. Write programs to work together. Write programs to handle text streams, because that is a universal interface." — Doug McIlroy

## CLI Conventions

### Standard Argument Patterns

All CLI tools should follow these conventions:

```bash
# Input from file
tool input.json -o output.mp4

# Output to stdout (text-based formats)
tool input.json                  # Defaults to stdout
tool input.json -o -             # Explicit stdout

# Input from stdin
tool -                           # Read from stdin
cat input.json | tool -          # Pipe input

# Full pipeline composition
cat params.json | tool - | next-tool - > output.txt
```

### Required Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-o, --output FILE` | Output file path | stdout for text, required for binary |
| `-h, --help` | Show help message | - |
| `--version` | Show version | - |
| `-v, --verbose` | Increase verbosity | - |
| `-q, --quiet` | Suppress non-essential output | - |

### Optional Arguments

| Argument | Description |
|----------|-------------|
| `--dry-run` | Preview without executing |
| `--json` | Output in JSON format |
| `--format FORMAT` | Specify output format |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 130 | Interrupted (Ctrl+C) |

### Stderr vs Stdout

- **stdout**: Primary output (data, results, pipeline content)
- **stderr**: Progress messages, warnings, errors, status updates

```python
# Correct: Data to stdout, status to stderr
print(json.dumps(result))  # stdout - can be piped
print(f"Processing: {filename}", file=sys.stderr)  # stderr - human readable
```

## Text-Based Interchange Formats

### Standard Formats

| Data Type | Format | File Extension |
|-----------|--------|----------------|
| Storyboards | JSON | `.json` |
| Parameters | JSON | `.json` |
| Canvas | BOXES_CANVAS_V1 | `.canvas` |
| Frame manifest | JSON | `manifest.json` |

### JSON Output Convention

When outputting JSON, pretty-print for human readability unless `--compact` is specified:

```python
if args.compact:
    print(json.dumps(data))
else:
    print(json.dumps(data, indent=2))
```

## CLI Template

Use this template when creating new CLI tools:

```python
#!/usr/bin/env python3
"""Tool description - one line summary.

Detailed description of what this tool does and how it fits
into the atari-style pipeline.

Usage:
    python -m atari_style.module.tool input.json -o output.mp4
    cat input.json | python -m atari_style.module.tool - > output.txt

Examples:
    # Basic usage
    python -m atari_style.module.tool input.json

    # With output file
    python -m atari_style.module.tool input.json -o result.json

    # Pipeline composition
    cat params.json | python -m atari_style.module.tool - | next-tool
"""

import argparse
import sys
from pathlib import Path


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        description='Tool description',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.json              # Output to stdout
  %(prog)s input.json -o out.json  # Output to file
  cat data.json | %(prog)s -       # Read from stdin
        """
    )

    parser.add_argument(
        'input',
        help='Input file (use - for stdin)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress non-essential output'
    )

    args = parser.parse_args()

    try:
        # Read input
        if args.input == '-':
            data = sys.stdin.read()
        else:
            with open(args.input, 'r') as f:
                data = f.read()

        # Process data (replace with your logic)
        result = data  # TODO: implement your processing here

        # Write output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            if not args.quiet:
                print(f"Output written to: {args.output}", file=sys.stderr)
        else:
            print(result)

        return 0

    except FileNotFoundError as e:
        print(f"Error: File not found: {e.filename}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

## Pipeline Examples

### Current Pipelines

```bash
# Storyboard to canvas visualization
python -m atari_style.connectors.storyboard2canvas storyboard.json | boxes-live --load -

# Preview server (not a pipeline tool, serves HTTP)
python -m atari_style.preview -d output/
```

### Target Pipelines (In Progress)

```bash
# Parameter exploration to video
atari-explore plasma --interesting | atari-render plasma | ffmpeg -i - output.mp4

# Storyboard validation pipeline
find storyboards/ -name "*.json" | xargs -I{} python -m atari_style.core.video_script_cli validate {}

# Batch conversion
ls output/*.json | while read f; do
    python -m atari_style.connectors.storyboard2canvas "$f" > "${f%.json}.canvas"
done
```

## Testing CLI Tools

### Required Tests

1. **Help output**: Verify `--help` works
2. **File input**: Test with valid input file
3. **Stdin input**: Test with `-` argument
4. **Missing file**: Test error handling
5. **Invalid input**: Test error handling

```python
class TestCLI(unittest.TestCase):
    """CLI integration tests."""

    def test_help(self):
        """Test --help flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.module.tool', '--help'],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage:', result.stdout.lower())

    def test_stdin_input(self):
        """Test reading from stdin."""
        result = subprocess.run(
            [sys.executable, '-m', 'atari_style.module.tool', '-'],
            input='{"test": true}',
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
```

## Security Guidelines

See `.github/copilot-instructions.md` for security requirements:
- Always escape HTML output with `html.escape()`
- Validate file paths against traversal attacks
- Stream large files, don't load into memory

## Code Quality

- Type hints on all public functions
- Docstrings in Google style
- No magic numbers (use named constants)
- Remove unused imports

## Before Merge

All PRs must pass CI checks. The following automated checks run on every PR:

### Lint (ruff)
```bash
# Run locally before pushing
ruff check atari_style/ tests/
```

### Tests (pytest)
```bash
# Run all tests
pytest tests/ -v
```

### Coverage
```bash
# Run tests with coverage (60% minimum for CLI tools)
pytest tests/ --cov=atari_style --cov-report=term
```

See `.github/workflows/ci.yml` for the full CI configuration.

## Pull Request Checklist

- [ ] CLI follows conventions (stdin/stdout, exit codes)
- [ ] Tests cover help, file input, stdin, errors
- [ ] Security guidelines followed
- [ ] All CI checks pass (lint, test, coverage)
- [ ] No unused imports
