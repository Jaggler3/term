# Development Guide

This document explains how to set up and use the development tools for the piko project.

## Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set up pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Available Tools

### Code Formatting

- **Black**: Automatic code formatter that enforces consistent style
- **isort**: Sorts and organizes import statements

### Linting

- **Ruff**: Fast Python linter that replaces flake8, pylint, and more
- **MyPy**: Static type checker for Python

## Usage

### Using Make Commands

```bash
# Format code
make format

# Run linter
make lint

# Run type checker
make type-check

# Run all checks
make check-all
```

### Using the Development Script

```bash
# Format code
python dev.py format

# Run linter
python dev.py lint

# Run type checker
python dev.py typecheck

# Run all checks
python dev.py check

# Install dependencies
python dev.py install
```

### Using Individual Tools

```bash
# Format with Black
black .

# Sort imports with isort
isort .

# Lint with Ruff
ruff check .

# Type check with MyPy
mypy .
```

## Configuration

All tools are configured in `pyproject.toml`:

- **Black**: 88 character line length, Python 3.6+ compatibility
- **isort**: Configured to work with Black, recognizes `piko` as first-party
- **Ruff**: Includes common error codes, excludes build directories
- **MyPy**: Strict type checking with exceptions for external libraries

## VS Code Integration

The `.vscode/settings.json` file configures VS Code to:
- Use Black as the default formatter
- Enable Ruff and MyPy linting
- Format on save
- Organize imports on save

## Pre-commit Hooks

If you've installed pre-commit hooks, they will automatically:
- Format your code with Black
- Sort imports with isort
- Run Ruff with auto-fix
- Run MyPy type checking

This ensures all committed code follows the project's style guidelines.

## Troubleshooting

### MyPy Errors

If you get MyPy errors for external libraries, they're likely already configured to be ignored in `pyproject.toml`. If you add new dependencies, you may need to add them to the `[[tool.mypy.overrides]]` section.

### Ruff Errors

Ruff is configured to be quite strict. If you need to ignore specific rules for a line, use:
```python
# ruff: noqa: E501
```

For entire files, add them to the `[tool.ruff.per-file-ignores]` section in `pyproject.toml`. 