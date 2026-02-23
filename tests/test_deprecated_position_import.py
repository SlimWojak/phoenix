"""
S52 T1: Verify old position import raises ImportError.

EXIT_GATE: T1_SINGLE_FSM
Proof: importing execution.position hard-fails with deprecation message.
"""

import pytest


class TestDeprecatedPositionImport:
    """Old import path must raise ImportError."""

    def test_direct_import_raises(self):
        """Importing execution.position raises ImportError."""
        with pytest.raises(ImportError, match="DEPRECATED"):
            import execution.position  # noqa: F401

    def test_from_import_raises(self):
        """from execution.position import X raises ImportError."""
        with pytest.raises(ImportError, match="DEPRECATED"):
            from execution.position import Position  # noqa: F401

    def test_canonical_import_works(self):
        """Canonical import from execution.positions works."""
        from execution.positions import Position, PositionLifecycle, PositionState

        assert Position is not None
        assert PositionState is not None
        assert PositionLifecycle is not None

    def test_paper_import_works(self):
        """Paper broker import works."""
        from execution.positions.paper import (
            PaperPosition,
            PaperPositionRegistry,
            PaperPositionState,
        )

        assert PaperPosition is not None
        assert PaperPositionState is not None
        assert PaperPositionRegistry is not None
