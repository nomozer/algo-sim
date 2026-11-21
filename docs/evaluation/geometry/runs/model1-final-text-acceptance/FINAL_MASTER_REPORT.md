# AXO HYBRID /19 — Authoritative Measurement, Prospective Text Acceptance & Pre-Merge Closure (`FINAL_MASTER_REPORT`)

**Date:** 2026-11-21 · **Run ID:** `model1-final-text-acceptance` · **Branch:** `feat/model1-final-text-acceptance` (base `/18`: `cf0b646f5`; measured detached HEAD: `b10c0a1e4`) · **Target `main`:** `bc6ff5e33` (untouched)

> **Executive Verdict (`NOT_READY_FOR_MODEL1_TEXT_REPLACEMENT` on Candidate 158; `MAIN_MERGE_READY = FALSE`):**
> On clean detached worktree `measure-model1-c158` (`b10c0a1e4`, Candidate 158 intact), **Authoritative Full T3 PASSED** (`FULL_PRODUCT_GATE_PASS`, `15,178` pytest, `2,345` Vitest, `AUTHORITATIVE_DETACHED_COMPLIANCE = VERIFIED`). However, single-shot prospective evaluation on frozen Class-B **`Holdout-7` (`58+22`)** **FAILED** acceptance thresholds: **`END_TO_END_SYSTEM_SCORE = 46/58 (0.7931)`** (95% Wilson CI `[0.6723, 0.8775]`, `< 0.85`), **`CANDIDATE_FALLBACK_SCORE = 3/15 (0.2000)`** (95% Wilson CI `[0.0705, 0.4519]`, `< 0.50`), and isolated **`INDEPENDENT_SLM_SCORE = 25/58 (0.4310)`** (95% Wilson CI `[0.3118, 0.5588]`, `< 0.60`, `gate_pass = false`). Zero wrong scenes (`0`), zero grounding violations (`0`), and `22/22` safe negative refusals confirm **soundness holds**, while colloquial and diverse phrasing (`learner_colloquial 1/10`, `teacher_wording 12/15`) remains below acceptance criteria. Combined with pending publication exceptions (`D4`, 12 branch hits / 96 main hits) and unrun live Gemini API smoke (`D7`), `MAIN_MERGE_READY = FALSE`.

---

## 1. Candidate 158 Lock & Recovered Root Cause (`test_holdout_freeze_is_intact()`)

| Field | Verified Value |
|---|---|
| Candidate | **`158`** (`CANDIDATE158_IDENTITY_VERIFIED = TRUE`) |
| Product commit (`backend/app`, `frontend/src`) | `2bb0211a1057c5d2a503f8a1f19e96cf84decff5` (`2bb0211a1`) — `0` diff to `HEAD` |
| Evaluation candidate freeze commit | `b92b68a94` (`EVALUATION_CANDIDATE.json` field `35a17644a`) |
| Measured HEAD (`measure-model1-c158` & branch) | `b10c0a1e4022dfd5af93aeb6ebf75de61078a901` (added root `.gitattributes` LF rule only) |
| Measured system tree SHA-256 (`127` files) | `bdb737bba9ab94d0274b57e25089c01d4cb47935d5989658e7c13aad1e79b132` |
| Cache & route policy | `CACHE_VERSION = "158"` · `ROUTE_D_CACHE_POLICY = "158:route-d"` · `semantic_environment_hash = f9df4bf0c8bd458a278d2692567fa3e096340ae37ff5493730dff4067c0f5e19` |
| Local SLM & runtime | `Qwen3-0.6B-AxoV9-Q4_K_M` (`73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35`) + `llama.cpp b12470` (`0` weight/prompt edits) |
| Default route mode | `HYBRID_ROUTE_MODE = "live"` preserved |

