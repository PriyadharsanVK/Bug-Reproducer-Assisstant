from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on the Python path for all tests
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))
