# AXO HYBRID /17 — Local Model 1 integration readiness, routing integrity & independent validation (`FINAL_MASTER_REPORT`)

**Date:** 2026-11-21 · **Run ID:** `model1-integration-readiness` · **Branch:** `feat/model1-integration-readiness`
(from `/16` HEAD `3a39a1ea4`, shared worktree `.superpowers/worktrees/simulation-intent-slm-recovery`; `main` `bc6ff5e33`
untouched; nothing merged or pushed). Audience: the owner.

> **Verdict: `READINESS_WITH_EXPLICIT_BLOCKERS`.** Candidate 157 is intact and reproduces its `/16` result. The routing
> audit found one metric-driven parser exclusion and one parser defect; both are fixed in **candidate 158** (Full T3
> PASS, 0 regressions on 706 exposed cases, 12 fewer SLM calls on Holdout-6 + SLM-Independent-3). Model 1 is
> architecturally compatible with the geometry core. Integration is blocked by owner decisions (merge scope, candidate,
> measurement compliance, publication exceptions) and by deployment gaps (Windows-only runtime, unhosted GGUF, no
> request deadline, single-process capacity ≈ 14 SLM requests/min on the dev host).

## 1. Answers to the seven questions

1. **Is candidate 157 stable and preserved?** Yes. Freeze, cache lock, model and runtime checksums, invariant suites
   (558 tests) and the 18 frozen `/16` artifacts all match; re-running Holdout-6 on 157 reproduces 64/72, 23 SLM,
   26/26 negatives safe. One recorded digest in `/16` `run.json` is a 63-character typo (file unchanged).
   → `CANDIDATE157_INTEGRITY_AUDIT.json`
2. **Is routing designed for the product or for the benchmark?** The router is deterministic-first by design, but `/16`
   kept the pairwise-perpendicular synonym out of the parser *"to preserve the SLM-required denominator"* while the SLM
   path applied the same rewrite deterministically. Separately, a parser defect (an assignment `Độ dài KL = 7` read as a
   goal) made 11 of the 31 Holdout-6 "SLM-required" problems SLM-dependent. SLM-first loses 16 cases and gains none.
   → `PARSER_SLM_ROUTING_AUDIT.json`
3. **What are the remaining failures?** All 8 unserved Holdout-6 positives are correct fail-closed refusals on
   capability gaps (7 first lost in the parser, 1 needs a derived-relation rule). No safety defect, no oracle or scope
   error. Q01b is in scope and its oracle is valid; its `OUT_OF_SCOPE` is Route D's capability escape, not the subject
   gate. Minor UX defect: capability gaps are worded as a request to "clarify the relation".
   → `RESIDUAL_FAILURE_TRIAGE.json`
4. **How strong is the text evidence?** Strong for regression and mathematical safety (0 wrong scenes across every
   exposed set), weak for generalization: every set was authored by the team that tuned Model 1, and this run showed the
   set design shaped the denominators. `EXTERNAL_INDEPENDENCE = NOT_MEASURED`.
   → `INDEPENDENT_VALIDATION_READINESS.md`
5. **How many requests can the backend serve?** On the dev laptop: ≈ 10–13 deterministic requests/s; SLM inference is
   serialized at ≈ 0.24 served requests/s with at most 4 waiting, then `503 LOCAL_SLM_BUSY` (fail-closed, no wrong
   scene). Crash, restart, unprovisioned runtime and client disconnect all recover correctly. No target-hardware or
   multi-user capacity claim is possible. → `RUNTIME_CAPACITY_REPORT.json`
6. **Is Model 1 compatible without redesigning the core?** Yes. TypedFactNext, Planner, Exact Kernel arithmetic and
   Scene3D are model-agnostic; every route passes the Source Gate. → `MODEL1_INTEGRATION_PLAN.md` §2
7. **If the owner integrates text-only Model 1, how, and how to roll back?** Fast-forward merge behind the existing
   `HYBRID_ROUTE_MODE` switch with `live` kept as default; rollback by `git revert`/previous tag, cache isolation by
   `ROUTE_D_CACHE_POLICY`, no DB migration. → `MODEL1_INTEGRATION_PLAN.md` §4–§6

