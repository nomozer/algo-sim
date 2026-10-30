# Final handoff: W3-F2 F7 recovery and final verification — READY_FOR_OWNER_REVIEW

Owner GOs: `HYBRID_V2_W3_F2_PUBLICATION_EXCEPTION_AND_FINAL_VERIFICATION`, then "UNBLOCK TECHNICAL WORK", then
"OWNER APPROVAL COMPLETED" (all 2026-10-30). This is the final layer and supersedes the status lines in `handoff.md`
and `technical-checkpoint.md`, which are kept unchanged as history. 0 provider calls. No merge, push or cleanup.

1. **Final research HEAD.** The commit that adds this file, following `019b6289`. Branch
   `research/hybrid-v2-w3-f2-ratio-projection-language-grounding`; `main` / `origin/main` = `996f114b`.
2. **Publication exceptions and scope evidence.**
   - Exactly two registry entries are approved: blobs `395896a0…` (`gate-d-full-backend-pytest.log`) and `21a012bb…`
     (`gate-d-pre-patch-5e44d5da-identity-12.log`). Both were first committed in `1490e3cd`, with rule `PY_TRACEBACK`
     only.
   - The 7 Owner conditions were verified in `publication-exception-verification.json`.
   - The Owner wrote `APPROVED_BY_USER` with a PowerShell command keyed on the two blob SHAs (commit `a12cbb0d`,
     `publication-approval-receipt.json`). The agent never wrote the value (`AGENTS.md:49`).
   - Semantic diff: 2 values; text diff: 2+/2−.
3. **Publication scanner.** `--range 996f114b..HEAD`: PASS, 0 violations. Before approval the same range had exactly 10
   violations, all on these two blobs, so nothing else is masked. The final reviewer re-ran this with the
   pre-approval registry.

   Disclosed and pre-existing: `--head` is BLOCKED identically on `main` and on this branch. It reports 105
   violations, of which 104 are pending historical entries. The remaining one is a `GOOGLE_API_KEY` pattern in
   `backend/tests/geometry/test_docs_information_architecture.py`, the same blob `0f726dfb` on `main`. It is outside
   this GO.
4. **Wave 3 replay** (`POST_FEEDBACK_DEVELOPMENT_REGRESSION`):
   - 50/72 positives served-correct and 22 false refusals.
   - 72/72 negatives refused, 62/72 with the correct reason.
   - 0 wrong-served and 0 transitions (`wave3-post-feedback-regression.json`).
   - Reproduced by the final reviewer on the candidate.
5. **T0/T1/T2** at `a0fd2377`, product unchanged since `dd17fbfb` (`tiers.json`):

   | tier | result |
   |---|---|
   | T0 | `IMPACT_GATE_FAIL` before the freeze, only on the 11 freeze-identity nodes; the rest pass. Those nodes pass after the freeze. |
   | T1 | geometry 872, semantic 24 |
   | T2 | vitest 1417, `tsc -b`, build |

6. **Candidate.**
   - Freeze commit: `4e7fe91d` (a separate commit), frozen from the clean tree at `a12cbb0d`.
   - Product commit: `dd17fbfb`.
   - Measured system: 118 files (current manifest), `c4fb8613800585ddd68a13f410e5c84755e64a8562c1604ed4b43b6e03c2fb8c`.
   - `--verify` MATCH.
   - New divergence layer: `runs/hybrid-v2-w3-f2-f7-narrow-recovery/candidate_divergence.json`.
   - Cache stays 130 (NO_BUMP).
7. **The 11 freeze-identity tests.** 11/11 passed after the freeze, and they pass again inside Full T3.
8. **Full T3** (`full-t3.json`): fresh, clean, detached worktree at `4e7fe91d`; `FULL_PRODUCT_GATE_PASS`, exit 0.

   | step | result |
   |---|---|
   | pytest | 15780 passed, 0 failed |
   | vitest | 1417 |
   | build | PASS |
   | demos | 5/5 |
   | crash surface | 6/6 |

   After T3: `--verify` MATCH, the candidate hash is unchanged, and the range publication scan PASSes. The log hash
   matches the raw local log.
9. **Independent final review: READY.** 0 BLOCKER, 0 MAJOR, 2 MINOR, 6 NOTE (`final-review.md`).
   - FR-1 (stale status docs) and FR-2 (`CORRECTED_BY` back-pointer) are fixed in this commit, docs only, outside
     `MEASURED_SYSTEM_PATHS`.
   - On the candidate, the reviewer independently re-ran: the publication scan, candidate identity, the 11 identity
     tests, Wave 3, Gate C 96/96, the 203 probes, 703 registered payloads × 3 routes (0 internal), and the targeted
     suites (2691 + 1008 passed).
10. **Historical evidence integrity.**
    - No historical receipt was modified, deleted or renamed.
    - In-place edits are limited to:
      - this run's own disclosed amendment (`415da751`);
      - the registry (2 appended entries plus 2 Owner-written values);
      - the living `EVALUATION_CANDIDATE.json`, the contract doc §5 and the status docs.
    - No history was rewritten.
11. **Remaining limitations.** All are fail-closed and unrepaired by Owner decision:
    - R3: `INVALID_MATH_GOAL` instead of `AMBIGUOUS_REFERENCE` for a constructed-label collision.
    - RV-2 / L-AREA: registered alternatives with no a3 branch are refused `INVALID_MATH_GOAL` on a3.
    - RV-8: a mixed curved+prism payload is refused `MISSING_CURVED_DIMENSION`.
    - 4 `PENDING_SOURCE_GRAMMAR_SUPPORT` diagnostics.
    - RV-5: an ordering effect, the same as on pl/a4.
    - Live provider quality is not measured.
12. **Verdict: `READY_FOR_OWNER_REVIEW`.** Integration into `main` (merge, push and cleanup) needs a separate Owner
    decision.
