# Handoff — F1/F2 target grammar and canonical identity recovery: NOT_READY (blocked on Owner decisions)

Branch `research/hybrid-v2-w3-f2-ratio-projection-language-grounding`. The task began at start head `df475f06`; `main` is `996f114b`. Nothing has been merged, pushed or cleaned up, and there were 0 provider calls. Settings are unchanged: `LLM_ONLY`, `ALLOW_LIVE_AI=0`, Hybrid opt-in, `CACHE_VERSION` 130.

| step | commit / receipt | result |
|---|---|---|
| RED preregistration | `c9cf9e92` | 337 fail / 1734 pass before product edits |
| F1/F2 fix | `6a09c06a` (`typed_fact_next.py` only) | targeted GREEN |
| CRLF harness fix | `5c4b743f` (`checkout-hash-amendment.md`) | frozen hash unchanged |
| Gates A–C | `gate-a/b/c.json` | A acceptance PASS (known-input safety NOT_PASS: F7); B PASS; C 96/96 |
| Gate D | `e18bccc4`, `gate-d.json` | backend compatibility on a clean tree: 11 failures, all `PENDING_NEW_FREEZE` and baseline-matched; V2 232/232; fixtures 41/41 |
| Independent review | `pre-freeze-review.md` | READY for this gate: 0 BLOCKER, 0 MAJOR, 3 MINOR (all fail closed) |

**What blocks freeze, Full T3 and integration (Owner decision required):**
1. **Publication `BLOCKED_PENDING_OWNER_DECISION`.** Two historical logs in commit `1490e3cd` contain stdlib tracebacks and private local paths; see `publication-risk.md`. No exception is recorded and none is approved.
2. **F7 unresolved.** Prism `radius`/`lateral_area` returns `ADAPTER_INTERNAL_ERROR` (`KeyError 'ask2'`), the same on `main`. It is outside the authorized product files and scope.

Open MINOR items (fail closed, no wrong answer served). These are candidates for a test-only follow-up and are not fixed here:
- R1: no test pins the order "namespace/ownership check, then repeated-identity check".
- R2: no test covers the derived-parent mapping when there is a second root solid.
- R3: for an ambiguous label that collides with a constructed point, the code returns `INVALID_MATH_GOAL` instead of `AMBIGUOUS_REFERENCE` (contract §5 wording).

Next step, only after both Owner decisions: Wave 3 replay → T0/T1/T2 → re-freeze the candidate in a clean worktree as a separate commit → Full T3 → final review.
