"""
Test CSO Draft Beads — Verify S27 CSO emits DRAFT only.

SPRINT: S27.0
EXIT_GATE: draft_only
INVARIANT: INV-CSO-DRAFT-ONLY
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class TestCSODraftBeads:
    """Test CSO only creates DRAFT beads."""
    
    def test_factory_creates_draft_decision(self):
        """BeadFactory creates DRAFT decision beads."""
        from cso import BeadFactory, BeadStatus
        
        factory = BeadFactory(source_module='test')
        
        bead = factory.create_decision_bead(
            symbol='EURUSD',
            direction='LONG',
            confidence=0.8,
            gate_result={'q1': True, 'q2': True, 'q3': True, 'q4': True},
            state_hash='abc123'
        )
        
        assert bead.status == BeadStatus.DRAFT
    
    def test_factory_creates_draft_observation(self):
        """BeadFactory creates DRAFT observation beads."""
        from cso import BeadFactory, BeadStatus
        
        factory = BeadFactory(source_module='test')
        
        bead = factory.create_observation_bead(
            symbol='EURUSD',
            observation_type='fvg',
            details={'direction': 'bull'},
            state_hash='abc123'
        )
        
        assert bead.status == BeadStatus.DRAFT
    
    def test_factory_creates_draft_comprehension(self):
        """BeadFactory creates DRAFT comprehension beads."""
        from cso import BeadFactory, BeadStatus
        
        factory = BeadFactory(source_module='test')
        
        bead = factory.create_comprehension_bead(
            symbol='SYSTEM',
            understanding={'htf_bias': 'bullish'},
            state_hash='abc123'
        )
        
        assert bead.status == BeadStatus.DRAFT
    
    def test_cannot_create_certified_bead(self):
        """Cannot create CERTIFIED bead in S27."""
        from cso import Bead, BeadType, BeadStatus, BeadStatusViolation
        
        with pytest.raises(BeadStatusViolation) as exc:
            Bead(
                bead_id='TEST-001',
                bead_type=BeadType.DECISION,
                status=BeadStatus.CERTIFIED,  # FORBIDDEN in S27
                created_at=datetime.now(timezone.utc),
                expires_at=None,
                symbol='EURUSD',
                content={},
                comprehension_hash='',
                source_module='test',
                source_state_hash='abc123',
            )
        
        assert exc.value.attempted_status == 'CERTIFIED'
    
    def test_cannot_create_rejected_bead(self):
        """Cannot create REJECTED bead directly."""
        from cso import Bead, BeadType, BeadStatus, BeadStatusViolation
        
        with pytest.raises(BeadStatusViolation):
            Bead(
                bead_id='TEST-001',
                bead_type=BeadType.DECISION,
                status=BeadStatus.REJECTED,  # NOT DRAFT
                created_at=datetime.now(timezone.utc),
                expires_at=None,
                symbol='EURUSD',
                content={},
                comprehension_hash='',
                source_module='test',
                source_state_hash='abc123',
            )
    
    def test_observer_emits_draft_only(self):
        """CSOObserver only emits DRAFT beads."""
        from cso import CSOObserver, BeadStatus
        
        observer = CSOObserver()
        observer._bead_factory = __import__('cso').BeadFactory(source_module='test')
        observer._beads_emitted = []
        observer._observation_count = 0
        
        # Create test bar with pattern
        bar = {
            'symbol': 'EURUSD',
            'structure_break_up': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        # Mock check_halt to avoid initialization requirement
        observer.check_halt = lambda: None
        
        bead = observer.observe_bar(bar)
        
        if bead:
            assert bead.status == BeadStatus.DRAFT


class TestBeadContent:
    """Test bead content structure."""
    
    def test_decision_bead_has_direction(self):
        """Decision bead contains direction."""
        from cso import BeadFactory
        
        factory = BeadFactory(source_module='test')
        bead = factory.create_decision_bead(
            symbol='EURUSD',
            direction='LONG',
            confidence=0.75,
            gate_result={},
            state_hash='abc123'
        )
        
        assert 'direction' in bead.content
        assert bead.content['direction'] == 'LONG'
    
    def test_decision_bead_has_confidence(self):
        """Decision bead contains confidence."""
        from cso import BeadFactory
        
        factory = BeadFactory(source_module='test')
        bead = factory.create_decision_bead(
            symbol='EURUSD',
            direction='SHORT',
            confidence=0.65,
            gate_result={},
            state_hash='abc123'
        )
        
        assert 'confidence' in bead.content
        assert bead.content['confidence'] == 0.65
    
    def test_bead_has_comprehension_hash(self):
        """Bead has computed comprehension hash."""
        from cso import BeadFactory
        
        factory = BeadFactory(source_module='test')
        bead = factory.create_decision_bead(
            symbol='EURUSD',
            direction='NEUTRAL',
            confidence=0.5,
            gate_result={},
            state_hash='abc123'
        )
        
        assert bead.comprehension_hash
        assert len(bead.comprehension_hash) == 16
