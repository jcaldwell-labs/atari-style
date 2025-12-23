# jcaldwell-labs Organization Guidelines

This document outlines standards and best practices for all projects in the jcaldwell-labs organization. These guidelines ensure consistency, quality, and discoverability across the ecosystem.

## Project Documentation Standards

### README Requirements

Every project must have a comprehensive README.md with the following sections:

1. **Header & Badges**
   - Project title
   - CI/CD status badge
   - Code coverage badge (if applicable)
   - License badge (MIT)
   - Language/version badge (e.g., Python 3.8+)
   - "PRs Welcome" badge

2. **Project Description**
   - One-line tagline describing the project
   - Brief explanation of purpose and philosophy
   - Feature summary

3. **"Why [Project Name]?" Section**
   - Value proposition - what makes this project unique
   - Key differentiators
   - Use cases with specific examples

4. **Demo Section**
   - Visual demonstration (GIF, asciinema, or screenshot)
   - Quick try-it-yourself snippet

5. **Features**
   - Organized by category
   - Bullet points with explanations
   - Technical details where relevant

6. **Installation**
   - Prerequisites
   - Step-by-step setup instructions
   - Virtual environment setup (for Python projects)

7. **Usage**
   - Basic usage examples
   - Common commands
   - Controls (if interactive)

8. **Documentation**
   - Links to guides, tutorials, and reference docs
   - Table format for easy navigation

9. **Roadmap**
   - Vision and strategic direction
   - Current status
   - Planned features

10. **Related Projects**
    - Links to other jcaldwell-labs projects
    - Integration points

11. **Community**
    - How to get help
    - Discussion forums or chat
    - Ways to connect

12. **Contributing**
    - Ways to contribute
    - Getting started steps
    - Development guidelines
    - Link to detailed dev docs

13. **License**
    - License type (MIT standard)

### AI Discoverability (llms.txt)

Every project should include an `llms.txt` file at the repository root for AI agent discoverability. This file should contain:

- **Project Description**: Clear summary of what the project does
- **Core Capabilities**: Detailed list of features and functionality
- **Quick Start**: Installation and basic usage
- **Commands & CLI**: All available commands and their usage
- **Use Cases**: Specific scenarios where the project is useful
- **Architecture**: High-level overview of structure and key components
- **Technology Stack**: Languages, frameworks, and dependencies
- **Key Technical Features**: Notable implementations or algorithms
- **Development Philosophy**: Core principles (if applicable)
- **Testing**: How to run tests and coverage expectations
- **Documentation**: Links to detailed guides
- **Related Projects**: Integration points with other projects
- **License**: License type
- **Repository URL**: Link to the GitHub repository

