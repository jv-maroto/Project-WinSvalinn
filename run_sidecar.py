"""Convenience launcher: `python run_sidecar.py` from the project root.

Equivalent to `cd src && python -m sidecar` but doesn't require changing
directories or setting PYTHONPATH manually.
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "src"))

from sidecar.__main__ import main

if __name__ == "__main__":
    main()
