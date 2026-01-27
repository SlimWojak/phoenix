"""
Phoenix Memory Module
=====================

Queryable memory palace — BeadStore + Athena.

Components:
- BeadStore: Bead persistence (SQLite + read-only query path)
- Athena: NL query → Query IR → SQL → capped results
- QueryParser: Natural language → Query IR

INVARIANTS:
- INV-ATHENA-RO-1: Queries cannot modify data
- INV-ATHENA-CAP-1: Results capped at 100 rows, 2000 tokens
- INV-ATHENA-AUDIT-1: Every query has audit fields
"""

from .athena import Athena, QueryResult
from .bead_store import BeadStore, BeadStoreError
from .query_parser import QueryIR, QueryParser

__all__ = [
    "BeadStore",
    "BeadStoreError",
    "QueryIR",
    "QueryParser",
    "Athena",
    "QueryResult",
]
