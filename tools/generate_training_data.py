"""
Training Data Generator — S41 Track A Phase 2B
===============================================

Generates training dataset for SLM distillation:
- Constitutional examples (positive): Valid narrator outputs
- Heresy examples (negative): Violated outputs with injected violations

INVARIANTS VALIDATED:
  INV-SLM-READONLY-1: Dataset teaches classification, not creation
  INV-NARRATOR-1: FORBIDDEN_WORDS form negative examples

Date: 2026-01-23
Sprint: S41 Phase 2B
"""

from __future__ import annotations

import json
import random
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from narrator.templates import FORBIDDEN_WORDS, MANDATORY_FACTS_BANNER


# =============================================================================
# DATASET SCHEMA
# =============================================================================


@dataclass
class TrainingExample:
    """Single training example for SLM distillation."""

    id: str
    input: str
    output: str
    category: str  # "constitutional" or "heresy"
    reason_code: str | None = None
    source: str = "generated"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TrainingExample":
        return cls(**d)


@dataclass
class TrainingDataset:
    """Complete training dataset with metadata."""

    version: str
    created_at: str
    invariant_freeze_hash: str
    examples: list[TrainingExample]
    metadata: dict = field(default_factory=dict)

    def to_json(self, path: Path) -> None:
        """Save dataset to JSON file."""
        data = {
            "version": self.version,
            "created_at": self.created_at,
            "invariant_freeze_hash": self.invariant_freeze_hash,
            "metadata": self.metadata,
            "examples": [e.to_dict() for e in self.examples],
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def from_json(cls, path: Path) -> "TrainingDataset":
        """Load dataset from JSON file."""
        data = json.loads(path.read_text())
        return cls(
            version=data["version"],
            created_at=data["created_at"],
            invariant_freeze_hash=data["invariant_freeze_hash"],
            metadata=data.get("metadata", {}),
            examples=[TrainingExample.from_dict(e) for e in data["examples"]],
        )


# =============================================================================
# CONSTITUTIONAL TEMPLATES (POSITIVE EXAMPLES)
# =============================================================================


CONSTITUTIONAL_TEMPLATES = [
    # Briefing outputs
    """OINK OINK MOTHERFUCKER! 🐗🔥
FACTS_ONLY — NO INTERPRETATION

═══════════════════════════════════════
         MORNING BRIEFING
═══════════════════════════════════════
{timestamp}

SYSTEM STATUS
─────────────────────────────────────
  STATE:      {state}
  MODE:       {mode}
  PHASE:      {phase}
  KILL_FLAGS: {kill_flags}

POSITIONS
─────────────────────────────────────
  OPEN:       {open_positions}
  DAILY P&L:  {pnl}

═══════════════════════════════════════
The boar watches. The floor holds.
═══════════════════════════════════════""",

    # Health outputs
    """FACTS_ONLY — NO INTERPRETATION

HEALTH SNAPSHOT
─────────────────────────────────────
  RIVER:      {river_status}
  STALENESS:  {staleness}
  SUPERVISOR: {supervisor_state}
  IBKR:       {ibkr_connected}
  HEARTBEAT:  {heartbeat}
  CIRCUITS:   {circuits_closed}/{circuits_total} closed
─────────────────────────────────────""",

    # CSO outputs
    """FACTS_ONLY — NO INTERPRETATION

CSO GATE STATUS
─────────────────────────────────────
  {pair}: gates_passed=[{gates}]
  BIAS: {bias}
  REGIME: {regime}
─────────────────────────────────────""",

    # Trade event
    """FACTS_ONLY — NO INTERPRETATION

TRADE EVENT
─────────────────────────────────────
  ACTION:   {action}
  PAIR:     {pair}
  DIRECTION: {direction}
  ENTRY:    {entry}
  STOP:     {stop}
  TARGET:   {target}
  RISK:     {risk}%
  GATES:    [{gates}]
  EVIDENCE: bead_{bead_id}
─────────────────────────────────────""",

    # Alert (new taxonomy)
    """FACTS_ONLY — NO INTERPRETATION

ALERT [{severity}]
─────────────────────────────────────
  COMPONENT: {component}
  EVENT:     {event}
  ACTION:    {action_taken}
  TIME:      {timestamp}
─────────────────────────────────────""",

    # Simple status
    """FACTS_ONLY — NO INTERPRETATION

STATUS: {status}
UPTIME: {uptime}h
TESTS:  {passed}/{total} passed""",

    # Position summary
    """FACTS_ONLY — NO INTERPRETATION

POSITION SUMMARY
  PAIR:     {pair}
  DIRECTION: {direction}
  ENTRY:    {entry}
  CURRENT:  {current}
  P&L:      {pnl}""",
]


# =============================================================================
# HERESY PATTERNS (NEGATIVE EXAMPLES)
# =============================================================================


HERESY_INJECTIONS = {
    "CAUSAL": [
        "because volatility decreased",
        "due to market conditions",
        "driven by sentiment",
        "caused by news events",
        "as a result of the trend",
        "therefore we see improvement",
        "consequently the system adapted",
        "leads to better performance",
        "results in higher returns",
        "the data suggests an improvement",
        "this indicates a change",
    ],
    "RANKING": [
        "the best setup today",
        "the worst performing pair",
        "ranked #1 in the portfolio",
        "top tier opportunity",
        "bottom of the list",
        "grade A setup",
        "superior to other pairs",
        "inferior performance compared",
    ],
    "SCORING": [
        "confidence score: 85%",
        "viability index: 0.72",
        "probability of success: 65%",
        "likelihood: high (78%)",
        "rating: 9/10",
        "quality score: 87/100",
        "setup confidence: HIGH",
    ],
    "RECOMMENDATION": [
        "you should take this trade",
        "consider entering here",
        "I recommend waiting",
        "suggest monitoring closely",
        "advise caution in this market",
        "might want to reduce exposure",
        "you could profit from this",
        "better to wait for confirmation",
        "prefer this setup over others",
        "avoid this pair today",
    ],
    "SYNTHESIS": [
        "I noticed the trend changing",
        "I observed unusual activity",
        "it appears the market is bullish",
        "seems like a reversal forming",
        "looks like consolidation ahead",
        "probably entering a new phase",
        "likely to continue higher",
        "unlikely to break support",
        "in my opinion, this setup is ideal",
        "I think the momentum is shifting",
        "I believe we're at a turning point",
    ],
    "ADJECTIVE": [
        "strong bullish momentum",
        "weak bearish structure",
        "safe entry zone",
        "unsafe market conditions",
        "good setup for entry",
        "bad risk/reward ratio",
        "excellent opportunity",
        "poor liquidity conditions",
        "optimal entry point",
        "suboptimal timing",
    ],
}


# Variations to inject at different positions
INJECTION_POSITIONS = ["start", "middle", "end"]


# =============================================================================
# DATA GENERATORS
# =============================================================================


def generate_constitutional_values() -> dict:
    """Generate random values for constitutional templates."""
    states = ["ARMED", "SHADOW", "HALTED", "INITIALIZING"]
    modes = ["LIVE", "PAPER", "BACKTEST", "REPLAY"]
    phases = ["EXECUTION", "MONITORING", "COLD_START", "SHUTDOWN"]
    pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD"]
    directions = ["LONG", "SHORT"]
    biases = ["BULLISH", "BEARISH", "NEUTRAL"]
    regimes = ["TRENDING", "RANGING", "VOLATILE", "QUIET"]
    actions = ["ENTRY", "EXIT", "STOP_HIT", "TARGET_HIT", "SCALE_OUT"]
    severities = ["CRITICAL", "WARNING", "INFO"]
    components = ["IBKR", "RIVER", "CSO", "SUPERVISOR", "GOVERNANCE"]
    events = ["DISCONNECTION", "STALE_DATA", "CIRCUIT_OPEN", "HALT_TRIGGERED"]
    action_takens = ["RECONNECTING", "ALERTING", "DEGRADING", "HALTING"]

    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "state": random.choice(states),
        "mode": random.choice(modes),
        "phase": random.choice(phases),
        "kill_flags": random.choice(["NONE", "MANUAL_HALT", "CIRCUIT_BREAK"]),
        "open_positions": random.randint(0, 5),
        "pnl": f"{'+' if random.random() > 0.4 else '-'}${random.randint(10, 5000):.2f}",
        "river_status": random.choice(["HEALTHY", "DEGRADED", "STALE"]),
        "staleness": f"{random.uniform(0.1, 5.0):.1f}s",
        "supervisor_state": random.choice(["RUNNING", "DEGRADED", "STARTING"]),
        "ibkr_connected": random.choice(["true", "false"]),
        "heartbeat": random.choice(["OK", "STALE", "MISSING"]),
        "circuits_closed": random.randint(0, 5),
        "circuits_total": 5,
        "pair": random.choice(pairs),
        "gates": ",".join(str(i) for i in random.sample(range(1, 8), random.randint(1, 5))),
        "bias": random.choice(biases),
        "regime": random.choice(regimes),
        "action": random.choice(actions),
        "direction": random.choice(directions),
        "entry": f"{random.uniform(1.0, 150.0):.5f}",
        "stop": f"{random.uniform(1.0, 150.0):.5f}",
        "target": f"{random.uniform(1.0, 150.0):.5f}",
        "current": f"{random.uniform(1.0, 150.0):.5f}",
        "risk": f"{random.uniform(0.5, 2.0):.1f}",
        "bead_id": hashlib.sha256(str(random.random()).encode()).hexdigest()[:8],
        "severity": random.choice(severities),
        "component": random.choice(components),
        "event": random.choice(events),
        "action_taken": random.choice(action_takens),
        "status": random.choice(["HEALTHY", "DEGRADED", "HALTED"]),
        "uptime": f"{random.uniform(0.1, 72.0):.1f}",
        "passed": random.randint(1200, 1400),
        "total": random.randint(1300, 1400),
    }


