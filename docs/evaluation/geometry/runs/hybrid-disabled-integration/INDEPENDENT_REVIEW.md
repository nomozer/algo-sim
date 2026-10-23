# Independent code/evidence review

Reviewer: a separate agent with no implementation role in this run, started fresh (not a fork of the implementer's
context), told to be read-only and to verify against Git and code instead of reports. It is a **code/evidence
reviewer, not an independent holdout evaluator**: every corpus it re-ran is the implementer's own locked
development set. No live provider calls; reviewer outputs went to the session scratchpad; it wrote nothing to the
worktree.

## Round 1 — target `b99f64203be005739cd390e237434d9ba5829d9a`

**Verdict: PASS, 0 BLOCKER.** Ten claims checked (coherent integration, contract isolation, backward compatibility,
source authority, exact mathematics, planner composition, Scene3D certificate semantics, refusal taxonomy, evidence
provenance and identity, docs sync): 9 CONFIRMED, 1 PARTIALLY CONFIRMED (claim 7, see IMPORTANT 4 / MINOR 5).
The reviewer independently re-ran `verify_integration_invariants.py`, `check_adapter4_consumer.py` and
`replay_planner_diagnostics.py` (byte-identical outputs except `head`), `freeze_evaluation_candidate.py --verify`
(MATCH 116 / `413ee525…`), a merge line-preservation check (0 lines lost) and 71 targeted docs/candidate tests.
It statically traced every lazy importer of the changed modules: only `pipeline.py:89` (preview + env),
`runtime_identity.py:293` (preview enabled) and `main.py:1030` (preview route after OFF/token/loopback/Origin gates);
`/api/analyze` never requests preview.

| Finding | Severity | Disposition |
|---|---|---|
| 1. Wave not closed at HEAD (no report/handoff/run.json, no EVIDENCE_INDEX entry, seam-replay command unrecorded) | IMPORTANT | Closed in the final docs commit: this directory's reports, `run.json`, EVIDENCE_INDEX and CURRENT_STATE entries; seam-replay command in the integration report §3 |
| 2. 4A EVIDENCE_INDEX entry ("product unchanged from local main", "unmerged Session 3 branch") and S1/S2/4A CODE_INDEX headers ("local", "no product integration") false on this branch | IMPORTANT | Old entries left unchanged (immutable record); new correction entry `HYBRID_DISABLED_INTEGRATION` in EVIDENCE_INDEX; 4B note in CODE_INDEX |
| 3. CODE_INDEX lacked `adapter4_route.py`, `bridge_v2`, `typed-fact-next/2` | IMPORTANT | Fixed in `2bbad1f2` |
| 4. Leak regex missed real id families (`khoi_*`, `kq_*`, `v_*`, `g_*`, `A_prime`) and skipped `display_label`/`role` | IMPORTANT | Fixed in `2bbad1f2`; new receipt `results/adapter4-consumer-after-review/` still 0 leaks (reviewer's own broader scan agreed); first receipt kept unchanged |
| 5. Closure certificates are 21/22 (DEV10 plane-only has none) | MINOR | Stated in all reports; CODE_INDEX wording fixed |
| 6. 7 construct-only served cases have no numeric oracle (reviewer first said 6, corrected to 7 in round 2); `square_of` ignores unit (inherited) | MINOR | Counts recorded by the script (15 numeric / 7 construct-only) |
| 7. `ALLOW_LIVE_AI` invariant was circular; receipt head was `14cdc25a` | MINOR | Fixed in `2bbad1f2`; new receipt at head `2bbad1f2` reads the inherited environment |
| 8. Gateway planner prose lacked the bounded-composition caveat | MINOR | Fixed in `2bbad1f2` (ARCHITECTURE_MAP) |

## Round 2 — target `2bbad1f2715c367736b4a5d783551b94b45fbb79`

**Verdict: PASS.** Read-only, git and file reads only (a Full T3 was running). `git diff --stat b99f6420 2bbad1f2
-- backend frontend` empty; 6 files, all under `docs/`; no `Co-Authored-By`. IMPORTANT 3/4 and MINOR 7/8 resolved;
new fixtures blob `47ba0c90…` byte-identical to the first; first receipt blob `9a29f6dc…` unchanged. One new MINOR
(CODE_INDEX `/4` row implied a closure certificate always) — wording fixed in the final docs commit.

## Scope of what review does not cover

The final docs commit after `2bbad1f2` (reports, indexes, receipts copy, CODE_INDEX wording) was not reviewed by the
reviewer; it changes no product path. Browser rendering, provider extraction and independent holdout remain
unreviewed because they were not executed.