**Recovered Root Cause of Interruption Failure:**
1. Prior detached run `t3_run1` (`98163cce5`, `1351.0s`, exit `1`) failed **1 test** (`test_aggregate_replay_on_12_inputs_equals_the_frozen_12_deliverables`) solely because Windows `core.autocrlf=true` converted frozen `V12_ACCEPTANCE_MANIFEST.json` from LF to CRLF while frozen `aggregate.py::_sha()` hashes raw bytes.
2. Prior detached run `t3` (`98163cce5`, `1320.0s`, exit `1`) forced LF across all files, passing `test_shared_live_harness.py` while breaking **4 historical CRLF-pinned tests** (`test_A1_hash_artifact_nguon_khop`, `test_run_receipts_and_hashes_are_consistent`, `test_sealed_khong_bi_sua_sau_khi_niem_phong`, `test_exporter_idempotence`).
3. The prior session then left invalid uncommitted edits in `docs/evaluation/geometry/harness/live-acceptance/aggregate.py` (+3/-1) and `backend/tests/geometry/test_shared_live_harness.py` (+15), tripping `test_holdout_freeze_is_intact()` (`47e39bbf...` != locked `35827769...`).
4. **Clean Fix (`/19`):** Reverted both uncommitted edits to restore exact byte-locked harness, added `.gitattributes` pinning LF strictly for `V12_ACCEPTANCE_MANIFEST.json` (`b10c0a1e4`), re-materialized `measure-model1-c158`, and passed all 6 previously failing tests (`6 passed in 2.39s`) on a clean working tree (`0` dirty files).

---

## 2. Authoritative Detached Full T3 Verification (`AUTHORITATIVE_FULL_T3_RECEIPT.json`)

Executed `cd frontend && npm run test:full` (`ALLOW_LIVE_AI = 0`, clean tree before & after) inside temporary detached worktree `measure-model1-c158` (`b10c0a1e4`), log at `D:\tmp\axo19\t3_authoritative\full-t3.log` (`sha256: 95b1b4dbb2c546b39d8db7d2a9dfcc823f8b47ed809869283a4596eb62949a7b`):

- **`verdict`**: **`FULL_PRODUCT_GATE_PASS`** (`exit_code = 0`, `1346.9s` outer / `1345.6s` wrapper, `AUTHORITATIVE_DETACHED_COMPLIANCE = VERIFIED`).
- **`backend_pytest`**: **`15,178 passed, 0 failed`**, `8 skipped`, `9 deselected`, `12 xfailed`, `1 warning` (`1172.76s` / `1178.9s`).
- **`frontend_vitest`**: **`203 passed (203)` files**, **`2,345 passed (2,345)` tests**, `0 failed` (`140.83s` / `144.1s`).
- **`typecheck_build`**: **PASS** (`21.6s`), **`demo_replay`**: **`5/5` + reduced chain `1/1`** (`0.6s`), **`demo_crash_surface`**: **`6/6` (`0` 500s)** (`0.4s`).
- Post-T3 cleanup: `measure-model1-c158` verified clean, caches removed, and worktree cleanly removed via `git worktree remove` without `--force`.

---

## 3. Prospective Text Acceptance on Frozen `Holdout-7` (`58+22`, Class B)

- **Provenance & Independence ([`INDEPENDENT_EVIDENCE_STATUS.md`](INDEPENDENT_EVIDENCE_STATUS.md), [`PROVENANCE.json`](holdout-7/PROVENANCE.json), [`EXPOSURE_CHECK.json`](holdout-7/EXPOSURE_CHECK.json)):** Hand-written by the `/19` agent from a pre-registered 4-family sampling plan (`58` positive in-scope + `22` negative = `80` cases; `376/376` coordinate relation checks via `check_relations.py`); `0` string and `0` template containment collisions across `29,643` prior strings. **Class B internal prospective only — `EXTERNAL_INDEPENDENCE = NOT_MEASURED`** (public MOET search yielded PDF/image aggregators requiring out-of-scope OCR; no external evaluator available).
- **Criteria & Freeze ([`ACCEPTANCE_CRITERIA.json`](holdout-7/ACCEPTANCE_CRITERIA.json), [`ACCEPTANCE_FREEZE.json`](holdout-7/ACCEPTANCE_FREEZE.json), [`CANDIDATE_FREEZE.json`](holdout-7/CANDIDATE_FREEZE.json)):** Identical thresholds to `/16` (`>= 0.85` E2E, `>= 0.50` fallback with `n >= 8` & `>= 5` scenes, `>= 0.60` isolated SLM, zero tolerance on safety/egress). Candidate 158 bound strata: `44 PARSER_COMPLETE`, `14 SLM_REQUIRED`, `22 negative`. Executed single-shot cold on isolated `:8019` / `:4173/app` (`ALLOW_LIVE_AI=0`, `local-only-scoped`, `0` cache/replay hits in browser run, `identity_mismatches = []`).

