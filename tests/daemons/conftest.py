"""
Test configuration for daemons tests.

Ensures phoenix root is in sys.path for imports.
"""

import sys
from pathlib import Path

# Add phoenix root to path for imports
_PHOENIX_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHOENIX_ROOT))
