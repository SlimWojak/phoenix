"""
Semantic Query — S37 Track D
============================

Query memory by meaning, not just keywords.
Returns DISTANCE SCORES, not "relevance" — no ranking by quality.

INVARIANTS:
  - INV-ATTR-NO-RANKING: Distance, not relevance
  - INV-SEMANTIC-NO-SINGLE-BEST: Unordered neighborhood
  - INV-SEMANTIC-POLARITY: Polar handling
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# CONSTANTS
# =============================================================================

ATHENA_ROOT = Path(__file__).parent
POLAR_PAIRS_PATH = ATHENA_ROOT / "polar_pairs.yaml"

DEFAULT_K = 5
MIN_DISTANCE_THRESHOLD = 0.20
DISTANCE_NOISE = 0.01
BAND_WIDTH = 0.05


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class SemanticResult:
    """
    Result of semantic search.

    Contains DISTANCE, not relevance/score/quality.
    """

    bead_id: str
    bead_type: str
    content_preview: str
    distance: float  # Lower = closer (NOT relevance!)
    is_ambiguous: bool = False
    ambiguity_reason: str = ""


@dataclass
class SemanticSearchResponse:
    """
    Response from semantic search.

    Results are "unordered neighborhood", not ranked.
    """

    query: str
    results: list[SemanticResult]
    result_type: str = "unordered_neighborhood"
    sort_declaration: str = "shuffled within distance bands (ascending)"
    k: int = DEFAULT_K


# =============================================================================
# FORBIDDEN PATTERNS
# =============================================================================

FORBIDDEN_PATTERNS = frozenset([
    "most relevant",
    "best match",
    "top results",
    "recommended",
    "most similar",
    "highest score",
    "best matching",
    "top match",
])


# =============================================================================
# SEMANTIC QUERY
# =============================================================================


class SemanticQuery:
    """
    Semantic query engine.

    Returns distance scores, not relevance.
    Results are unordered neighborhood, not ranked.

    INVARIANTS:
      - INV-ATTR-NO-RANKING: Distance only
      - INV-SEMANTIC-NO-SINGLE-BEST: No "top result"
      - INV-SEMANTIC-POLARITY: Flag polar opposites
    """

    def __init__(self) -> None:
        """Initialize semantic query."""
        self._polar_pairs: list[tuple[str, str]] = []
        self._min_distance_threshold = MIN_DISTANCE_THRESHOLD
        self._load_polar_pairs()

    def _load_polar_pairs(self) -> None:
        """Load polar pairs from config."""
        if POLAR_PAIRS_PATH.exists():
            with open(POLAR_PAIRS_PATH) as f:
                config = yaml.safe_load(f)
                pairs = config.get("polar_pairs", [])
                self._polar_pairs = [(p[0].lower(), p[1].lower()) for p in pairs]
                cfg = config.get("config", {})
                self._min_distance_threshold = cfg.get(
                    "min_distance_threshold", MIN_DISTANCE_THRESHOLD
                )
        else:
            # Default polar pairs
            self._polar_pairs = [
                ("bullish", "bearish"),
                ("long", "short"),
                ("buy", "sell"),
                ("support", "resistance"),
            ]

    def validate_query(self, query: str) -> tuple[bool, str]:
        """
        Validate query doesn't request ranking.

        Args:
            query: Query string

        Returns:
            (valid, error_message)
        """
        query_lower = query.lower()

        for pattern in FORBIDDEN_PATTERNS:
            if pattern in query_lower:
                return (
                    False,
                    f"Ranking language forbidden: '{pattern}'. "
                    "Use 'nearest neighbors' or 'unordered neighborhood'.",
                )

        return (True, "")

    def validate_sort_order(self, sort_order: str) -> tuple[bool, str]:
        """
        Validate sort order is ascending only.

        Args:
            sort_order: Requested sort order

        Returns:
            (valid, error_message)
        """
        sort_lower = sort_order.lower()

        if "desc" in sort_lower or "descending" in sort_lower:
            return (
                False,
                "Descending sort forbidden. "
                "INV-SEMANTIC-NO-SINGLE-BEST: ascending only.",
            )

        return (True, "")

    def check_polarity(
        self,
        query: str,
        result_content: str,
        distance: float,
    ) -> tuple[bool, str]:
        """
        Check for polar match at low distance.

        Args:
            query: Query string
            result_content: Result content
            distance: Embedding distance

        Returns:
            (is_ambiguous, reason)
        """
        if distance > self._min_distance_threshold:
            return (False, "")

        query_lower = query.lower()
        content_lower = result_content.lower()

        for term1, term2 in self._polar_pairs:
            # Query has term1, result has term2
            if term1 in query_lower and term2 in content_lower:
                return (
                    True,
                    f"Polar opposite '{term2}' found for query term '{term1}' "
                    f"at low distance {distance:.2f}",
                )
            # Query has term2, result has term1
            if term2 in query_lower and term1 in content_lower:
                return (
                    True,
                    f"Polar opposite '{term1}' found for query term '{term2}' "
                    f"at low distance {distance:.2f}",
                )

        return (False, "")

    def add_distance_noise(self, distance: float) -> float:
        """
        Add noise to distance to break mental ranking.

        Args:
            distance: Raw distance

        Returns:
            Distance with ±0.01 noise
        """
        rng = secrets.SystemRandom()
        noise = rng.uniform(-DISTANCE_NOISE, DISTANCE_NOISE)
        return round(distance + noise, 2)

    def shuffle_within_bands(
        self,
        results: list[SemanticResult],
    ) -> list[SemanticResult]:
        """
        Shuffle results within distance bands.

        Results with similar distances (±0.05) are shuffled.

        Args:
            results: Results to shuffle

        Returns:
            Shuffled results
        """
        if not results:
            return results

        # Sort by distance first
        sorted_results = sorted(results, key=lambda r: r.distance)

        # Group into bands
        bands: list[list[SemanticResult]] = []
        current_band: list[SemanticResult] = []
        band_start = sorted_results[0].distance if sorted_results else 0

        for result in sorted_results:
            if result.distance <= band_start + BAND_WIDTH:
                current_band.append(result)
            else:
                if current_band:
                    bands.append(current_band)
                current_band = [result]
                band_start = result.distance

        if current_band:
            bands.append(current_band)

        # Shuffle within each band
        rng = secrets.SystemRandom()
        shuffled: list[SemanticResult] = []
        for band in bands:
            rng.shuffle(band)
            shuffled.extend(band)

        return shuffled

    def search(
        self,
        query: str,
        beads: list[dict[str, Any]],
        k: int = DEFAULT_K,
    ) -> SemanticSearchResponse:
        """
        Perform semantic search.

        This is a simplified implementation without actual embeddings.
        Production would use sentence-transformers.

        Args:
            query: Search query
            beads: Beads to search
            k: Number of results

        Returns:
            SemanticSearchResponse (unordered neighborhood)
        """
        # Validate query
        valid, error = self.validate_query(query)
        if not valid:
            raise ValueError(error)

        results: list[SemanticResult] = []
        query_lower = query.lower()

        for bead in beads:
            # Simplified distance calculation (production would use embeddings)
            content = str(bead.get("content", "")).lower()
            assertion = str(bead.get("assertion", "")).lower()
            full_text = content + " " + assertion

            # Simple word overlap as proxy for distance
            query_words = set(query_lower.split())
            text_words = set(full_text.split())
            overlap = len(query_words & text_words)

            if overlap > 0:
                # Distance inversely proportional to overlap
                raw_distance = 1.0 / (1.0 + overlap)

                # Add noise
                distance = self.add_distance_noise(raw_distance)

                # Check polarity
                is_ambiguous, reason = self.check_polarity(
                    query, full_text, distance
                )

                # Skip ambiguous results
                if is_ambiguous:
                    continue

                results.append(SemanticResult(
                    bead_id=bead.get("bead_id", ""),
                    bead_type=bead.get("bead_type", ""),
                    content_preview=full_text[:100],
                    distance=distance,
                    is_ambiguous=is_ambiguous,
                    ambiguity_reason=reason,
                ))

        # Shuffle within bands
        shuffled = self.shuffle_within_bands(results)

        # Take top k (after shuffling)
        limited = shuffled[:k]

        return SemanticSearchResponse(
            query=query,
            results=limited,
            result_type="unordered_neighborhood",
            sort_declaration="shuffled within distance bands (ascending)",
            k=k,
        )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "SemanticQuery",
    "SemanticResult",
    "SemanticSearchResponse",
    "FORBIDDEN_PATTERNS",
]