def generate_constitutional_examples(count: int = 500) -> Iterator[TrainingExample]:
    """Generate constitutional (positive) training examples."""
    for i in range(count):
        template = random.choice(CONSTITUTIONAL_TEMPLATES)
        values = generate_constitutional_values()

        try:
            content = template.format(**values)
        except KeyError:
            # If template has missing keys, generate new values
            values = generate_constitutional_values()
            content = template.format(**{k: values.get(k, "") for k in values})

        yield TrainingExample(
            id=f"constitutional_{i:04d}",
            input=content,
            output="VALID_FACTS",
            category="constitutional",
            source="template_generation",
            metadata={"template_index": CONSTITUTIONAL_TEMPLATES.index(template)},
        )


def inject_heresy(content: str, reason_code: str, position: str = "middle") -> str:
    """Inject heresy into constitutional content."""
    heresy_phrase = random.choice(HERESY_INJECTIONS[reason_code])
    lines = content.split("\n")

    if position == "start":
        # Inject after banner
        for i, line in enumerate(lines):
            if MANDATORY_FACTS_BANNER in line:
                lines.insert(i + 1, f"\nNote: {heresy_phrase.capitalize()}.\n")
                break
    elif position == "end":
        lines.append(f"\n{heresy_phrase.capitalize()}.")
    else:  # middle
        mid = len(lines) // 2
        lines.insert(mid, f"\n{heresy_phrase.capitalize()}.\n")

    return "\n".join(lines)


