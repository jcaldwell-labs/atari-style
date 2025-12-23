## Description

Brief description of what this PR does.

Fixes #(issue number)

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test improvement

## Changes Made

- List key changes made in this PR
- Include any architectural decisions
- Note any new dependencies

## Testing Performed

- [ ] Ran the affected demo/tool manually
- [ ] Added/updated unit tests
- [ ] Ran full test suite: `pytest --cov=atari_style`
- [ ] Tested on multiple platforms (if applicable)
- [ ] Verified visual regression tests (if applicable)

**Test Results:**
```
[Paste relevant test output or coverage report]
```

## Screenshots/Demos

If this is a visual change, include screenshots or GIF/video demos.

## Pre-Commit Checklist

Verified the following from [CLAUDE.md](../CLAUDE.md#pre-commit-checklist):

- [ ] **Run the code** - Actually executed and observed behavior
- [ ] **Tests assert outcomes** - Tests have meaningful assertions
- [ ] **Input validation** - Validated user inputs at boundaries
- [ ] **Cross-platform** - Works on Linux/macOS/Windows (or tested on available platforms)

For algorithm/math changes:
- [ ] **Verified the math** - Worked through calculations by hand
- [ ] **Tested edge cases** - Zero, negative, very large values, empty inputs
- [ ] **Checked units** - FPS, seconds, frame counts are consistent

## Code Quality

- [ ] Followed Unix philosophy principles (PHILOSOPHY.md)
- [ ] Maintained/improved test coverage (target: 80%+)
- [ ] Used type hints for public functions
- [ ] Updated CLAUDE.md with new features/changes (if applicable)
- [ ] Updated README.md (if user-facing changes)

## Documentation

- [ ] Updated relevant documentation in docs/
- [ ] Added docstrings to new functions/classes
- [ ] Updated CLAUDE.md if adding new demo or changing architecture

## Additional Notes

Any additional information for reviewers.
