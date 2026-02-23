# BRIEF FOR CRAIG/CTO
## Amendment Package - BLUR Fixes Completion
## Date: January 30, 2026

---

## 🎯 WHAT THIS IS

**Problem Found:** The BLUR-001/002/003 fixes were incomplete. You correctly removed duplicated logic from `conditions.yaml` and added references, but `context.yaml` never received the content it's supposed to own.

**Current State:** `conditions.yaml` references `context.Q1_location`, `context.Q2_objective`, etc. but these don't exist → system is broken.

**This Package:** Adds the missing content to `context.yaml` so references work.

---

## 📦 WHAT TO DO

**Step 1:** Apply `amendments_context_yaml.md` to `context.yaml`
- Adds 3Q framework, P/D calculation, PDA detection
- 5 amendments total
- Takes 30-45 minutes

**Step 2:** Apply `amendments_index_yaml.md` to `index.yaml`  
- Updates signal counts (21→24, 41→44)
- 2 lines changed
- Takes 2 minutes

**Step 3:** Return updated files to Olya

---

## 🤖 FOR THE MACHINE

Each amendment file has:
- 🤖 **MACHINE INSTRUCTION** sections (exact locations, search terms)
- **Clear INSERT or REPLACE actions**
- **Verification checklists** after each amendment
- **Post-application checklist** at the end

**Just follow the instructions in order.** They're designed to be copy-paste friendly.

---

## ✅ SUCCESS CRITERIA

After amendments applied:
- `context.yaml` parses without errors ✓
- Signal count: 24 (was 21) ✓
- All references in `conditions.yaml` now resolve ✓
- `index.yaml` counts updated ✓

---

## 📁 FILES IN PACKAGE

1. **AMENDMENT_PACKAGE_SUMMARY.md** ← Read this for full context
2. **amendments_context_yaml.md** ← Apply this FIRST
3. **amendments_index_yaml.md** ← Apply this SECOND
4. **BRIEF_FOR_CRAIG.md** ← This file (quick overview)

---

## ⏱️ TIME ESTIMATE

**Total: 35-50 minutes**

---

## ❓ QUESTIONS?

Check the detailed instructions in each amendment file. They have step-by-step guidance with verification at each step.

---

**Ready to apply!** 🚀
