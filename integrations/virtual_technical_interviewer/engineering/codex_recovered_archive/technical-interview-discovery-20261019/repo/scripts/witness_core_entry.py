"""Entry point for the standalone HAL worker. Never stores API credentials.

Build with PyInstaller on the target macOS architecture. The Python process is
still a trusted local HAL Core: it does not execute arbitrary downloaded code.
"""
from hal_core.interactive import main

if __name__ == "__main__":
    raise SystemExit(main())
