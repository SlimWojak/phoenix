"""
Phoenix River Module — Data Ingestion and Storage
==================================================

Components:
- SyntheticRiver: Mock data for testing/development
- schema: RAW_BAR_SCHEMA, validation, hash computation
- writer: RiverWriter (IBKR → daily parquet)
- reader: RiverReader (DuckDB query layer)
- streamer: RiverStreamer (live 1m bars)
- seam: Cross-source reconciliation
- nex_ingestor: NEX historical data → River with source tags

S42: SyntheticRiver extracted for offline use.
S51: River foundation — schema, writer, NEX ingestor.
S52: Canonical exports (RISK-6 fix).
"""

from .reader import RiverReader
from .schema import RAW_BAR_SCHEMA, compute_bar_hashes, get_river_root, validate_raw_bars
from .seam import generate_report, reconcile_all, reconcile_pair
from .streamer import RiverStreamer
from .synthetic_river import SyntheticRiver, create_synthetic_river
from .writer import RiverWriter

__all__ = [
    "SyntheticRiver",
    "create_synthetic_river",
    "RAW_BAR_SCHEMA",
    "compute_bar_hashes",
    "validate_raw_bars",
    "get_river_root",
    "RiverReader",
    "RiverWriter",
    "RiverStreamer",
    "reconcile_pair",
    "reconcile_all",
    "generate_report",
]
