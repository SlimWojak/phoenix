# ADVISOR ORIENTATION — Phoenix Bootstrap Protocol

**PURPOSE**: Fast orientation for fresh Claude/Advisor sessions.
**LOAD ORDER**: Sequential — each builds on previous context.

---

## PRIORITY 0: ESSENTIAL (Always Load)

### 1. SKILL.md
```
path: phoenix/SKILL.md
contains:
  - Communication standard (DENSE_M2M)
  - Core invariants
  - Role map
  - Brief templates
  - Report templates
```

### 2. CONSTITUTION Manifest
```
path: phoenix/CONSTITUTION/CONSTITUTION_MANIFEST.yaml
contains:
  - Architecture overview
  - Module registry
  - Invariant index
check: phoenix/CONSTITUTION/invariants/*.yaml for proven state
```

### 3. Active Data Contract
```
path: phoenix/contracts/ICT_DATA_CONTRACT.md
contains:
  - 472 column schema
  - Schema hash: b848ffe506fd3fff
  - Truth Teller requirements
```

---

## PRIORITY 1: CONTEXT (Load for Sprint Work)

### 4. Current Sprint Doc
```
path: phoenix/docs/SPRINT_*.md (current)
latest: SPRINT_26.md → S28.D is current
contains:
  - Track status
  - Exit gates
  - Deliverables
```

### 5. Governance Contract
```
path: phoenix/contracts/GOVERNANCE_INTERFACE_CONTRACT.md
contains:
  - GovernanceInterface ABC
  - Tier system (T0/T1/T2)
  - Halt mechanism
  - State hash
```

---

## PRIORITY 2: REFERENCE (Load As Needed)

### 6. Methodology Architecture
```
path: phoenix/cso/knowledge/index.yaml
contains:
  - 5-drawer structure
  - 59 signals
  - Olya methodology index
```

### 7. Vision & Manifesto
```
paths:
  - phoenix/docs/VISION_v4.md
  - phoenix/docs/PHOENIX_MANIFESTO.md
contains:
  - Strategic direction
  - Founding principles
```

---

## QUICK STATE CHECK

```bash
# Proven invariants
ls phoenix/CONSTITUTION/invariants/

# Current sprint status
cat phoenix/docs/SPRINT_26.md | head -50

# Test health
cd ~/nex && source .venv/bin/activate
python -m pytest ~/phoenix/tests/ -v --tb=short | tail -20
```

---

## PROVEN STATE (S28.D)

| Invariant | Proven Value | Test |
|-----------|--------------|------|
| INV-HALT-1 | 0.003ms | test_halt_latency.py |
| INV-HALT-2 | 22.59ms | test_halt_propagation.py |
| INV-CONTRACT-1 | hash match | test_state_hash_canonical.py |
| INV-DATA-CANON | XOR == 0 | test_mirror.py |

---

## ANTI-PATTERNS

```yaml
AVOID:
  - Reading VISION_v4 before SKILL.md (wrong priority)
  - Skipping CONSTITUTION (leads to invariant violations)
  - Ignoring current sprint (context drift)
  - Writing code before checking tests exist

PREFER:
  - Sequential load order above
  - Check proven state before modifying
  - Run tests after changes
  - Emit beads for significant decisions
```

---

## COMMUNICATION FORMAT

All advisor output should follow DENSE_M2M:
- Zero prose preamble
- YAML/structured preferred
- Binary verdicts (PASS/FAIL)
- Explicit refs (file:line)
- No restating context back

---

*OINK OINK.* 🐗🔥
