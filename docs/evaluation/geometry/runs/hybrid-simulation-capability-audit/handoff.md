# Hybrid simulation capability audit: handoff

Status: `HYBRID_SIMULATION_AUDIT_AWAITING_DECISION`.
Next action: `HYBRID_GATE_FIX_AND_SECTION_SLICE_DECISION` (the user's).
LIVE GEMINI CALLS = 0. PRODUCTION DEFAULT = `LLM_ONLY`. No product code changed.

## Deliverables (all in [`report.md`](report.md))

| Deliverable | Section |
|---|---|
| SIMULATION_COVERAGE_MATRIX | §3 (+ inventory of the 27 functions, §2) |
| HYBRID_DATA_FLOW_AUDIT | §1 |
| GOAL_DIRECTED_PLANNING_GAP_REPORT | §5 |
| SEMANTIC_AND_GEOMETRY_VERIFICATION_GAP_REPORT | §4, §6 |
| METAMORPHIC_TEST_PLAN + executed probes | §7; `backend/tests/geometry/test_hybrid_simulation_capability_probes.py` |
| PRIORITIZED_NEXT_SLICES | §8 (S0 prerequisite + 3 slices; slice 1 recommended) |
| ROADMAP / CANONICAL_NEXT_ACTION | updated |

## Decisions needed from the user

1. **S0** — fix `ISSUE-ARCH-GATE-CLAUSE-ROLE-INSIDE-QUOTE`, optionally together with `ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK`.
   - It changes the shared source gate of both routes A and B.
   - No provider-surface change. The candidate must be refrozen.
2. **Slice 1 (section + intersection line)** — new Registry entries and a new Typed Facts kind.
   - These change the A and B provider surfaces.
   - IR, kernel and Scene3D stay unchanged.

## Git

- Branch `research/hybrid-simulation-capability-audit` holds one commit: probes + docs.
- `main` = `origin/main` = `a6e27a78`, untouched.
- No push.
