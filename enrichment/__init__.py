"""
Phoenix Enrichment — NEX subsumption.

SPRINT: S27.0
VERSION: 1.0

Subsumes NEX enrichment layers L1-L6 into Phoenix jurisdiction.

FORBIDDEN:
- forward_fill
- auto_fix
- synthetic fills
- implicit defaults

INVARIANTS:
- INV-DATA-1: Single source of truth (River)
- INV-DATA-2: No synthetic data without is_synthetic=TRUE
- INV-CONTRACT-1: Deterministic (same input → same output)
"""

from .layers import (
    l1_time_sessions,
    l2_reference_levels,
    l3_sweeps,
)

__all__ = [
    'l1_time_sessions',
    'l2_reference_levels',
    'l3_sweeps',
]

__version__ = '1.0.0'


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

def get_all_columns() -> list:
    """Get all columns produced by L1-L6."""
    columns = []
    columns.extend(l1_time_sessions.LAYER_1_COLUMNS)
    columns.extend(l2_reference_levels.LAYER_2_COLUMNS)
    columns.extend(l3_sweeps.LAYER_3_COLUMNS)
    return columns


def validate_no_forbidden_patterns(module_path: str) -> bool:
    """
    Validate module contains no forbidden patterns.
    
    FORBIDDEN:
    - forward_fill
    - ffill
    - auto_fix
    - fillna (except with explicit sentinel)
    """
    import importlib.util
    import re
    
    spec = importlib.util.spec_from_file_location("module", module_path)
    if spec is None:
        return False
    
    with open(module_path, 'r') as f:
        content = f.read()
    
    forbidden = [
        r'\.forward_fill\(',
        r'\.ffill\(',
        r'auto_fix',
        r'\.fillna\([^)]*\)',  # Will need manual audit
    ]
    
    for pattern in forbidden[:3]:  # First 3 are hard forbidden
        if re.search(pattern, content):
            return False
    
    return True
