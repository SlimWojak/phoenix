"""
Pytest configuration for Phoenix tests.

Adds project root to sys.path for proper imports.
"""

import sys
from pathlib import Path

# Add phoenix root to path - must be at module level, before any imports
PHOENIX_ROOT = Path(__file__).resolve().parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))


# Configure pytest
def pytest_configure(config):
    """Configure pytest with phoenix root in path."""
    if str(PHOENIX_ROOT) not in sys.path:
        sys.path.insert(0, str(PHOENIX_ROOT))
