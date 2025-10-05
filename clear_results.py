"""Utility script to clean generated artifacts under results/."""

from __future__ import annotations

from pathlib import Path
import shutil

RESULT_DIRS = [
    Path("results/html"),
    Path("results/videos"),
    Path("results/frames"),
]


def remove_contents(directory: Path) -> None:
    """Delete every file and subdirectory inside the given directory."""
    if not directory.exists():
        return

    for path in directory.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path)


def main() -> None:
    for directory in RESULT_DIRS:
        remove_contents(directory)


if __name__ == "__main__":
    main()
