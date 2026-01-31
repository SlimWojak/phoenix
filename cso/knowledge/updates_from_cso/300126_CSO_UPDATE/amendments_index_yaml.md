# AMENDMENTS: index.yaml
## Update Signal Counts After context.yaml Amendments
## Date: January 30, 2026
## Purpose: Reflect new signal counts after BLUR-001/002/003 fixes applied to context.yaml

---

## 🤖 INSTRUCTIONS FOR CTO MACHINE

**File to modify:** `index.yaml`

**Action:** REPLACE specific lines with updated counts

**Total amendments:** 2
- Amendment 1: Update context drawer signal count (21 → 24)
- Amendment 2: Update total signals count (41 → 44)

**Dependency:** Apply AFTER `amendments_context_yaml.md` is complete

**Verification after applying:**
- Context signals: 24
- Total signals: 44
- Version remains: v1.0

**Estimated time:** 2 minutes

---

## AMENDMENT 1: Update Context Drawer Signal Count

**🤖 MACHINE INSTRUCTION:**
- **Action:** REPLACE one line
- **Location:** Line 57 (inside `drawers:` section, under `- drawer: 2`)
- **Search for exact line:** `signals: 21  # +4 (SIG-CTX-018 to SIG-CTX-021)`
- **Replace with:** Line below
- **Verification:** New line should show 24 signals with correct comment

**Current line (line 57):**
```yaml
      signals: 21  # +4 (SIG-CTX-018 to SIG-CTX-021)
```

**Replace with:**
```yaml
      signals: 24  # 21 base + 3 new (3Q framework, P/D calc, PDA detection per BLUR 1-3)
```

**Explanation:**
- Base signals: 21 (original)
- +1 for 3Q framework (SIG-CTX-3Q with Q1/Q2/Q3 + synthesis)
- +1 for P/D calculation (SIG-CTX-PD-STATE)
- +1 for PDA detection (SIG-CTX-PDA-DETECT with FVG/OB/IFVG/BPR)
- **New total: 24**

---

## AMENDMENT 2: Update Total Signals Count

**🤖 MACHINE INSTRUCTION:**
- **Action:** REPLACE one line
- **Location:** Line 116 (inside `totals:` section)
- **Search for exact line:** `signals: 41  # +4 context, -3 conditions (blur dedup)`
- **Replace with:** Line below
- **Verification:** New total should be 44

**Current line (line 116):**
```yaml
  signals: 41  # +4 context, -3 conditions (blur dedup)
```

**Replace with:**
```yaml
  signals: 44  # context: 24, conditions: 12, entry: 5, management: 8, foundation tracking: varies
```

**Calculation:**
- Context: 24 (was 21, +3 from amendments)
- Conditions: 12 (unchanged)
- Entry: 5 (unchanged)
- Management: 8 (unchanged)
- Weekly/Daily: ~5 (part of context count)
- **New total: 44**

---

## SUMMARY OF CHANGES

**What changed:**
1. **Context drawer signal count:** 21 → 24 (+3 from BLUR fixes)
2. **Total signal count:** 41 → 44 (+3 from context amendments)

**Why changed:**
- Applied BLUR-001/002/003 fixes to context.yaml
- Added 3 new signal sections (3Q, P/D, PDA)
- These were previously missing from context but referenced by conditions

**Gap status:**
- All 9 GAPS still resolved ✅
- All 3 BLUR fixes now complete ✅

---

## ✅ POST-APPLICATION VERIFICATION CHECKLIST

**For CTO Machine to verify after applying amendments:**

### Line Updates
- [ ] Line 57 shows: `signals: 24` (not 21)
- [ ] Line 116 shows: `signals: 44` (not 41)

### Count Accuracy
- [ ] Context drawer: 24 signals
- [ ] Conditions drawer: 12 signals (no change)
- [ ] Entry drawer: 5 signals (no change)
- [ ] Management drawer: 8 signals (no change)
- [ ] Total adds up correctly: 24 + 12 + 5 + 8 + other = 44

### Consistency Check
- [ ] index.yaml counts match actual signal counts in each drawer
- [ ] Comments explain the change (+3 from BLUR fixes)
- [ ] Version and date unchanged (still v1.0, 2026-01-30)

### Integration Check
- [ ] This amendment applied AFTER context.yaml amendments
- [ ] All references in index still valid
- [ ] No other sections need updating

**If all checkboxes pass → Amendment application SUCCESSFUL ✅**

---

**Status:** Ready for Craig to implement
**Priority:** MEDIUM (dependent on context.yaml amendments)
**Dependencies:** Must apply AFTER amendments_context_yaml.md
**Estimated implementation time:** 2 minutes