Format: Markdown with clear section headers (##). See atari-style/llms.txt for reference.

### CLAUDE.md for AI Development

Projects developed with AI assistance should include a `CLAUDE.md` file containing:

- Project overview and philosophy
- Technology stack
- Setup and installation
- Project architecture
- Development commands
- Guidelines for adding new features
- Input/control patterns
- Rendering guidelines
- Performance considerations
- Pre-commit checklist
- Code quality standards
- Testing standards

## Code Quality Standards

### Security Requirements

**HTML Output**: Always escape user data when generating HTML:
```python
import html
filename_safe = html.escape(filename)
f'<h2>{filename_safe}</h2>'  # Safe
```

**Path Validation**: Validate file paths to prevent traversal attacks:
```python
requested = (base_dir / user_path).resolve()
if not str(requested).startswith(str(base_dir.resolve())):
    return error_forbidden()
```

**Large Files**: Stream instead of loading into memory:
```python
CHUNK_SIZE = 8192
with open(path, 'rb') as f:
    while chunk := f.read(CHUNK_SIZE):
        output.write(chunk)
```

### Code Conventions

- **Constants**: Extract magic numbers as named constants
- **Imports**: Only import what you use; remove unused imports
- **Type Hints**: All public functions must have type hints (Python)
- **Docstrings**: Document public APIs with Args, Returns, and examples

### Testing Standards

- **Core modules**: 80% coverage minimum
- **Integration tests**: Required for all features (not just unit tests)
- **Edge cases**: Test empty inputs, missing dependencies, error conditions
- **Test data consistency**: Match test filenames/types to what's being tested

### Before Submitting PRs

1. **Run the code** - Actually execute and observe behavior
2. **Tests assert outcomes** - Every test should have meaningful assertions
3. **Input validation** - Validate user inputs at boundaries
4. **Cross-platform** - Ensure compatibility (Linux/macOS/Windows)
5. **Lint**: Run linter (e.g., `ruff check` for Python)
6. **Security audit**: Verify escaping, path validation, resource limits

## Repository Organization

### Directory Structure

```
project-root/
├── .github/
│   ├── workflows/           # CI/CD workflows
│   ├── templates/           # Issue/PR templates
│   ├── planning/            # Internal planning documents
│   ├── copilot-instructions.md  # GitHub Copilot guidance
│   └── ORG-GUIDELINES.md    # This file
├── docs/
│   ├── guides/              # How-to guides
│   ├── tutorials/           # Step-by-step tutorials
│   ├── reference/           # API/command reference
│   ├── architecture/        # Design documentation
│   ├── getting-started/     # New user onboarding
│   └── README.md            # Documentation hub
├── src/ or [project-name]/  # Source code
├── tests/                   # Test files
├── README.md                # Main documentation
├── CLAUDE.md                # AI development guide (if applicable)
├── PHILOSOPHY.md            # Core principles (if applicable)
├── llms.txt                 # AI discoverability
├── LICENSE                  # MIT license
└── requirements.txt         # Dependencies (Python projects)
```

### .github/planning/

Internal planning documents not visible to end users:
- Roadmaps
- Feature backlogs
- Test plans
- Architecture decision records (ADRs)
- Meeting notes

### .github/templates/

Reusable templates for:
- Issue templates
- PR templates
- Discussion templates

## Documentation Organization

### docs/ Structure

- **guides/**: Task-oriented how-to guides
- **tutorials/**: Learning-oriented step-by-step tutorials
- **reference/**: Information-oriented API/command documentation
- **architecture/**: System design and technical decisions
- **getting-started/**: New user onboarding
- **blog/** (optional): Articles, announcements, and posts

### Documentation Principles

1. **Show, Don't Tell**: Use examples and interactive demos
2. **Progressive Disclosure**: Start simple, provide depth for those who need it
3. **Searchable**: Use clear section headers and keywords
4. **AI-Friendly**: Structure for both human and AI consumption

## Git & Version Control

### Branch Naming

- `main` or `master` - Production-ready code
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `claude/description-XXXXX` - AI-assisted development branches

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Be specific: "Add BFS pathfinding for Pac-Man ghosts" not "Update game"
- Reference issues: "Fix #123: Resolve collision detection bug"

### Pull Requests

- Clear title describing the change
- Description with context and approach
- Screenshots/demos for visual changes
- Checklist of testing performed
- Link to related issues

## License

All jcaldwell-labs projects use the MIT License unless otherwise specified.

## Philosophy

### Unix Philosophy

Projects should follow Unix principles:
1. **Do one thing well**: Focus on a specific purpose
2. **Compose freely**: Work with other tools via standard interfaces
3. **Text streams**: Use text as universal interface where applicable

### AI-Native Development

Projects are designed for both human developers and AI assistants:
- Comprehensive documentation (CLAUDE.md)
- Clear code structure and naming
- Extensive inline comments for complex logic
- Pre-commit checklists to reduce review cycles

### Community-Driven

- Welcome contributions from all skill levels
- Provide clear onboarding documentation
- Respond to issues and PRs promptly
- Share knowledge and learn in public

## Continuous Improvement

These guidelines evolve with the organization. Suggestions for improvements are welcome via issues or PRs.

---

**Last Updated**: 2025-12-22
**Applies To**: All jcaldwell-labs projects
