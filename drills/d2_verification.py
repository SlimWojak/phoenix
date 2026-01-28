#!/usr/bin/env python3
"""
D2 Verification Script — Mock Oracle Pipeline Validation
=========================================================

S34: D2 MOCK_ORACLE_PIPELINE_VALIDATION

Verifies all D2 invariants:
- INV-D2-FORMAT-1: Mock CSE schema == production CSE schema
- INV-D2-TRACEABLE-1: Evidence refs resolvable to conditions.yaml
- INV-D2-NO-INTELLIGENCE-1: Zero market analysis logic in mock
- INV-D2-NO-COMPOSITION-1: Whitelist gate IDs only
"""

import sys
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

import yaml  # noqa: E402 - Must be after sys.path modification


class D2Verification:
    """Run all D2 invariant tests."""

    def __init__(self):
        self.results = {}

    def test_inv_d2_format_1_schema_match(self) -> bool:
        """INV-D2-FORMAT-1: Mock CSE validates against production schema."""
        print("\n[INV-D2-FORMAT-1] Testing schema match...")

        # Use CSEValidator from mock_cse_generator (standalone)
        from mocks.mock_cse_generator import CSEValidator, MockCSEGenerator, Pair

        # Create mock CSE
        generator = MockCSEGenerator()
        cse = generator.create_cse_from_gate(
            gate_id="GATE-COND-001",
            pair=Pair.EURUSD,
        )
        cse_dict = cse.to_dict()

        # Validate against schema (returns tuple)
        valid, errors = CSEValidator.validate(cse_dict)

        if valid:
            print("  Mock CSE validates against schema: PASS")
        else:
            print(f"  Validation errors: {errors}")

        return valid

    def test_inv_d2_traceable_1_refs_resolvable(self) -> bool:
        """INV-D2-TRACEABLE-1: Evidence refs resolvable."""
        print("\n[INV-D2-TRACEABLE-1] Testing evidence traceability...")

        from mocks.mock_cse_generator import MockCSEGenerator, Pair

        # Create mock CSE
        generator = MockCSEGenerator()
        cse = generator.create_cse_from_gate(
            gate_id="GATE-COND-001",
            pair=Pair.EURUSD,
        )
        cse_dict = cse.to_dict()

        # Check evidence refs are present and resolvable
        mock_meta = cse_dict.get("_mock_metadata", {})
        gate_ref = mock_meta.get("gate_ref", {})

        print(f"  Gate ref present: {bool(gate_ref)}")

        if gate_ref:
            gate_id = gate_ref.get("gate_id", "")
            source = gate_ref.get("source", "")
            print(f"    Gate ID: {gate_id}")
            print(f"    Source: {source}")

            # Check source file exists
            if source == "conditions.yaml":
                conditions_path = PHOENIX_ROOT / "cso" / "knowledge" / "conditions.yaml"
                resolved = conditions_path.exists()
                print(f"    Source file exists: {resolved}")
                return resolved

        return False

    def test_inv_d2_no_intelligence_1_no_market_logic(self) -> bool:
        """INV-D2-NO-INTELLIGENCE-1: Zero market analysis logic."""
        print("\n[INV-D2-NO-INTELLIGENCE-1] Testing no market logic...")

        from mocks.mock_cse_generator import MockCSEGenerator, Pair

        generator = MockCSEGenerator()

        # Generate CSEs for different pairs - prices should be static
        prices = {}
        for pair in [Pair.EURUSD, Pair.GBPUSD, Pair.USDJPY]:
            cse = generator.create_cse_from_gate(
                gate_id="GATE-COND-001",
                pair=pair,
            )
            prices[pair.value] = cse.parameters.entry

        # Prices should match DEFAULT_PRICES (static, no intelligence)
        expected = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2700,
            "USDJPY": 150.00,
        }

        matches = all(prices.get(pair) == expected.get(pair) for pair in expected)

        print(f"  Static prices match defaults: {matches}")
        for pair, price in prices.items():
            exp = expected.get(pair, "N/A")
            status = "✓" if price == exp else "✗"
            print(f"    {pair}: {price} (expected: {exp}) {status}")

        # Check confidence is static
        cse = generator.create_cse_from_gate("GATE-COND-001", Pair.EURUSD)
        static_confidence = cse.confidence == 0.75  # Default value
        print(f"  Static confidence (0.75): {static_confidence}")

        return matches and static_confidence

    def test_inv_d2_no_composition_1_whitelist_only(self) -> bool:
        """INV-D2-NO-COMPOSITION-1: Whitelist gate IDs only."""
        print("\n[INV-D2-NO-COMPOSITION-1] Testing whitelist enforcement...")

        from mocks.mock_cse_generator import MockCSEGenerator, Pair

        generator = MockCSEGenerator()

        # Valid gate IDs from conditions.yaml
        valid_gates = generator.valid_gate_ids
        print(f"  Valid gate IDs: {valid_gates}")

        # Test valid gate
        try:
            generator.create_cse_from_gate("GATE-COND-001", Pair.EURUSD)
            valid_accepted = True
            print("  Valid gate accepted: ✓")
        except ValueError:
            valid_accepted = False
            print("  Valid gate accepted: ✗")

        # Test invalid gate - should be rejected
        try:
            generator.create_cse_from_gate("FAKE-GATE-999", Pair.EURUSD)
            invalid_rejected = False
            print("  Invalid gate rejected: ✗ (should have been rejected)")
        except ValueError as e:
            invalid_rejected = True
            print(f"  Invalid gate rejected: ✓ ({e})")

        # Test composite gate attempt (synthesis) - should be rejected
        try:
            generator.create_cse_from_gate("GATE-COND-001+GATE-COND-002", Pair.EURUSD)
            composite_rejected = False
            print("  Composite gate rejected: ✗")
        except ValueError:
            composite_rejected = True
            print("  Composite gate rejected: ✓")

        return valid_accepted and invalid_rejected and composite_rejected

    def test_gate_d2_1_gate_to_cse(self) -> bool:
        """GATE_D2_1: Gate from conditions.yaml → valid CSE."""
        print("\n[GATE_D2_1] Testing gate → CSE pipeline...")

        from mocks.mock_cse_generator import GateLoader, MockCSEGenerator, Pair

        # Load gates
        loader = GateLoader()
        gates = loader.valid_gate_ids
        print(f"  Gates loaded: {len(gates)}")

        # Generate CSE from each gate
        generator = MockCSEGenerator()
        all_valid = True

        for gate_id in gates:
            try:
                cse = generator.create_cse_from_gate(gate_id, Pair.EURUSD)
                errors = cse.validate()
                if errors:
                    print(f"  {gate_id}: INVALID ({errors})")
                    all_valid = False
                else:
                    print(f"  {gate_id}: ✓ valid CSE")
            except Exception as e:
                print(f"  {gate_id}: ERROR ({e})")
                all_valid = False

        return all_valid

    def test_gate_d2_2_cse_validates_routes(self) -> bool:
        """GATE_D2_2: CSE validates and routes to approval."""
        print("\n[GATE_D2_2] Testing CSE validation + routing...")

        from mocks.mock_cse_generator import CSEValidator, MockCSEGenerator, Pair

        # Create CSE
        generator = MockCSEGenerator()
        cse = generator.create_cse_from_gate("GATE-COND-001", Pair.EURUSD)
        cse_dict = cse.to_dict()

        # Validate using standalone validator
        valid, errors = CSEValidator.validate(cse_dict)

        print(f"  Validation passed: {valid}")
        if errors:
            print(f"  Errors: {errors}")

        # Check routing capability (has required fields for D1 watcher)
        has_type = cse_dict.get("source") is not None
        has_params = cse_dict.get("parameters") is not None
        has_evidence = cse_dict.get("evidence_hash") is not None

        print("  Has routing fields:")
        print(f"    source: {has_type}")
        print(f"    parameters: {has_params}")
        print(f"    evidence_hash: {has_evidence}")

        routable = has_type and has_params and has_evidence

        return valid and routable

    def test_gate_d2_3_t2_evidence_display(self) -> bool:
        """GATE_D2_3: T2 UI shows evidence from 5-drawer refs."""
        print("\n[GATE_D2_3] Testing T2 evidence display...")

        from approval.evidence import CSEEvidenceBuilder, EvidenceDisplay
        from mocks.mock_cse_generator import MockCSEGenerator, Pair

        # Create CSE
        generator = MockCSEGenerator()
        cse = generator.create_cse_from_gate("GATE-COND-001", Pair.EURUSD)
        cse_dict = cse.to_dict()

        # Build evidence
        builder = CSEEvidenceBuilder()
        evidence = builder.build_from_cse(cse_dict)

        # Check gate evidence present
        has_gate_evidence = evidence.gate_evidence is not None
        print(f"  Gate evidence present: {has_gate_evidence}")

        if evidence.gate_evidence:
            print(f"    Gate ID: {evidence.gate_evidence.gate_id}")
            print(f"    Requirements: {len(evidence.gate_evidence.requirements)}")
            print(f"    Resolved: {evidence.gate_evidence.resolved}")

        # Display formats
        markdown = EvidenceDisplay.to_markdown(evidence)
        compact = EvidenceDisplay.to_compact(evidence)

        has_markdown = "5-Drawer Gate Evidence" in markdown
        has_compact = "GATE-COND-001" in compact

        print(f"  Markdown includes gate: {has_markdown}")
        print(f"  Compact includes gate: {has_compact}")

        return has_gate_evidence and has_markdown and has_compact

    def test_gate_d2_4_schema_consistency(self) -> bool:
        """GATE_D2_4: Mock CSE schema == production CSE schema."""
        print("\n[GATE_D2_4] Testing schema consistency...")

        from mocks.mock_cse_generator import MockCSEGenerator, Pair

        # Generate mock CSE
        generator = MockCSEGenerator()
        cse = generator.create_cse_from_gate("GATE-COND-001", Pair.EURUSD)
        mock_cse = cse.to_dict()

        # Check against cse_schema.yaml
        schema_path = PHOENIX_ROOT / "schemas" / "cse_schema.yaml"
        if not schema_path.exists():
            print(f"  Schema file not found: {schema_path}")
            return False

        with open(schema_path) as f:
            schema = yaml.safe_load(f)

        cse_fields = schema.get("cse_fields", {})
        required_fields = [name for name, defn in cse_fields.items() if defn.get("required", False)]

        # Check all required fields present
        missing = [f for f in required_fields if f not in mock_cse]
        if missing:
            print(f"  Missing required fields: {missing}")
            return False

        print(f"  All {len(required_fields)} required fields present: ✓")

        # Check field types match
        type_matches = True
        for field_name, field_def in cse_fields.items():
            if field_name in mock_cse:
                expected_type = field_def.get("type", "")
                value = mock_cse[field_name]

                if expected_type == "string" and not isinstance(value, str):
                    print(f"    {field_name}: expected string, got {type(value)}")
                    type_matches = False
                elif expected_type == "float" and not isinstance(value, (int, float)):
                    print(f"    {field_name}: expected float, got {type(value)}")
                    type_matches = False

        print(f"  Field types match: {type_matches}")

        return type_matches

    def run_all(self):
        """Run all verification tests."""
        print("=" * 60)
        print("D2 VERIFICATION: MOCK ORACLE PIPELINE")
        print("=" * 60)

        tests = [
            ("INV-D2-FORMAT-1 (schema match)", self.test_inv_d2_format_1_schema_match),
            ("INV-D2-TRACEABLE-1 (refs resolvable)", self.test_inv_d2_traceable_1_refs_resolvable),
            ("INV-D2-NO-INTELLIGENCE-1", self.test_inv_d2_no_intelligence_1_no_market_logic),
            ("INV-D2-NO-COMPOSITION-1", self.test_inv_d2_no_composition_1_whitelist_only),
            ("GATE_D2_1 (gate → CSE)", self.test_gate_d2_1_gate_to_cse),
            ("GATE_D2_2 (CSE validates + routes)", self.test_gate_d2_2_cse_validates_routes),
            ("GATE_D2_3 (T2 evidence display)", self.test_gate_d2_3_t2_evidence_display),
            ("GATE_D2_4 (schema consistency)", self.test_gate_d2_4_schema_consistency),
        ]

        for name, test_fn in tests:
            try:
                result = test_fn()
                self.results[name] = result
            except Exception as e:
                print(f"\n[{name}] ERROR: {e}")
                import traceback

                traceback.print_exc()
                self.results[name] = False

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)

        for name, result in self.results.items():
            status = "PASS ✓" if result else "FAIL ✗"
            print(f"  {name}: {status}")

        print()
        print(f"Results: {passed}/{total}")

        if passed == total:
            print("D2 VERIFICATION: ALL PASS ✓")
            return True
        else:
            print("D2 VERIFICATION: SOME FAILED ✗")
            return False


if __name__ == "__main__":
    verifier = D2Verification()
    success = verifier.run_all()
    sys.exit(0 if success else 1)