### 3.1 Top-Level Scores & 95% Wilson Intervals

| Metric | Score | 95% Wilson CI | Threshold | Gate Verdict |
|---|---:|---|---:|---|
| **`END_TO_END_SYSTEM_SCORE`** | **`46/58 (0.7931)`** | `[0.6723, 0.8775]` | `>= 0.85` (`>= 50`) | **FAIL** |
| **`CANDIDATE_FALLBACK_SCORE`** | **`3/15 (0.2000)`** | `[0.0705, 0.4519]` | `>= 0.50` (`n >= 8`, `>= 5` scenes) | **FAIL** |
| **`INDEPENDENT_SLM_SCORE`** (`allow_parser_reconcile=false`) | **`25/58 (0.4310)`** | `[0.3118, 0.5588]` | `>= 0.60` (`>= 35/58`) | **FAIL** (`gate_pass=false`) |
| **`LEGACY_BASELINE_STRATUM_SCORE`** (`SLM_REQUIRED` stratum) | **`3/14 (0.2143)`** | `[0.0757, 0.4759]` | `—` (`0` det rescued) | **Recorded** |
| **Negative Safe Refusal** (`22` cases) | **`22/22 (1.0000)`** | `[0.8513, 1.0000]` | `1.00` | **PASS** |
| **`SLM_CAPABILITY_AUDIT` (isolated)** | `ext=0.6379`, `ground=0.5517` | `—` | `false=0`, `invalid=0` | `false=0`, `invalid=0` |

### 3.2 Stratified Breakdown (`PROSPECTIVE_TEXT_ACCEPTANCE.json`)

| Slice | Completed / Total | Rate (95% Wilson) | Deterministic | Live SLM | Served `p50 / p95` ms | Uncompleted Case IDs |
|---|---:|---|---:|---:|---:|---|
| Stratum `PARSER_COMPLETE` | `43/44` | `0.9773` `[0.8819, 0.9960]` | `43` | `0` | `147.0 / 332.0` | `C02` (routed to SLM, `CONDITIONAL_CLAUSE`) |
| Stratum `SLM_REQUIRED` | `3/14` | `0.2143` `[0.0757, 0.4759]` | `0` | `3` | `4377.0 / 8075.0` | `G01, G03, G11, C01, C03..C08, C10` |
| `textbook_canonical` | `17/17` | `1.0000` `[0.8157, 1.0000]` | `16` | `1` (`T06`) | `—` | `—` |
| `exam_wording` | `16/16` | `1.0000` `[0.8064, 1.0000]` | `16` | `0` | `—` | `—` |
| `teacher_wording` | `12/15` | `0.8000` `[0.5481, 0.9295]` | `10` | `2` (`G06, G08`) | `—` | `G01, G03, G11` |
| `learner_colloquial` | `1/10` | `0.1000` `[0.0179, 0.4042]` | `1` | `0` | `—` | `C01..C08, C10` |

### 3.3 Failure Taxonomy, Safety, Network & Host Latency
- **End-to-end unserved positives (`12` fail-closed, `0` wrong scenes):**
  - SLM self-refused (`4`): `G03, C01, C04, C05` (`SLM_REPORTED_UNRESOLVED` -> `AMBIGUOUS_FACT`) + `G11` (`REJECTED_NO_GROUNDED_GOAL` -> `AMBIGUOUS_FACT`).
  - Lowered & grounded by SLM, rejected downstream (`7`): `G01, C08` (`NOT_ASKED_IN_SOURCE`), `C03, C10` (`UNGROUNDED_VALUE`), `C07` (`OBJECT_NOT_IN_QUOTE`), `C02, C06` (`CONDITIONAL_CLAUSE`).
