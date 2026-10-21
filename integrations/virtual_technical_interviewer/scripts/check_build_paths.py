"""Fail before any compiler/directory writes through symlinked generated paths."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
paths = [
    root / ".build-cache", root / "dist",
    root / "dist/Technical Interview Lab.app",
    root / "dist/Technical Interview Lab.app/Contents",
    root / "dist/Technical Interview Lab.app/Contents/MacOS",
    root / "dist/Technical Interview Lab.app/Contents/Resources",
    root / "dist/Technical Interview Lab.app/Contents/MacOS/TechnicalInterviewLab",
]
for path in paths:
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        sys.exit("UNSAFE_BUILD_PATH")
    if path.exists() and path != paths[-1] and not path.is_dir():
        sys.exit("INVALID_BUILD_DIRECTORY")
