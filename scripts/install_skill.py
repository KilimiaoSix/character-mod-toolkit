#!/usr/bin/env python3
"""Copy this skill into a Codex project's .agents/skills directory."""
import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="an existing project directory")
    args = parser.parse_args()
    project = args.project.resolve()
    if not project.is_dir():
        parser.error(f"Project directory does not exist: {project}")
    source = Path(__file__).resolve().parents[1] / "skills" / "character-mod-toolkit"
    destination = project / ".agents" / "skills" / source.name
    if destination.exists() or destination.is_symlink():
        parser.error(f"Existing skill must be reviewed before updating: {destination}")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    print(destination)


if __name__ == "__main__":
    main()