- **Isolated `SLM_CAPABILITY_AUDIT` unserved positives (`33`):** `19` `SLM_UNRESOLVED:AMBIGUOUS_FACT`, `1` `GROUNDING_REJECTED:AMBIGUOUS_FACT`, `1` `MULTI_GOAL_INCOMPLETE:REQUEST_NOT_ANSWERED`, and `12` `GROUNDED_AND_LOWERED` rejected downstream (`SOURCE_OBJECT_MISMATCH: 3`, `NOT_ASKED_IN_SOURCE: 2`, `CONDITIONAL_CLAUSE: 2`, `UNGROUNDED_VALUE: 2`, `AMBIGUOUS_VALUE_QUOTE: 1`, `SOURCE_PREMISE_UNREAD: 1`, `OBJECT_NOT_IN_QUOTE: 1`).
- **Oracle, Safety, UI & Network:** `46/46` served scenes **`MATHEMATICALLY_VALID`** (`0` invalid, `0` validation error); `0` wrong served, `0` grounding violations, `0` unverified relations, `0` fabricated/mismatched numbers; **`10/10` UI scenarios PASS** (including `I05` conditional clarification on `N01` & 4 responsive viewports); `0` browser external requests; `0` proxy interceptions during run (`2` separate selfcheck blocks proven on `:18999`); `321` TCP heartbeats, `0` non-loopback records (`physical_internet_disconnect = NOT_MEASURED`).
- **Windows dev host latency & stack RAM (`158` samples):** uncached deterministic served `n=43` `p50/p95 = 147.0 / 332.0 ms`, live SLM served `n=3` `4,377.0 / 8,075.0 ms`, rejected valid `n=12` `p50 = 2,991.0 ms`, rejected negative `n=22` `p50 = 109.5 ms`, warm cache `n=4` `p50 = 38.7 ms`, concurrency `all_200=true`; peak WS `llama 901.8 MB`, `chromium 602.8 MB`, `backend 122.2 MB`.

---

## 4. Publication Safety, Gemini Compatibility & Merge Readiness

- **Publication Safety ([`PUBLICATION_SAFETY_STATUS.json`](PUBLICATION_SAFETY_STATUS.json)):** Range `cf0b646f5..b10c0a1e4` = **`0` violations** (`PASS`). Range `bc6ff5e33..b10c0a1e4` = **`12` `HARDCODED_PASSWORD` violations** (`11` path/blob pairs in frozen `/10`–`/12` test scripts, synthetic loopback test passwords) + **`96` `main` baseline entries** still pending (`0` true secret exposures). Status: **`BLOCKED_OWNER_DECISION`** (`0` exceptions granted).
- **Gemini Live Compatibility ([`GEMINI_LIVE_COMPATIBILITY_AUDIT.json`](GEMINI_LIVE_COMPATIBILITY_AUDIT.json)):** Offline downstream replay (`replay_compat.py`, `ALLOW_LIVE_AI=0`) comparing `main` (`bc6ff5e33`) vs Candidate 158 across all 5 historical Gemini-shaped corpora (`82` cases: `scene3d_v2_replacement` 43, `v2_backend_gen_main` 14, `v2_backend_gen_point_line` 8, `v2_nl_cert_line_plane` 9, `v2_nl_cert_point_line` 8 — the two `point_line` corpora share SHA-256 `a41d0e4f...`, totaling `82` replay runs across 5 corpora) shows **`82/82` identical status, reason, and answers**, **`0` regressions**, **`0` crashes**. **Live Gemini API smoke (`ALLOW_LIVE_AI=1`): `NOT_MEASURED`** (pending owner budget/authorization **D7**).
- **Merge Readiness & Rollback ([`MERGE_READINESS_AND_ROLLBACK_AUDIT.md`](MERGE_READINESS_AND_ROLLBACK_AUDIT.md)):** `main` (`bc6ff5e33`) and its 6-file untracked `post-merge-cleanup-closure/` snapshot are verified 100% untouched. Forward-only `--no-ff` merge (`pre-model1-merge` tag, `git revert -m 1 M`, or redeploy `bc6ff5e33` with zero DB migrations and `132:route-d` vs `158:route-d` cache isolation) is documented and ready **only after** blockers close. **`MAIN_MERGE_READY = FALSE`**, **`MAIN_MERGE_COMPLETED = FALSE`**, **`REMOTE_PUSH_COMPLETED = FALSE`**.

