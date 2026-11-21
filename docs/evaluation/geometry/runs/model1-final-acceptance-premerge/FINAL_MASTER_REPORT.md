# AXO HYBRID /18 — Model 1 final acceptance, evidence integrity & pre-merge closure (`FINAL_MASTER_REPORT`)

**Date:** 2026-11-21 · **Run ID:** `model1-final-acceptance-premerge` · **Branch:** `feat/model1-final-acceptance-premerge`
(from `/17` `6789da55a`, shared worktree; `main` = `origin/main` = `bc6ff5e33` untouched; nothing merged, pushed or
tagged). Audience: the owner.

> **Verdict: `BLOCKED_BY_INDEPENDENT_EVIDENCE`.** Candidate 158 is intact and has no known product defect, but no
> valid unexposed data exists to accept it, so `LOCAL_TEXT_MODEL1_VERIFIED` stays `NOT_VERIFIED` for 158. Behind that,
> three policy blockers need the owner: measurement compliance (D3), publication exceptions (D4) and merge scope (D1),
> plus a live-route smoke decision (D7). No product code changed in /18.

## 1. Answers

1. **Does 158 have new acceptance evidence?** No. Prospective internal acceptance and external validation are both
   `NOT_MEASURED`: no traceable source or independent evaluator was available, every existing set is exposed, and no
   dataset was invented to force the gate. Thresholds are pre-registered (the `/16` criteria, unchanged) and an evaluator
   kit is ready. → `PROSPECTIVE_ACCEPTANCE_REPORT.json`, `EVALUATOR_MANIFEST_TEMPLATE.json`
2. **What was really closed, what needs the owner?** Closed: identity of 158 (all checks PASS), classification of every
   publication finding (0 true secrets; 12 synthetic test passwords proposed as exact exceptions), a corrected rollback
   plan, the merge audit and the two-session plan. Owner: D1 scope, D2 candidate, D3 measurement, D4 exceptions, D5
   independent evaluator, D6 deployment, D7 live smoke.
3. **Does testing meet the authoritative-measurement policy?** No. `AGENTS.md §2` requires a *created* clean detached
   worktree; the owner forbids new worktrees; all 158 measurements ran in the shared worktree.
   → `AUTHORITATIVE_MEASUREMENT_STATUS.md` (exact plan for either owner option)
4. **Is publication safety good enough for `main`?** Not yet. The range `main..HEAD` has 12 `HARDCODED_PASSWORD` hits
   (11 path/blob pairs, all the synthetic register password of loopback test accounts in frozen `/10`–`/12` tools);
   `main` itself carries 96 pending traceback/placeholder findings. Gate `BLOCKED_OWNER_DECISION`.
   → `PUBLICATION_SAFETY_CLOSURE.json`, `PUBLICATION_EXCEPTION_PROPOSAL.json`
5. **Can text Model 1 merge alone with Gemini `live` as default and Vision not replaced?** Technically yes: local modes
   are opt-in, `live` stays the default, local-only image input fails closed, no DB migration. But the merge also
   changes the shared Source Gate / Planner / Kernel that the `live` route uses, and the `live` route has not been run
   on 158. → `PREMERGE_INTEGRATION_AUDIT.md` §3
6. **What would merge, how, how to roll back?** The `/18` tip (product tree = 158, `bdb737bb…`; everything after
   `b92b68a94` is docs). Recommended `git merge --no-ff` (single revertable commit) after the owner tags `bc6ff5e33`;
   rollback by redeploying `bc6ff5e33` (no migration, cache isolated by policy) or `git revert -m 1 M`; for a
   fast-forward, a tree-restore commit — not a 401-commit revert. → `PREMERGE_INTEGRATION_AUDIT.md` §5–§6
7. **How do the two backend sessions split after merge?** A owns Construction /2 + Model 2 files; B owns the parser,
   normalizer, SLM extractor/runtime, router; Typed Facts, Source Gate, Planner/Registry, Kernel, Adapter schema, cache
   identity and the harness are shared and locked. → `POST_MERGE_TWO_SESSION_PLAN.md`

## 2. Gates

| gate | status | evidence / missing |
|---|---|---|
| F0 baseline integrity | **PASS** | freeze `bdb737bb…`, lock 158/`f9df4bf0…`, GGUF `73f1484b…`, llama.cpp b12470 `dde9de82c`, 579 regression tests, 0 product diff since `2bb0211a1` → `CANDIDATE158_FINAL_IDENTITY_AUDIT.json` |
| F1 routing safety | **PASS** (exposed sets) | `/17`: 706 exposed cases parser-only + 138 full-route, 0 served negatives, 0 invalid scenes; `/18` rerun of `test_parser_routing_integrity.py` 16/16 |
| F2 prospective acceptance | **NOT_MEASURED** | needs a frozen unexposed set measured once on 158 |
| F3 independent evidence | **NOT_MEASURED** | needs an external source + evaluator + reviewed oracle |
| F4 authoritative measurement | **BLOCKED** (`NOT_VERIFIED`) | owner D3 |
| F5 publication safety | **BLOCKED** | owner D4 (11 entries) + decision on main's 96 |
| F6 full product regression | **PASS** (non-authoritative location) | `/17` Full T3 on `b92b68a94`; not re-run (no product change) |
| F7 merge safety | **PASS** (audit complete, blockers listed) | diff, deps, rollback, flags, `main` untracked folder (sha256 snapshot, untouched) |
| F8 owner authorization | **BLOCKED** | D1, D2, merge permission; running /18 is not authorization |

