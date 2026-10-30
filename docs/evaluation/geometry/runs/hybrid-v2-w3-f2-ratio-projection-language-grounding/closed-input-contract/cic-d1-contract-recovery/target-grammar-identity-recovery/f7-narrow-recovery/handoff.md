# Handoff: F7 narrow recovery and final safety preparation, NOT_READY (PUBLICATION_BLOCKED)

Owner GO `W3-F2 F7 NARROW RECOVERY & FINAL SAFETY PREPARATION`, 2026-10-30. This is a continuation of
`HYBRID_V2_W3_F2_TARGET_GRAMMAR_AND_CANONICAL_IDENTITY_RECOVERY`, not a new wave.

1. **Research HEAD.** Branch `research/hybrid-v2-w3-f2-ratio-projection-language-grounding`. The commit that contains
   this handoff follows `48721da3`. Chain from checkpoint `1b1a9ed2`:
   - `ae81b65e`: RED preregistration
   - `415da751`: harness amendment
   - `dd17fbfb`: F7 fix
   - `48721da3`: Gate D and publication assessment
   - then this commit: review, RV fixes and handoff.

   `main` / `origin/main` = `996f114b`.
2. **F7 root cause.** In `_Adapter3Compiler._compile_derived_solids_and_goals`, every measurement goal got a call id,
   but `radius` and `lateral_area` had no dispatch branch on prisms and pyramids, so no `ask_*` call was emitted.
   `_compute_certified_math_goals` then raised `KeyError` on `hoi[cid]`, and the boundary recorded it as
   `ADAPTER_INTERNAL_ERROR`.
   - Affected inputs: prism and pyramid, `{solid}` and `{section_id}`, single and multi-goal payloads.
   - The bug predates this branch: it is present on main.
   - Details: `root-cause.md`.
3. **Changed modules.**
   - Product: `backend/app/ai/adapter3_simulation.py` only, +3 lines: a terminal `else` that raises
     `BRIDGE_UNSUPPORTED_MEASUREMENT`. This module is one of the originally authorized three, so the scope did not widen.
   - Tests: the new `backend/tests/geometry/test_measurement_dispatch_and_identity_order.py`, and the 8-cell re-pin in
     `test_target_grammar_identity_recovery.py`.
   - Docs: contract §5.
4. **F7 RED/GREEN.**
   - Preregistered 47 cases.
   - Amended RED on unmodified product: 27 failures, all preregistered F7 cells (`red-amended.json`).
   - GREEN: 241/241, now 242 after RV-1.
   - No `ADAPTER_INTERNAL_ERROR` from F7 and no uncontrolled `KeyError`. Supported controls keep their exact answers,
     and nothing is wrong-served.
   - Mutation guards: dropping the dispatch branch is killed, and a planted `KeyError` is still reported as an internal
     error.
5. **R1/R2: `TEST_GAP_CLOSED`, no product change.**
   - Every behavioural and mutant oracle passed on unmodified product.
   - RV-1 extended the R2 oracle to the parent-last solid order, and the first-root mutant is killed.
6. **R3 limitation.** For a constructed-label collision, a3 returns `INVALID_MATH_GOAL` instead of
   `AMBIGUOUS_REFERENCE`. Deferred MINOR (D3), not closed. Both reviewers agree it is not MAJOR.

   Other limitations, all fail-closed:
   - **L-AREA / RV-2:** registered alternatives without an a3 branch are refused on a3 as `INVALID_MATH_GOAL`. They are
     polyhedral `area {solid}`, `distance {point,line}`, `{line,plane}`, `{plane1,plane2}` and `angle {plane1,plane2}`.
   - **RV-8:** a mixed cylinder+prism payload is refused as `MISSING_CURVED_DIMENSION`.
   - **Source grammar:** 4 diagnostics remain `PENDING_SOURCE_GRAMMAR_SUPPORT`.
7. **Gates.**

   | gate | status | result |
   |---|---|---|
   | A | PASS | combined suite 3199 passed / 6 skipped; 203 locked probes: 0 served negatives, 0 internal, 0 transitions; 50 mutation oracles pass |
   | B | PASS | one product file; cache 130, `LLM_ONLY`, live 0, Hybrid opt-in |
   | C | PASS | 96/96, 0 wrong-served; re-run on clean `dd17fbfb` by the reviewer |
   | D | `PRE_FREEZE_COMPATIBILITY_PASS` | clean detached `dd17fbfb`: 15768 passed, 11 failed, node-identical to `PENDING_NEW_FREEZE` (cause: candidate drift); locked V2 232/232; fixtures 41/41; `overall_pass` false |

8. **Independent review.** READY for this gate: 0 BLOCKER, 0 MAJOR, 4 MINOR, 4 NOTE (`independent-review.md`).
   - RV-1, RV-3 and RV-4 are closed.
   - RV-2 is disclosed.
   - RV-5 to RV-8 are noted.
9. **Publication risk.** `publication-assessment.md`. Two pytest logs from `1490e3cd`; I checked each blob and hash.
   - Both contain the `PY_TRACEBACK` rule ×5: a stdlib cp1252 reader-thread warning, with no product stack.
   - 0 credential, token or email matches.
   - Local paths, 4 of which contain the Windows profile name. That name is already present in 138 files on
     `origin/main`.
10. **Exception recommendation.** I recommend APPROVE for both entries, on condition that the Owner accepts publishing
    the local-path disclosure. If the Owner does not, DECLINE both and use a separate clean publication candidate under
    its own GO. Nothing was approved, `APPROVED_BY_USER` was not written, the registry is unchanged and the scanner is
    untouched.
11. **Wave 3 replay:** NOT RUN; publication is blocked.
12. **T0/T1/T2:** NOT RUN.
13. **Candidate / freeze / Full T3:** NOT RUN. No new candidate was written; `freeze-cause-current.json` confirms
    `candidate_written: false`. Old T3 receipts are not reused.
14. **Historical evidence integrity.**
    - No historical file outside `f7-narrow-recovery/` was modified, deleted or renamed. The one in-place amendment was
      this run's own `cases.json` and `registration.json`, disclosed with its original in `ae81b65e`.
    - No history was rewritten.
    - Raw logs were kept local and not committed.
15. **Verdict: `NOT_READY — PUBLICATION_BLOCKED`.** Exact blockers:
    - (a) The Owner decision on the two publication exceptions, or an authorized remediation that passes the scanner.
    - (b) After that, the conditional chain must still run and pass: Wave 3 replay → T0/T1/T2 → new candidate freeze
      (separate commit) → candidate identity verify → Full T3 on a clean detached tree → final independent review.

    There is no technical BLOCKER or MAJOR. No merge, push or cleanup was done; 0 provider calls.
