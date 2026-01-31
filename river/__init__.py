"""
Phoenix River Module — Data Ingestion and Storage
==================================================

Components:
- SyntheticRiver: Mock data for testing/development
- (Future) RiverReader: Real data from River DB

S42: SyntheticRiver extracted for offline use.
"""

from .synthetic_river import SyntheticRiver, create_synthetic_river

__all__ = [
    "SyntheticRiver",
    "create_synthetic_river",
]
