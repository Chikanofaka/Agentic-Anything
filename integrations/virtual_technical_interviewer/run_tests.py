#!/usr/bin/env python3
"""Run TIA tests from any working directory, using only the standard library."""
from pathlib import Path
import unittest


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