## 2. Baseline integrity (P0)

| check | result |
|---|---|
| `freeze_evaluation_candidate.py --verify` on 157 | PASS (127 files, `3152f382…`) |
| `lock_cache_identity.py --verify` | PASS (157, `f9df4bf0…`) |
| GGUF / llama.cpp | `73f1484b…` / b12470 commit `dde9de82c`, archive `fc833716…` — match pins |
| docs IA, shared harness, cache & identity, holdout immutability, Source Gate suites | 524 passed |
| Construction /2 freeze suites | 34 passed; harness + `construction_planner/` 0 diff vs `c4ae9dd1f` |
| `/16` artifacts | 18/18 content unchanged; 1 recorded digest typo (corrected in this run) |
| behaviour | Holdout-6 64/72 · SLM-Ind-3 via router 28/30 · 0/36 negatives served |
| publication safety | `main`: 96 pending owner exceptions (already BLOCKED); branch adds 12 synthetic test passwords in frozen `/10`–`/12` tools |

## 3. Routing ablation (P1)

Same 138 inputs, same shared `scene_oracle.py`, real `/api/analyze` handler, AxoV9 on CPU, fresh DB per arm.
**All sets are exposed — diagnostic and regression evidence only.**

| arm | Holdout-6 | SLM-Ind-3 | negatives served | SLM calls | median ms (all cases) |
|---|---:|---:|---:|---:|---:|
| A production 157 | 64/72 | 28/30 | 0/36 | 59 | 144 |
| B deterministic-first extension | 64/72 | 28/30 | 0/36 | 47 | 117 |
| C SLM-first diagnostic | 55/72 | 21/30 | 0/36 | 137 | 4,197 |
| **158 as committed** | 64/72 | 28/30 | 0/36 | 47 | — (≡ B, 0 differences) |

The 12 cases B moves from AxoV9 to the parser: median 5,862 ms → 102 ms. Parser-only on all 706 exposed text cases
(original text, v3 step not included): 319 → 356/530 completed, 0/176 negatives served in both, the 37 changed cases
all `MATHEMATICALLY_VALID`. (The commit message of `2bb0211a1` calls this "deterministic completion"; it is the
parser-only figure.) Arm D (another adaptive policy) was not proposed: no data favoured it over B.

## 4. Product change: candidate 158

| | |
|---|---|
| product commit | `2bb0211a1` — `local_geometry_parser.py` (2 rules), `CACHE_VERSION` 157 → 158, lock, identity table, pending templates |
| test | `backend/tests/geometry/test_parser_routing_integrity.py`: red on 157 (9 failed / 6 controls passed), green on 158 (16 passed incl. `157:route-d` MISS) |
| freeze | `b92b68a94` (`EVALUATION_CANDIDATE.json` commit `35a17644a`, tree `bdb737bb…`, 127 files, clean tree) |
| Full T3 | **`FULL_PRODUCT_GATE_PASS`** (1,308 s): pytest 15,178 passed / 0 failed, vitest 203 files / 2,345, build, demo 5/5, crash 6/6 → `FULL_T3_RECEIPT.json` |
| frontend | 0 lines changed vs 157 |
| semantic environment hash | unchanged (`f9df4bf0…`): the parser is not part of the fingerprint, so the bump is a manual decision — noted in `OPEN_ISSUES.md` |
| prospective acceptance | **not measured** — Holdout-6 / SLM-Ind-3 are exposed; no score of 157 is transferred |
| browser UI on 158 | not re-measured (frontend byte-identical; the newly deterministic cases use the same Adapter /4 envelope as the 41 parser cases measured in `/16`) |

Consequence for metrics: an SLM-fallback rate on any registered set is no longer comparable — the SLM stratum shrinks
when the parser reads more. Future SLM gates should measure capability (`allow_parser_reconcile = false`) on a new blind
set, not the model's share of production traffic.

## 5. Policy consistency (P7, P8)

