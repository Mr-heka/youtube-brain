#!/usr/bin/env python3
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Run the fictional fixture suite with Python socket access disabled."""
from pathlib import Path
import sys
import unittest

import offline_guard.sitecustomize  # noqa: F401 - importing installs the guard


def main():
    tests = Path(sys.argv[1]).resolve()
    suite = unittest.defaultTestLoader.discover(str(tests), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
