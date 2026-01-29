"""
CFP Test Configuration
======================

Ensures phoenix root is in path for imports.
"""

import sys
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))