def generate_heresy_examples(count: int = 500) -> Iterator[TrainingExample]:
    """Generate heresy (negative) training examples."""
    reason_codes = list(HERESY_INJECTIONS.keys())

    for i in range(count):
        # Start with constitutional template
        template = random.choice(CONSTITUTIONAL_TEMPLATES)
        values = generate_constitutional_values()

        try:
            content = template.format(**values)
        except KeyError:
            values = generate_constitutional_values()
            content = template.format(**{k: values.get(k, "") for k in values})

        # Inject heresy
        reason_code = random.choice(reason_codes)
        position = random.choice(INJECTION_POSITIONS)
        poisoned_content = inject_heresy(content, reason_code, position)

        yield TrainingExample(
            id=f"heresy_{i:04d}",
            input=poisoned_content,
            output=f"BANNED — {reason_code}",
            category="heresy",
            reason_code=reason_code,
            source="injection_generation",
            metadata={"injection_position": position},
        )


def generate_missing_banner_examples(count: int = 100) -> Iterator[TrainingExample]:
    """Generate examples with missing FACTS_ONLY banner."""
    for i in range(count):
        template = random.choice(CONSTITUTIONAL_TEMPLATES)
        values = generate_constitutional_values()

        try:
            content = template.format(**values)
        except KeyError:
            values = generate_constitutional_values()
            content = template.format(**{k: values.get(k, "") for k in values})

        # Remove banner
        content = content.replace(MANDATORY_FACTS_BANNER, "")
        content = content.replace("OINK OINK MOTHERFUCKER! 🐗🔥\n", "")

        yield TrainingExample(
            id=f"no_banner_{i:04d}",
            input=content.strip(),
            output="BANNED — BANNER_MISSING",
            category="heresy",
            reason_code="BANNER_MISSING",
            source="banner_removal",
        )