**Transition to `FINAL_ACCEPTANCE_PASS_READY_FOR_OWNER_DECISION`:** a valid set measured once on 158 meets the
pre-registered criteria (F2) **and** D3 is decided with a compliant Full T3 (F4) **and** the range publication scan exits 0
(F5). F3 is required for any claim of external independence, not for this transition. If F2 fails, the verdict becomes
`NOT_READY_DUE_TO_PRODUCT_DEFECT` for 158 (157 remains the last accepted candidate, with its two known routing defects).

## 3. Cache-identity finding (P1)

Candidate 158 is protected: `CACHE_VERSION` 158 makes every `157:route-d` row miss (tested). The structural gap stays:
the semantic fingerprint and Route D cache key carry version *labels* (`local-geometry-parser/3`,
`geometry-functions/33`, `geometry-fact-planner/26`, `geometry-function-engine/24`) that did not move across /5–/17,
so a future local-route change without a manual bump would replay old envelopes. Not fixed here (it would change the
candidate identity); assigned to Session B.

## 4. Verdict flags (§XV)

| flag | value |
|---|---|
| `CANDIDATE158_IDENTITY_VERIFIED` | `TRUE` |
| `PARSER_SLM_ROUTING_INTEGRITY_VERIFIED` | `TRUE` (exposed regression sets) |
| `PROSPECTIVE_TEXT_ACCEPTANCE_STATUS` | `NOT_MEASURED` |
| `EXTERNAL_INDEPENDENCE` | `NOT_MEASURED` |
| `AUTHORITATIVE_DETACHED_COMPLIANCE` | `NOT_VERIFIED` (`BLOCKED_OWNER_DECISION`) |
| `SOURCE_GROUNDING_VERIFIED` | `NOT_VERIFIED` for 158 on unexposed data (0 ungrounded served on every exposed set) |
| `NEGATIVE_SAFETY_GATE_PASS` | `NOT_VERIFIED` for 158 on unexposed data (176/176 + 36/36 exposed negatives safe) |
| `SLM_INDEPENDENT_CAPABILITY_STATUS` | `NOT_MEASURED` for 158 (exposed SLM-Ind-3 under SLM-first 21/30, diagnostic) |
| `FULL_PRODUCT_GATE_PASS` | `TRUE` (158, `b92b68a94`, shared worktree) |
| `LOCAL_TEXT_MODEL1_VERIFIED` | `TRUE` for 157 (`/16`) · `NOT_VERIFIED` for 158 |
| `LOCAL_VISION_REPLACEMENT_VERIFIED` | `FALSE` |
| `FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED` | `FALSE` |
| `PUBLICATION_SAFETY_GATE_PASS` | `BLOCKED_OWNER_DECISION` |
| `INTEGRATION_PLAN_READY` | `TRUE` |
| `TECHNICAL_PREMERGE_READY` | `FALSE` (F2, F4, F5 open; live route not run on 158) |
| `MERGE_SCOPE_APPROVED` | `BLOCKED_OWNER_DECISION` |
| `OWNER_MERGE_AUTHORIZED` | `FALSE` |
| `MAIN_MERGE_READY` | `FALSE` |
| `MAIN_MERGE_COMPLETED` | `FALSE` |
| `REMOTE_PUSH_COMPLETED` | `FALSE` |

## 5. Owner decisions

| id | question | agent's technical recommendation (not an approval) |
|---|---|---|
| D1 | Option A (wait for Vision) or Option B (text Model 1, `live` default, Vision not replaced) | B, under the conditions of `PREMERGE_INTEGRATION_AUDIT.md` §7 |
| D2 | candidate 158 or 157 | 158 — 157 carries a metric-driven parser exclusion and a length-goal defect (both refuse correctly but send exact cases to the SLM) |
| D3 | temporary detached worktree, or amend `AGENTS.md §2` | either; the plan for both is written |
| D4 | approve the 11 proposed exceptions / squash / relocate; decide main's 96 | approve the 11 exact entries (owner command in `PUBLICATION_SAFETY_CLOSURE.json`) |
| D5 | name an evaluator and a problem source | protocol + template ready |
| D6 | deployment work (Linux runtime, GGUF hosting/backup, deadline, multi-process idempotency, target capacity) | not needed to merge under the flag; needed before public local mode |
| D7 | budgeted live Gemini smoke of the default route on 158, or a written waiver | run a small registered smoke (needs `ALLOW_LIVE_AI=1` + quota decision) |

## 6. What /18 did not do

No product change, no new candidate, no CACHE bump, no Full T3 re-run, no new dataset, no worktree, no exception
granted, no edit of frozen evidence /5–/17, no change of `HYBRID_ROUTE_MODE`, no OCR/Vision, Model 2 or Construction /2
work. The /18 records are documentation only (`freeze --verify` PASS at the tip).
