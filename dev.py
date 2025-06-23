#!/usr/bin/env python3
"""
Development helper script for the piko project.
Provides easy access to formatting and linting commands.
"""

import subprocess
import sys
from typing import List


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"Running {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stdout)
        print(e.stderr)
        return False


def main():
    """Main function to handle development commands."""
    if len(sys.argv) < 2:
        print("Usage: python dev.py <command>")
        print("Commands:")
        print("  format    - Format code with black and isort")
        print("  lint      - Run ruff linter")
        print("  typecheck - Run mypy type checker")
        print("  check     - Run all checks (format, lint, typecheck)")
        print("  install   - Install development dependencies")
        sys.exit(1)

    command = sys.argv[1]

    if command == "format":
        success = True
        success &= run_command(["black", "."], "Black formatter")
        success &= run_command(["isort", "."], "isort import sorter")
        sys.exit(0 if success else 1)

    elif command == "lint":
        success = run_command(["ruff", "check", "."], "Ruff linter")
        sys.exit(0 if success else 1)

    elif command == "typecheck":
        success = run_command(["mypy", "."], "MyPy type checker")
        sys.exit(0 if success else 1)

    elif command == "check":
        success = True
        success &= run_command(["black", "--check", "."], "Black check")
        success &= run_command(["isort", "--check-only", "."], "isort check")
        success &= run_command(["ruff", "check", "."], "Ruff linter")
        success &= run_command(["mypy", "."], "MyPy type checker")
        sys.exit(0 if success else 1)

    elif command == "install":
        print("Installing development dependencies...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        print("✅ Development dependencies installed")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