# =============================================================================
# DATASET GENERATION
# =============================================================================


def generate_full_dataset(
    constitutional_count: int = 500,
    heresy_count: int = 400,
    banner_missing_count: int = 100,
) -> TrainingDataset:
    """
    Generate complete training dataset.

    Args:
        constitutional_count: Number of positive examples
        heresy_count: Number of negative examples (injected)
        banner_missing_count: Number of missing banner examples

    Returns:
        TrainingDataset with all examples
    """
    examples = []

    # Generate positive examples
    print(f"Generating {constitutional_count} constitutional examples...")
    examples.extend(generate_constitutional_examples(constitutional_count))

    # Generate negative examples (injected)
    print(f"Generating {heresy_count} heresy examples...")
    examples.extend(generate_heresy_examples(heresy_count))

    # Generate missing banner examples
    print(f"Generating {banner_missing_count} missing banner examples...")
    examples.extend(generate_missing_banner_examples(banner_missing_count))

    # Shuffle
    random.shuffle(examples)

    # Create dataset
    dataset = TrainingDataset(
        version="1.0.0",
        created_at=datetime.now(timezone.utc).isoformat(),
        invariant_freeze_hash="S41_PHASE_2A",  # Reference to frozen invariants
        examples=examples,
        metadata={
            "constitutional_count": constitutional_count,
            "heresy_count": heresy_count,
            "banner_missing_count": banner_missing_count,
            "total_count": len(examples),
            "reason_code_distribution": {
                rc: sum(1 for e in examples if e.reason_code == rc)
                for rc in list(HERESY_INJECTIONS.keys()) + ["BANNER_MISSING"]
            },
        },
    )

    return dataset


def split_dataset(
    dataset: TrainingDataset,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
) -> tuple[list[TrainingExample], list[TrainingExample], list[TrainingExample]]:
    """Split dataset into train/val/test sets."""
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001

    examples = dataset.examples.copy()
    random.shuffle(examples)

    n = len(examples)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    return (
        examples[:train_end],
        examples[train_end:val_end],
        examples[val_end:],
    )


# =============================================================================
# JSONL FORMAT (FOR TRAINING)
# =============================================================================


def to_jsonl(examples: list[TrainingExample], path: Path) -> None:
    """Write examples to JSONL format for training."""
    with path.open("w") as f:
        for ex in examples:
            # Training format
            training_record = {
                "prompt": f"""Classify this narrator output.
Respond ONLY with: VALID_FACTS or BANNED — [REASON_CODE]

Output to classify:
{ex.input}

Classification:""",
                "completion": ex.output,
                "id": ex.id,
            }
            f.write(json.dumps(training_record) + "\n")


# =============================================================================
# CLI
# =============================================================================


def main():
    """Generate training dataset."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate SLM training data")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("slm/training"),
        help="Output directory",
    )
    parser.add_argument(
        "--constitutional",
        type=int,
        default=500,
        help="Number of constitutional examples",
    )
    parser.add_argument(
        "--heresy",
        type=int,
        default=400,
        help="Number of heresy examples",
    )
    parser.add_argument(
        "--no-banner",
        type=int,
        default=100,
        help="Number of missing banner examples",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )

    args = parser.parse_args()

    # Set seed for reproducibility
    random.seed(args.seed)

    # Generate dataset
    dataset = generate_full_dataset(
        constitutional_count=args.constitutional,
        heresy_count=args.heresy,
        banner_missing_count=args.no_banner,
    )

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Save full dataset
    dataset_path = args.output_dir / "slm_training_data.json"
    dataset.to_json(dataset_path)
    print(f"Saved full dataset to {dataset_path}")

    # Split dataset
    train, val, test = split_dataset(dataset)
    print(f"Split: {len(train)} train, {len(val)} val, {len(test)} test")

    # Save JSONL files for training
    to_jsonl(train, args.output_dir / "train.jsonl")
    to_jsonl(val, args.output_dir / "val.jsonl")
    to_jsonl(test, args.output_dir / "test.jsonl")

    print(f"\nDataset generation complete:")
    print(f"  Total examples: {len(dataset.examples)}")
    print(f"  Constitutional: {args.constitutional}")
    print(f"  Heresy: {args.heresy}")
    print(f"  Missing banner: {args.no_banner}")
    print(f"\nReason code distribution:")
    for rc, count in dataset.metadata["reason_code_distribution"].items():
        print(f"  {rc}: {count}")


if __name__ == "__main__":
    main()
