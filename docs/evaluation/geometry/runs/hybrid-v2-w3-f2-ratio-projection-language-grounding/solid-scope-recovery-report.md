# W3-F2 Adapter /3 safety recovery — Claude takeover report

Owner GO `HYBRID_V2_W3_F2_ADAPTER3_SEMANTIC_FALLBACK_SAFETY_HARDENING` (Claude takeover), 2026-10-29. 0 provider
calls throughout. Classification of every new replay: `POST_FEEDBACK_DEVELOPMENT_REGRESSION` (not a blind holdout).
Starting state and the reconstructed Codex stop: `codex-to-claude-takeover.md`.

## 1. Codex state recovered

- Codex HEAD `6516d5d4` (all work committed; empty staged/unstaged diff). Only untracked file: an empty
  `verification/full-t3/full-t3.log`, committed in `bcf0b7fd` as the record of the aborted run.
- Original STOP: not a test failure. Codex's separate-context final reviewer reproduced a MAJOR during T3 (height
  premise `solid_id=pyr1` with `args.solid=pyr2` served by Adapter /3). The abort commands failed (ambiguous process
  match, then auto-review rejection on usage limit). T3 produced no output and no receipt; nothing is claimed from it.
- Evidence-integrity correction: Codex's `verification/pre-freeze-tiers.json` records `T0 impact: PASS`, but
  `verification/adapter3-impact.log` is a `--dry` listing (tests selected, none run). The real T0 here failed 16
  tests (`verification/solid-scope-t0-impact-fail.log`), two of them genuine pre-existing defects (§3). The Codex
  file is left unchanged; this report corrects it.

## 2. Safety failure and fix (Gate A)

Root cause: Adapter /3 read every solid-valued operand as `inner or scope` (`height.solid`, `altitude.solid`, volume
`target.solid`) and never checked a goal's declared `solid_id`, nor a section-area goal's solid against the
section. On legacy inputs the Bridge raises a capability refusal before its scope validator runs, so Adapter /3's
compile was the only guard. The Bridge volume goal had the same blind spot, which Adapter /4 inherits.

Fix (`393864d1`): one helper per layer, same rule — unknown declared scope → `UNKNOWN_SOLID_ID`, operand
contradicting the declared scope (by id or notation) → `SOURCE_OBJECT_MISMATCH`.
`typed_fact_next_bridge.py::_pham_vi_khoi` (extracted from the existing premise validator, reused by volume goals);
`adapter3_simulation.py::_Adapter3Compiler._scoped_solid_name` (altitude, height, volume goal, section-area goal).
No Registry / Planner / kernel / Adapter /4 code / default routing change.

| boundary (takeover §3) | before | after (Adapter /3; /4 where applicable) |
|---|---|---|
| H1 legacy height pyr1 vs pyr2 | SERVED | REFUSED `SOURCE_OBJECT_MISMATCH` |
| H2a volume goal s2 vs target s1 | SERVED (/3, /4) | REFUSED `SOURCE_OBJECT_MISMATCH` (/3 = /4) |
| H2b volume goal `foreign` | SERVED (/3, /4) | REFUSED `UNKNOWN_SOLID_ID` (/3 = /4) |
| H2c/H2d legacy volume goal pyr2 / foreign | SERVED | REFUSED mismatch / unknown |
| H3 s1 vs target `T.ABCD` | SERVED (/3) | REFUSED `SOURCE_OBJECT_MISMATCH` (/3 = /4) |
| A3-DEV-02 and supplementary controls | SERVED exact | SERVED exact (unchanged) |

RED `df453779` (16 failing negatives, all positives passing; log `verification/claude-solid-scope-red-tests.log`)
→ GREEN 64/64 in `test_adapter3_fallback_safety.py`. Four new guard-removal mutants (Bridge/Adapter3 × conflict /
unknown scope) are killed alongside Codex's four.

## 3. Defects found by the real T0 (pre-existing in `6516d5d4`, also fixed)

- Locked holdout negative **N006** (`test_holdout_failure_repair.py`): Codex's Bridge premise scope validator
  refused an unscoped height naming undeclared `s99` as `UNKNOWN_SOLID_ID`, ahead of the planner's locked
  `UNKNOWN_SOLID` (refused, wrong reason; PASS on main). Fix `c4d7b759`: with no declared scope the Bridge makes no
  scope claim; with a declared scope it still refuses. Expected codes unchanged.
