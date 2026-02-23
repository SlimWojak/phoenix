"""
CSO Test Configuration — S36
"""

import sys
from pathlib import Path

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))
