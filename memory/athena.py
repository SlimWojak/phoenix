"""
Athena — Memory Palace Query Engine
====================================

NL query → Query IR → SQL → capped results

INVARIANTS:
- INV-ATHENA-RO-1: Queries cannot modify data
- INV-ATHENA-CAP-1: Results capped at 100 rows, 2000 tokens
- INV-ATHENA-AUDIT-1: Every query has audit fields
- INV-ATHENA-IR-ONLY-1: SQL generated ONLY from QueryIR fields

Operator experience:
1. Olya asks memory question
2. Claude classifies as DISPATCH:QUERY_MEMORY
3. Athena queries beads
4. Lens injects results → Claude presents
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .bead_store import BeadStore
from .query_parser import QueryIR, QueryParser, Requester, ValidationResult

# =============================================================================
# CONSTANTS
# =============================================================================

# Result caps (INV-ATHENA-CAP-1)
MAX_ROWS = 100
MAX_TOKENS = 2000


# =============================================================================
# RESULT TYPES
# =============================================================================


@dataclass
class QueryResult:
    """Result of Athena query."""

    query_id: str
    status: str  # COMPLETE, FAILED, NO_RESULTS
    summary: str
    result_count: int
    bead_refs: list[str]  # bead_ids for cited results

    # Full results (optional)
    results: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    capped: bool = False
    total_found: int = 0
    tokens_used: int = 0

    # Errors
    errors: list[str] = field(default_factory=list)

    def to_summary(self, max_tokens: int = 500) -> str:
        """Generate summary for Lens injection."""
        if self.status == "FAILED":
            return f"Query failed: {'; '.join(self.errors)}"

        if self.status == "NO_RESULTS":
            return "No matching beads found."

        cap_note = f" (showing {self.result_count} of {self.total_found})" if self.capped else ""

        return f"""Found {self.result_count} beads{cap_note}.
{self.summary}"""


# =============================================================================
# ATHENA
# =============================================================================


class Athena:
    """
    Athena — Memory Palace Query Engine.

    Pipeline:
    1. Parse NL → Query IR (via QueryParser)
    2. Validate IR
    3. Generate SQL (deterministic, from IR only)
    4. Execute SQL (read-only via BeadStore)
    5. Cap results (100 rows, 2000 tokens)
    6. Compress to summary

    INVARIANT: INV-ATHENA-RO-1 — Read-only queries
    INVARIANT: INV-ATHENA-IR-ONLY-1 — SQL from IR only
    """

    def __init__(
        self,
        bead_store: BeadStore | None = None,
        parser: QueryParser | None = None,
    ) -> None:
        """
        Initialize Athena.

        Args:
            bead_store: BeadStore instance (creates new if None)
            parser: QueryParser instance (creates new if None)
        """
        self._store = bead_store or BeadStore(read_only=True)
        self._parser = parser or QueryParser()

    def query(
        self,
        query_text: str,
        session_id: str,
        requester: Requester = Requester.CLAUDE,
    ) -> QueryResult:
        """
        Execute memory query.

        Args:
            query_text: Natural language query
            session_id: Session identifier
            requester: Who is making the query

        Returns:
            QueryResult with summary and bead references
        """
        # 1. Parse NL → Query IR
        ir = self._parse_to_ir(query_text, requester)
        if ir is None:
            return self._fail_result("", ["Failed to parse query"])

        # 2. Validate IR
        validation = self._validate_ir(ir)
        if not validation.valid:
            return self._fail_result(ir.query_id, validation.errors)

        # 3. Generate SQL (INV-ATHENA-IR-ONLY-1)
        sql, params = self._generate_sql(ir)

        # 4. Execute SQL (read-only)
        try:
            results = self._execute(sql, params)
        except Exception as e:
            return self._fail_result(ir.query_id, [f"Query execution failed: {e}"])

        # 5. Cap results (INV-ATHENA-CAP-1)
        capped_results, capped, total_found = self._cap_results(results)

        # 6. Compress to summary
        summary, tokens_used = self._compress(capped_results)

        # No results case
        if not capped_results:
            return QueryResult(
                query_id=ir.query_id,
                status="NO_RESULTS",
                summary="No matching beads found. Try broadening your search.",
                result_count=0,
                bead_refs=[],
            )

        # Build result
        return QueryResult(
            query_id=ir.query_id,
            status="COMPLETE",
            summary=summary,
            result_count=len(capped_results),
            bead_refs=[r["bead_id"] for r in capped_results],
            results=capped_results,
            capped=capped,
            total_found=total_found,
            tokens_used=tokens_used,
        )

    def _parse_to_ir(
        self,
        text: str,
        requester: Requester,
    ) -> QueryIR | None:
        """Parse natural language to Query IR."""
        return self._parser.parse(text, requester)

    def _validate_ir(self, ir: QueryIR) -> ValidationResult:
        """Validate Query IR."""
        return self._parser.validate(ir)

    def _generate_sql(self, ir: QueryIR) -> tuple[str, tuple]:
        """
        Generate SQL from Query IR.

        INVARIANT: INV-ATHENA-IR-ONLY-1
        SQL generated ONLY from QueryIR fields, never from raw query text.
        All values are parameterized (no string interpolation).
        """
        conditions = []
        params: list[Any] = []

        # Bead type filter
        if ir.bead_types:
            placeholders = ",".join("?" * len(ir.bead_types))
            conditions.append(f"bead_type IN ({placeholders})")
            params.extend(bt.value for bt in ir.bead_types)

        # Pair filter (search in content JSON)
        if ir.pair_filter:
            pair_conditions = []
            for pair in ir.pair_filter:
                pair_conditions.append("content LIKE ?")
                params.append(f'%"{pair}"%')
            conditions.append(f"({' OR '.join(pair_conditions)})")

        # Keyword filter (search in content JSON)
        if ir.keywords:
            for keyword in ir.keywords:
                # Sanitized via validation (no SQL operators)
                conditions.append("content LIKE ?")
                params.append(f"%{keyword}%")

        # Date range filter
        if ir.date_range:
            if ir.date_range.start:
                conditions.append("timestamp_utc >= ?")
                params.append(ir.date_range.start.isoformat())
            if ir.date_range.end:
                conditions.append("timestamp_utc <= ?")
                params.append(ir.date_range.end.isoformat())

        # Build query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        limit = min(ir.limit, MAX_ROWS)

        # SQL generated from validated IR fields only (INV-ATHENA-IR-ONLY-1)
        sql = f"""
            SELECT bead_id, bead_type, timestamp_utc, content
            FROM beads
            WHERE {where_clause}
            ORDER BY timestamp_utc DESC
            LIMIT ?
        """  # noqa: S608
        params.append(limit + 1)  # +1 to detect if capped

        return sql, tuple(params)

    def _execute(self, sql: str, params: tuple) -> list[dict[str, Any]]:
        """Execute SQL query."""
        return self._store.query_sql(sql, params)

    def _cap_results(
        self,
        results: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], bool, int]:
        """
        Cap results at MAX_ROWS.

        Returns:
            (capped_results, was_capped, total_found)
        """
        total = len(results)
        capped = total > MAX_ROWS

        return results[:MAX_ROWS], capped, total

    def _compress(
        self,
        results: list[dict[str, Any]],
    ) -> tuple[str, int]:
        """
        Compress results to summary.

        Returns:
            (summary_text, tokens_used)
        """
        if not results:
            return "No results.", 0

        # Build summary
        lines = []

        # Group by bead type
        by_type: dict[str, list] = {}
        for r in results:
            bead_type = r.get("bead_type", "UNKNOWN")
            if bead_type not in by_type:
                by_type[bead_type] = []
            by_type[bead_type].append(r)

        for bead_type, beads in by_type.items():
            lines.append(f"**{bead_type}** ({len(beads)}):")

            for bead in beads[:5]:  # Max 5 per type in summary
                # Parse content
                content = bead.get("content", "{}")
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        content = {}

                # Extract relevant info based on type
                if bead_type == "HUNT":
                    hypothesis = content.get("hypothesis_text", "")[:50]
                    survivors = len(content.get("survivors", []))
                    lines.append(
                        f"  - {bead['bead_id']}: \"{hypothesis}...\" ({survivors} survivors)"
                    )

                elif bead_type == "CONTEXT_SNAPSHOT":
                    hypothesis = content.get("current_hypothesis", "")[:40]
                    lines.append(f"  - {bead['bead_id']}: {hypothesis}...")

                elif bead_type == "PERFORMANCE":
                    sharpe = content.get("metrics", {}).get("sharpe", "?")
                    lines.append(f"  - {bead['bead_id']}: Sharpe {sharpe}")

                else:
                    lines.append(f"  - {bead['bead_id']}")

            if len(beads) > 5:
                lines.append(f"  ... and {len(beads) - 5} more")

        summary = "\n".join(lines)

        # Estimate tokens (rough: 1 token ≈ 4 chars)
        tokens = len(summary) // 4

        # Truncate if over budget
        if tokens > MAX_TOKENS:
            # Truncate to fit
            max_chars = MAX_TOKENS * 4
            summary = summary[:max_chars] + "\n... (truncated)"
            tokens = MAX_TOKENS

        return summary, tokens

    def _fail_result(self, query_id: str, errors: list[str]) -> QueryResult:
        """Create failed query result."""
        return QueryResult(
            query_id=query_id or "unknown",
            status="FAILED",
            summary=f"Query failed: {'; '.join(errors)}",
            result_count=0,
            bead_refs=[],
            errors=errors,
        )
