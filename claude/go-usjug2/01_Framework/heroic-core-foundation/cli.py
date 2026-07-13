#!/usr/bin/env python3
"""Thin wrapper so `python cli.py` works the same as `python foundation.py`."""
from foundation import main
import sys

if __name__ == "__main__":
    sys.exit(main())