- OCR/Vision: nothing changed; local-only image upload still fails closed `503 LOCAL_ONLY_CLOUD_VISION_DISABLED`.
- "Gemini replaced" is not claimed: `LOCAL_TEXT_MODEL1_VERIFIED` (157) ≠ `FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED`.
- `AGENTS.md §2` asks for a *created* clean detached worktree; the owner forbids new worktrees. All measurements ran
  in the shared worktree on a clean tracked tree at branch HEAD ⇒ `AUTHORITATIVE_DETACHED_COMPLIANCE = NOT_VERIFIED`.
  `CLAUDE.md` / `AGENTS.md` were not edited.

## 6. Verdict flags (§33)

| flag | value | evidence |
|---|---|---|
| `CANDIDATE157_INTEGRITY_VERIFIED` | `TRUE` | §2 |
| `PARSER_SLM_ROUTING_INTEGRITY_VERIFIED` | `TRUE` (on 158) | §3, §4 |
| `METRIC_DRIVEN_ROUTING_BIAS_RESOLVED` | `TRUE` (on 158; 157 still carries it) | `PARSER_SLM_ROUTING_AUDIT.json` |
| `RESIDUAL_FAILURES_CLASSIFIED` | `TRUE` | `RESIDUAL_FAILURE_TRIAGE.json` |
| `EXTERNAL_INDEPENDENCE` | `NOT_MEASURED` | no third-party data or evaluator |
| `DEV_HOST_PERFORMANCE_MEASURED` | `TRUE` | `RUNTIME_CAPACITY_REPORT.json` |
| `TARGET_HARDWARE_PERFORMANCE_MEASURED` | `FALSE` | target unknown |
| `MULTIUSER_CAPACITY_VERIFIED` | `FALSE` | safe under load, but no registered target; dev host only |
| `PRODUCTION_CAPACITY_VERIFIED` | `FALSE` | no deployment |
| `MODEL1_TEXT_ARCHITECTURE_COMPATIBLE` | `TRUE` | `MODEL1_INTEGRATION_PLAN.md` §2 |
| `LOCAL_TEXT_MODEL1_VERIFIED` | `TRUE` for candidate 157 (`/16`, unchanged) · `NOT_VERIFIED` for 158 | prospective set needed for 158 |
| `LOCAL_VISION_REPLACEMENT_VERIFIED` | `FALSE` | postponed by owner |
| `FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED` | `FALSE` | Vision not replaced |
| `AUTHORITATIVE_DETACHED_COMPLIANCE` | `NOT_VERIFIED` | §5 |
| `FULL_PRODUCT_GATE_PASS` | `TRUE` (158, this run; 157 in `/16`) | `FULL_T3_RECEIPT.json` |
| `INTEGRATION_PLAN_READY` | `TRUE` | `MODEL1_INTEGRATION_PLAN.md` |
| `MAIN_MERGE_READY` | `FALSE` | owner decisions D1–D4 below |
| `MAIN_MERGE_COMPLETED` | `FALSE` | — |
| `REMOTE_PUSH_COMPLETED` | `FALSE` | — |

## 7. Owner decisions needed

| id | decision | options |
|---|---|---|
| D1 | merge scope | Option A (wait for Vision) or Option B (text Model 1 behind `HYBRID_ROUTE_MODE`, `live` stays default) |
| D2 | which candidate | 157 (accepted on Holdout-6, carries the routing defects) or 158 (fixed, T3 PASS, regression PASS, needs a new blind/independent measurement to claim acceptance) |
| D3 | measurement compliance | allow one temporary detached worktree for the final pre-merge measurement, or amend `AGENTS.md §2` |
| D4 | publication safety | exception entries (or relocation) for the 12 synthetic test passwords; the 96 pending traceback exceptions already on `main` |
| D5 | independent validation | name an evaluator / problem source (protocol ready) |
| D6 | deployment | Linux llama.cpp pin, GGUF hosting + backup, request deadline, target hardware, capacity target |

## 8. Commits of this run

`2bb0211a1` parser fix + CACHE 158 · `35a17644a` P0/P2/P3 records · `b92b68a94` freeze candidate 158 · then the
evidence/docs commit containing this report (`run.json` lists all).