- Three Registry pins still at `/20` after the Owner-approved `/21` bump (`test_holdout_failure_repair`,
  `test_wave3a_adapter3_integration`, `test_wave3a_volume_reasoning`); updated like the two Codex updated.
- The remaining T0 failures were the stale freeze (product changed after `6516d5d4`) and a dirty-tree precondition
  (uncommitted evidence at run time); all 112 tests of those files pass after the freeze on a clean tree.

## 4. Gates (product `c4d7b759`, `solid-scope-final-safety-gates.json`)

- A PASS: boundary matrix above; NEG08/23 + canonical variants, foreign/cross-solid/same-label collision,
  terminal semantic refusal, legacy positives — all in the safety file; 0 WRONG_SERVED on the locked 96.
- B PASS (unaffected): no incidence/engine/Registry change since the independently adjudicated `f7dd5580`;
  witness tests re-run in the compatibility suite.
- C PASS: locked 96 development cases 96/96 match (authored ratio 24/24, projection 26/26, isolated 1/1,
  historical 20/21 served + 1 locked refusal, mandatory negative/tamper 24/24 refused with locked codes).
- D PASS: compatibility suite 717 passed / 0 failed / 6 xfailed (W3-F1, Adapter /3 + /4, Registry /21, Planner
  /18, contract v2, radical, exact certificates, holdout repair, Wave 3A); 41/41 preview fixtures verify;
  cache identity lock MATCH. `CACHE_VERSION` 130 not bumped: cached `LLM_ONLY` path untouched.

## 5. Wave 3 post-feedback replay (144 cases)

`wave3-post-feedback-regression-after-solid-scope-final.json`: positives 50/72 served correct, 22 false refusals,
0 wrong-served; negatives 72/72 refused, 62 correct reason, 10 reason disagreement, 0 wrong-served; 0 machine-ID or
source-identity leaks. 0 transitions from the post-Adapter3 replay. A06 remains the radical-limit refusal.

## 6. Freeze and Full T3

New candidate frozen at `55bdd332` (separate commit; measured system 118 files `609931405d65aed5…`; divergence
declared in `inputs/candidate_divergence.json`, correcting this run's earlier declaration). Full T3 in a clean
detached worktree (`.superpowers/worktrees/w3-f2-solid-scope-t3`): pytest 12783 passed / 0 failed, vitest 1417/1417,
typecheck + build, demo replay, crash surface — `FULL_PRODUCT_GATE_PASS`; post-freeze verify MATCH; source tree clean
before and after (`verification/full-t3-solid-scope/receipt.json`).

## 7. Independent review → verdict NOT_READY

`review-solid-scope.md`: the repair itself is correct and the evidence chain is sound, but the reviewer found three
more MAJOR scope fail-open paths of the same class — (1) Adapter /4 serves distance/angle goals whose `solid_id` is
foreign or contradicted, (2) the Adapter /3 curved route ignores goal and premise `solid_id`, (3) ratio/residual goals
with a foreign `solid_id` are served — all independently re-reproduced and all present on main. Gate A is therefore
FAIL despite the Full T3 PASS; the Full T3 receipt certifies regression safety of `55bdd332`, not readiness.

**Verdict: `NOT_READY`.** No product change after the review.

Recommended next step (needs Owner GO): replace point fixes with one declared-scope validator per layer that walks
every scoped field — all math-goal kinds (including ratio/residual and derived solids), premises, relations,
simulation goals — and run it on the curved route too, before any capability refusal or fallback. Owner decisions
needed: (a) meaning of goal-level `solid_id` on ratio/residual goals (refuse when present vs. forbid in schema);
(b) whether the curved route is in this wave's scope; (c) whether Adapter /4-only relation refusals (finding 4) are
required. Then RED (findings 1–6 as tests) → GREEN → Gates A–D → replay → T0–T2 → refreeze → Full T3 → review.

## 8. Unchanged invariants

`LLM_ONLY` default, `ALLOW_LIVE_AI=0`, Hybrid opt-in only; Wave 3 blind holdout and all earlier receipts byte-
unchanged (only additions in this run dir); no merge, push or cleanup.