---

## 5. Missing Owner Decisions Required Next

| ID | Decision / Blocker | Current Status & Options |
|---|---|---|
| **H7-Fail** | Candidate 158 failed prospective `Holdout-7` (`46/58`, `3/15` fallback, `25/58` isolated SLM) | Keep Candidate 158 unaccepted for local Model 1 text replacement (`LOCAL_TEXT_MODEL1_VERIFIED = FALSE`), run a new Model 1 recovery wave targeting colloquial phrasing (`learner_colloquial` 1/10) + quote grounding, **or** decide whether to integrate shared core / Candidate 157 only under explicit written acceptance of known limits |
| **D1** | Merge scope | Option A (wait for Vision) vs Option B (text-only core behind dormant local flags, `live` default) |
| **D2** | Candidate selection | Candidate 157 (`64/72` on `/16` Holdout-6, carries routing bias/len-goal bug) vs Candidate 158 (fixes routing, `FAIL` on prospective `Holdout-7`) |
| **D3** | Measurement policy compliance | Satisfied for Candidate 158 in `/19` (`AUTHORITATIVE_DETACHED_COMPLIANCE = VERIFIED` via `measure-model1-c158`); decide standing rule in `AGENTS.md §2` vs future runs |
| **D4** | Publication exceptions | Review & approve/relocate 11 exact synthetic-password pairs (`/10`–`/12` tools) + decide `main`'s 96 pending entries |
| **D5** | External independent validation | Supply rights-cleared unseen Vietnamese text source & independent human evaluator (`EXTERNAL_INDEPENDENCE = NOT_MEASURED`) |
| **D6** | Production local deployment | Linux `llama.cpp` runtime pin, hosted GGUF + backup, request deadline, target low-end hardware (`PHYSICAL_LOW_END = NOT_MEASURED`) |
| **D7** | Live Gemini default route | Authorize budgeted live Gemini smoke (`ALLOW_LIVE_AI=1`) on shared core or record written waiver |

---

## 6. Final Mandatory Verdict Flags

- `CANDIDATE158_IDENTITY_VERIFIED = true`
- `AUTHORITATIVE_DETACHED_COMPLIANCE = "VERIFIED"`
- `FULL_PRODUCT_GATE_PASS = true`
- `PROSPECTIVE_TEXT_ACCEPTANCE = "FAIL"`
- `SYSTEM_TEXT_COMPLETION_THRESHOLD_MET = false` (`46/58 = 0.7931`, 95% Wilson `[0.6723, 0.8775]`)
- `SLM_FALLBACK_GATE_MET = false` (`3/15 = 0.2000`, 95% Wilson `[0.0705, 0.4519]`)
- `SLM_INDEPENDENT_CAPABILITY_GATE_MET = false` (`25/58 = 0.4310`, 95% Wilson `[0.3118, 0.5588]`, `gate_pass = false`)
- `SOURCE_GROUNDING_VERIFIED = true` (`0` grounding/unverified/wrong scenes served)
- `NEGATIVE_SAFETY_GATE_MET = true` (`22/22 = 1.0000`, `0` external calls)
- `SEMANTIC_REWRITE_SAFETY_VERIFIED = "NOT_MEASURED"` (not re-run on Candidate 158's modified `local_geometry_parser.py`)
- `COMPOSITE_LIVE_TEXT_ACCEPTED = false`
- `LOCAL_TEXT_MODEL1_VERIFIED = false` (for Candidate 158; Candidate 157 `/16` historical record preserved)
- `LOCAL_VISION_REPLACEMENT_VERIFIED = false`
- `FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED = false`
- `EXTERNAL_INDEPENDENCE = "NOT_MEASURED"`
- `OFFLINE_GEMINI_DOWNSTREAM_COMPATIBILITY = "PASS_82_OF_82"`
- `LIVE_GEMINI_API_SMOKE = "NOT_MEASURED"`
- `PUBLICATION_SAFETY_GATE_PASS = "BLOCKED_OWNER_DECISION"`
- `MAIN_MERGE_READY = false` · `MAIN_MERGE_COMPLETED = false` · `REMOTE_PUSH_COMPLETED = false`
