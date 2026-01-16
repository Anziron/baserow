"""
Pytest configuration for Access Control plugin tests.
"""

import sys
from pathlib import Path

import pytest

# Add the source directory to the Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
