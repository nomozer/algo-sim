# Hybrid backend — validation and cutover report

Run `hybrid-live-validation` · Master Epic `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · backend only (`frontend/**`
untouched) · 2026-11-03.

> [!IMPORTANT]
> **Gemini was not called.** The one grounded preflight stopped at `PAID_PROJECT_NOT_VERIFIED` before any request
> (0 HTTP requests, USD 0.00). Every number below is **offline** (gold TypedFactNext replay, no provider). No token,
> latency, cost or extraction-quality figure for Gemini exists, and none is estimated.

## Status labels (evidence-bound)

| label | status | evidence |
|---|---|---|
| `BACKEND_HYBRID_OFFLINE_VERIFIED` | **YES** | §8, §15 — gold replay 72/72 + 72/72 refused, 0 wrong-served; Full T3 `FULL_PRODUCT_GATE_PASS` (`16 673` pytest, `1 502` vitest) |
| `LIVE_GEMINI_MEASURED` | **NO** — `NOT_MEASURED` | §3 — `live-preflight.json` |
| `LIVE_GEMINI_QUALITY_VALIDATED` | **NO** — `NOT_MEASURED` | §3 |
| `PLANNER_COMPOSITION_VERIFIED` | **YES, as registered decomposition, offline** | §12 |
| `GENUINE_DISCOVERY_NOT_ESTABLISHED` | **unchanged** | §13 |
| `HYBRID_CUTOVER_BLOCKED` | **BLOCKED** | §17, §19 |
| `LEGACY_REMOVAL_BLOCKED` | **BLOCKED** | §16, §18 |

## 1. Git checkpoint

| | commit | note |
|---|---|---|
| before | `957ec289` | candidate `fba8b7a7`, product `adf4a113`, measured `39e9f54b…` (verified at start: clean tree, `--verify` MATCH) |
| product | `55db50c3` | backend repairs (§11), registry `/32`, engine `/24` |
| tool | `db9177c7` | `tools/legacy_dependency_inventory.py` |
| candidate (superseded) | `d5c4098b` | first freeze (product `55db50c3`, `f4ed426a…`); Full T3 attempt 1 failed on one divergence-layer key (§15) |
| product (review round 1) | `57457fc4` | one altitude-foot grammar for both readers; docstrings (§11) — no served/refused change |
| **candidate** | **`79bbc053`** | `EVALUATION_CANDIDATE.json` frozen at `57457fc4` on a clean tree; templates re-bound; `live-preflight.json` re-run |
| after | see the final commit of this run (report + receipts + governance) | no merge, no push |

## 2. Candidate identity

- Product commit (`product_commit_sha` and `EVALUATION_CANDIDATE.json` `commit` at freeze time):
  `57457fc4c59094c5e57dd934bffd73533d82b81e`, frozen in candidate commit `79bbc0531df89d3757ae16a6d8c5c0388fdac84b`;
  `measured_system.tree_hash` `6202a6a67b555a0d18b59c0edbea7c396b8fe6f1488fb1984f4e7663be1e1421` (118 files);
  `cay_lam_viec_sach = true` (`frozen-evaluation-candidate.json`, `candidate_divergence.json`).
- Registry `geometry-functions/32`, Planner `geometry-fact-planner/26`, Engine `geometry-function-engine/24`,
  TypedFactNext `/2`, Adapter `hybrid-simulation-adapter/4`, `CACHE_VERSION = 131`, `DEFAULT_MODE = LLM_ONLY`,
  `HYBRID_ROUTE_MODE = off` by default.
- Pilot templates re-bound to `6202a6a6…`, still `PENDING_OWNER_DECISION`, `paid_project_confirmed: false`
  (`runner_sha256 = e9c6ad43…`, unchanged).
- Prior candidates (`fba8b7a7`, `123e57da`, `15d236eb`, …) and their receipts are unchanged.

## 3. Gemini live execution status — `BLOCKED_PREFLIGHT` (`PAID_PROJECT_NOT_VERIFIED`)

One check, with the runner's own authority (`run_s2_student_language_pilot.verify_paid_project`), recorded in
`live-preflight.json` (presence and source only, never values):

| condition | observed |
|---|---|
| `GEMINI_API_KEY` | present (root `backend/.env`, `AQ.` kind) — never implies paid billing |
| `GOOGLE_CLOUD_PROJECT` / `GCP_PROJECT` | absent |
| Cloud Billing OAuth token / `gcloud` | absent / not on PATH |
| `owner-paid-project-attestation/1` file | absent |
| runner / caps | `--delegated-c21` ready; `gemini-2.5-flash`; K-1 ≤ 16 / USD 1, S-2 ≤ 36 / USD 2, R-1 ≤ 18 / USD 1, total ≤ 70 / USD 4 |
| decision | `BLOCKED_PREFLIGHT`, 0 requests, 0 approvals minted, USD 0.00 |

Not done, by rule: no `paid_project_confirmed: true`, no forged approval, no free-tier switch, no replay labelled live.

**Shortest valid unblock (Owner, one of):**
1. **Cloud Billing API:** set `GOOGLE_CLOUD_PROJECT=<project-id>` and provide a Cloud Billing OAuth token
   (`GOOGLE_OAUTH_ACCESS_TOKEN`, or `gcloud auth application-default login` on PATH) for the project that owns the key;
   the runner reads `billingInfo.billingEnabled`.
2. **Owner attestation:** write, yourself, a file with `schema: owner-paid-project-attestation/1`,
   `authorization_source: EXPLICIT_OWNER_SEPARATE_STATEMENT`, `paid_project_confirmed: true`, a `statement_ref` and a
   `statement_quote` (≥ 10 chars) of your own statement, and pass it to the runner.

Then `--delegated-c21` runs K-1 → S-2 → R-1 automatically inside the caps above; no further approval round is needed
for those three pilots on this candidate.

## 4–7. Extraction quality, tokens, provider latency, cost per problem

`NOT_MEASURED` — no live request was made (§3). The harness that will measure them is unchanged and ready:
`run_s2_student_language_pilot.py` (per-request usage incl. thinking tokens; missing usage recorded `UNKNOWN` and
charged at the request ceiling), `score_s2_student_language_pilot.py` (8 deterministic metrics vs gold), and
`run_paired_route_evaluation.py` (paired LLM_ONLY vs Hybrid). Deterministic backend time is reported separately in §12.

## 8. End-to-end correctness (offline, gold extraction)

Gold TypedFactNext `/2` payloads → Source Gate → FactGraph → Planner → Registry → Compiler/IR → Kernel → Adapter `/4`
(`gold-replay-regression.json`, `wave3-gold-replay.json`; head `79bbc053`, product committed, 0 provider calls; the same counts were recorded at `d5c4098b` in commit `10ea9acd`):

| set | before (`fba8b7a7`) | after (`79bbc053`) |
|---|---|---|
| Wave 3 positives (72) | 67 served correct, 5 false refusals | **72 served correct**, 0 false refusals |
| Wave 3 negatives (72) | 72 refused, 62 exact reason | **72 refused, 65 exact reason** |
| wrong-served (144) | 0 | **0** |
| locked development (96) | 96/96 | **96/96** |
| reviewer probes (203) | 0 served negatives | **0 served negatives** |
| measurement probe (S.ABCD) | 10/10 + 4/4 | **10/10 served correct, 4/4 refused** (`measurement-probe.json`, run at `79bbc053`; the tool records no head itself) |

> [!WARNING]
> Wave 3 is **development-contaminated** (W3-F1 and this run fixed against it). These are regression numbers, not
> held-out generalization.

## 9. False refusal / correct refusal

- False refusals on Wave 3 positives: 5 → **0**.
- Correct refusals with a reason the frozen taxonomy disagrees with: 10 → **7** (all still refused):
  N03, N25, N58, N72 (`SOURCE_OBJECT_MISMATCH` before the expected contradiction/degeneracy layer), N38
  (`UNSUPPORTED_CAPABILITY`), N47 (`UNGROUNDED_VALUE`, known lexical gap, recorded W4), N53
  (`PARALLEL_NO_INTERSECTION` is absent from the frozen taxonomy → `UNMAPPED`, an `EVALUATION_ORACLE_ISSUE`).

## 10. Failure attribution (every gold-replay failure at `fba8b7a7`)

| case | before | attribution | root cause |
|---|---|---|---|
| W3-B01 | FALSE_REFUSAL `CONDITIONAL_CLAUSE` | `SOURCE_GATE_FAILURE` | `_DIEU_KIEN_SAU` lacked the "khi **bị** cắt" exception `_DIEU_KIEN` has; then "vuông tại **đỉnh** E" and "thỏa mãn **hệ thức**" were unread |
| W3-B34 | FALSE_REFUSAL `SOURCE_PREMISE_UNREAD` | `SOURCE_GATE_FAILURE` | two-line slice did not read "**khối** lăng trụ **tam giác**"; "hình chiếu … của **đỉnh** B'" opaque |
| W3-B35, B36 | FALSE_REFUSAL `SOURCE_PREMISE_UNREAD` | `SOURCE_GATE_FAILURE` | "**Xét** khối …"; altitude-foot paraphrase "chân đường cao hạ/kẻ từ K' xuống/đến mặt phẳng (KLM) trùng với/là (đỉnh) L" opaque to the sentence reader |
| W3-A06 | FALSE_REFUSAL `ENGINE_EXECUTION_FAILED` (`RADICAL_DOMAIN_OVERFLOW`) | `KERNEL_FAILURE` | input bound `MAX_RADICAND²` refused 1.13·10²⁴ = 60259484250²·310 before trial division could extract its small-prime square part |
| W3-N54, N55 | refused `PREVIEW_RESULT_INVALID` at the adapter | `KERNEL_FAILURE` (certificate gap in `kiem_dinh_cat`) | the route **served** a stated-cut section whose named vertices (M, N, P) missed one vertex of the exact cross-section; only Adapter `/4` validation caught it |
| W3-N02 | refused `SOURCE_OBJECT_MISMATCH` | `EXPECTED_REFUSAL` | now reaches `INCONSISTENT_FACTS` (MN = 8 and 13), the taxonomy's reason |

No `PROVIDER_FAILURE` / `EXTRACTION_FAILURE` attribution is possible: no provider was involved.

## 11. Backend repairs (products `55db50c3` + `57457fc4`)

Review round 1 (`57457fc4`): `_C_CHIEU`'s altitude-foot alternative narrowed to exactly the binder's grammar
(`_chan_duong_cao_dung_nguon`; the extra wordings were already refused, so no result change and no further bump); the
coverage refusal documented as unsupported partial naming; radical bound documented; closed right-angle form reads
"đỉnh".

Each: reproduction (gold payload) → root cause (§10) → failing test (RED, 7 failed) → change → passing test
(`backend/tests/geometry/test_route_d_gold_replay_repairs.py`, 21 tests) → regression (§8, §15).

1. **Clause reader consistency** (`registry._DIEU_KIEN_SAU`): "khi (bị/đã) cắt" is construction wording in both
   readers. Adversarial: "Nếu/Giả sử mặt phẳng (P) …" and a post-clause "khi H trùng S" still `CONDITIONAL`.
2. **Source Gate wording** (registry `/32`): "vuông tại đỉnh X"; "hình chiếu … của (điểm|đỉnh) X"; altitude foot
   "chân đường cao (hạ|kẻ)? từ X (xuống|đến) mặt phẳng (…) (là|trùng với) (điểm|đỉnh)? Y" (exactly the binder's grammar); ratio "thỏa mãn (hệ|đẳng)
   thức"; the two-line slice reads "xét", "khối" and a base-polygon word **that must equal the base's vertex count**.
   Adversarial: every wrong image / wrong apex of the projection refuses; "tứ giác" on a triangular base refuses; a
   wrong ratio refuses.
3. **Stated-cut coverage certificate** (engine `/24`, `chung_chi_phu_dinh`): a `/2` stated-cut section must name
   every vertex of `cross_section(solid, plane)`, else `SECTION_BOUNDARY_INCOMPLETE` in the kernel. Positive control:
   the same problem stating SB, SC, SD is served with vertices {M, N, P, K}.
4. **Exact radicals** (`radical._tach_binh_phuong`): the trial-division input bound moves from `MAX_RADICAND²` to
   `MAX_RADICAND³`; the domain ceiling and every refusal of a non-certifiable remainder are unchanged (10²⁴ + 7,
   10³⁶ + 1, 4·(10¹² + 39) still refuse).

**Known limitation of repair 3 (review R-5).** Partial naming that is legitimate (e.g. "(P) qua A ⊥ SC cắt SC tại N. Tính diện tích thiết diện") is refused `SECTION_BOUNDARY_INCOMPLETE`, which the learner surface maps to the "dữ kiện mâu thuẫn / suy biến" message, while the same problem with no stated cut is served. Nothing it refuses was served before (the adapter rejected it as an invalid result). Proper fix: derive the unstated vertices (`derived_fresh`, engine-certified) or fall back to the engine-derived section; logged in `docs/OPEN_ISSUES.md` as `ISSUE-ARCH-PARTIAL-STATED-CUT-NAMING`.

Bump rule (MIGRATION_CHECKLIST M-2) applied: registry `/31 → /32`, engine `/23 → /24`, declared in
`export_hybrid_preview_fixtures.IDENTITY_DELTAS`; 41 preview fixtures verify through the delta. `CACHE_VERSION`
unchanged (LLM_ONLY bytes untouched; Route D rows keyed by the bumped versions).

## 12. Planner composition performance (offline, candidate `79bbc053`)

`planner-composition-c18-probe.json` (C18 corpus, independent oracle `composition_oracle.py`):

| metric | value |
|---|---|
| cases | 504 (480 reachable, 24 degenerate) |
| served correct / wrong-served | 480 / 0 |
| degenerate refused | 24/24 (`DEGENERATE_POINTS`) |
| oracle `COMPOSITION_NECESSARY`, served correct | 208 |
| of which necessary for the GOAL and served by a ≥ 2-function chain with every fresh point consumed | 202 (6 prism cases ask a distance the same for every point of the triangle's plane ⇒ `COMPOSED_NOT_NECESSARY`, as in C18 review MINOR-3) |
| chains | `orthogonal_projection_line`×2 → `intersect_line_line` (91); + `midpoint`, `translate_point` (111) |
| search | depth ≤ 4, ≤ 25 explored states; route time median 42.3 ms, max 129.3 ms (deterministic backend only; measured while Full T3 ran on the same machine — 34.4 / 92.4 ms at `d5c4098b` on a quieter machine) |

Identical classification to C18 (`composition-probe-r2.json`): the repairs changed no plan.

The C11 matrix tool (`planner_recomposition_probe.py`) aborts on its own stale expectation
(`C1a … SOURCE_EXPLICIT_SEQUENCE ≠ DISCOVERED_FUNCTION_COMPOSITION`) **at `adf4a113` too** (verified in a throw-away
detached worktree, removed): its labels predate the C16/C18 provenance relabel. `EVALUATION_ORACLE_ISSUE`, not a
regression; its locked test (`test_planner_recomposition_oracle.py`) runs in Full T3.

## 13. Registered decomposition vs genuine discovery

All 480 served plans: planner provenance `REGISTERED_DECOMPOSITION`, C15 rule `REGISTERED_DECOMPOSITION`, 0
`search_generated` steps. Case **A** (a plan found from existing functions with no decomposition registered for that
goal) is **not** demonstrated: the loci come from the declared definitions (`DINH_NGHIA_DIEM`). No decomposition was
added in this run. **`GENUINE_DISCOVERY_NOT_ESTABLISHED`** (unchanged; `composition-c18.md` §10 states what would be
needed). This does not block serving the supported scope.

## 14. H-1 independent evaluation — `NOT_MEASURED`

Missing input, the only one: **a 60-problem corpus written by an independent author named by the Owner**
(`heldout-authoring/README.md`; `AUTHORING_INDEPENDENCE = NOT_ESTABLISHED`, 0 cases written). No corpus was authored
here: an agent of this repository may not author it. Live H-1 also needs §3 cleared and a separate Owner GO (outside
the K-1/S-2/R-1 delegation).

## 15. Regression results

- Targeted (new + version pins + preview fixtures + radicals + product integration + Route D cache/rollback): 269
  passed; the only failure was the expected pending-freeze tree-hash pin, green after the freeze.
- Gold replay / locked 96 / probes 203: §8. Composition: §12.
- **Full T3** attempt 1 at `d5c4098b`: `FULL_PRODUCT_GATE_FAIL` — 16 669 passed, **1 failed**
  (`test_C2b_candidate_hien_tai_phai_duoc_KHAI`: this run's `candidate_divergence.json` spelled the key
  `so_lieu_lượt_đo_cuối` without diacritics); vitest 1 502/1 502, build, demo 5/5, crash 6/6 PASS. Fixed in `10ea9acd`
  (docs only).
- **Full T3** attempt 2 at `79bbc053` on a clean detached worktree (`hm-t3-79bbc053`, pre/post `freeze_evaluation_candidate.py --verify` MATCH, `ALLOW_LIVE_AI=0`, `0` provider calls): **`FULL_PRODUCT_GATE_PASS`** (`exit 0`, `630.2` s total; `full-t3-79bbc053.json`, local log SHA-256 `79af887e…`) — pytest `16 673` passed, `0` failed, `7` skipped, `2` deselected, `15` xfailed (`600.07` s); vitest `85` files / `1 502` passed; `npm run build` PASS; thesis demo replay `5/5` PASS; demo crash surface `6/6` (`0` thrown as 500) PASS. (An initial PowerShell `*>` pipe redirection on `hm-t3-79bbc053` stalled at 7 % in `test_completion_runner_repair.py` on Windows pipe inheritance and was re-run with `cmd /c "... > ... 2>&1"` disk-file redirection on the same clean worktree; the worktree and its `node_modules` junction were then removed cleanly.)
- Frontend: not modified; its suites run unchanged inside Full T3 (API compatibility only).

## 16. Legacy LLM_ONLY dependency inventory (`legacy-dependency-inventory.json`)

Static import graph over `backend/app` (96 classified modules out of 101 `.py` files — empty package markers skipped; function-level imports included — over-approximation):

| class | modules | lines | content |
|---|---|---|---|
| `LEGACY_ONLY` | 13 | 6 484 | compiler C (`geometry_compiler/*`, 6 modules), `semantic_program.route`, `analyze_contract`, `grammar_card`, `learner_surface`, `section_provenance`, `visual_obligations`, `simulation.error_codes` |
| `HYBRID_REQUIRED` | 6 | 2 466 | `hybrid_offline`, `adapter4_route`, `typed_fact_next_extraction`, `ingestion.input`/`image`/`image_extraction` |
| `SHARED_COMPONENT` | 74 | 49 012 | 62 solver modules both routes load (geometry kernel, `geometry_functions/*`, the semantic-program interpreter/scene3d/envelope compiler Adapter `/4` reuses, `gemini.py`, `function_calling.py`) + 12 route-independent shell modules (`main`, accounts, persistence, `runtime_identity`, `route_trace`) |
| `UNCERTAIN_DEPENDENCY` | 3 | 3 711 | `ai.adapter3_simulation` (tests only), `simulation.product_capability`, `semantic_program.purpose_analysis` |

Key couplings found:
- `hybrid_offline` imports `RoutePolicy` and `route_policy_snapshot` from **`app.ai.pipeline`** (the LLM_ONLY
  orchestrator): `pipeline.py` cannot be deleted until those move to a route-neutral module.
- `app.main` imports `simulation.error_codes` and `pipeline.run_pipeline`; `runtime_identity` imports
  `analyze_contract` / `grammar_card` (identity reporting) — API-level consumers to migrate first.
- Adapter `/4` reuses `semantic_program.pipeline_adapter`, `interpreter`, `scene3d`: most of `semantic_program/` is
  **shared**, not legacy.

## 17. Cutover readiness

| condition | status |
|---|---|
| real extraction quality acceptable | **NOT_MEASURED** (§3) |
| no unresolved serious wrong-served in scope | offline: 0 wrong-served on 144 + 96 + 203 + 504 + 14; live: NOT_MEASURED |
| refusal / clarification correct | offline: 72/72 negatives refused; 7 reason disagreements (§9) |
| planner coverage | supported scope served offline; genuine discovery not established (not required) |
| exact kernel with oracles | yes (independent oracles, §8, §12) |
| API contract stable | Adapter `/4`, TypedFactNext `/2` unchanged |
| runtime errors typed | yes (product-integration receipts; no fallback to LLM_ONLY) |
| rollback | yes (`HYBRID_ROUTE_MODE=off`, D-12) |
| reliable live results | **NO** |
| Owner approval | **NO** |

**`HYBRID_CUTOVER_BLOCKED`.** Gates still open: D-04 (new independent held-out), D-11 (paired live), D-13
(`NO-GO`), GATE-16 (tokens/latency). `DEFAULT_MODE` and `HYBRID_ROUTE_MODE` defaults were not changed.

**Proposed thresholds (proposal only, not an Owner decision)** for the live paired GO, risk-ordered:
- wrong-served on expected-serve: **0** allowed in K-1/S-2/R-1 and H-1 (a wrong figure is the costliest error);
- expected-refuse served: **0**;
- Hybrid served-correct on H-1 expected-serve ≥ LLM_ONLY served-correct on the same items, with the paired difference
  reported with a 95 % CI (H-1 n = 45 serve / 15 refuse is small: decide on the point estimate only if the CI excludes
  a loss);
- provider/infrastructure failures excluded from capability scores and reported separately; Hybrid p50 end-to-end
  latency ≤ LLM_ONLY p50 on the same items (no p95 claim at this n).

## 18. Proposed legacy removal plan (after cutover GO only; nothing removed now)

Order chosen so no step breaks an importer of the next:

1. Move `RoutePolicy` / `route_policy_snapshot` (and `HYBRID_PREVIEW_TOKEN_MIN_LENGTH`) from `ai/pipeline.py` to a
   route-neutral module; re-point `main`, `hybrid_offline`, `runtime_identity`.
2. Switch `/api/analyze` default to Hybrid (Owner GO), keep `HYBRID_ROUTE_MODE=off` as the rollback for one release.
3. Retire compiler C (`geometry_compiler/*`, 6 modules, 2 939 lines; opt-in, disabled; parity corpus never built) and its
   7 diagnostics scripts.
4. Retire the LLM_ONLY synthesis chain: `pipeline.run_pipeline` + `semantic_program.route`, `analyze_contract`,
   `grammar_card`, `learner_surface`, `section_provenance`, `visual_obligations`; migrate `runtime_identity`'s use of
   `analyze_contract`/`grammar_card`; replace `error_codes` consumers in `main`.
5. Keep every `SHARED_COMPONENT` (kernel, interpreter, scene3d, envelope compiler) — Adapter `/4` depends on them.
6. Decide `UNCERTAIN_DEPENDENCY` one by one (`adapter3_simulation`: curved parity is on `/4` now; retire with its 10
   test modules after a parity check).
7. LLM_ONLY cache rows: bump `CACHE_VERSION` at step 2.

**`LEGACY_REMOVAL_BLOCKED`** until §17 clears.

## 19. Remaining blockers

1. `PAID_PROJECT_NOT_VERIFIED` (Owner, §3) → blocks K-1/S-2/R-1 live, §4–7, D-11, GATE-16.
2. H-1 independent author (Owner, §14) → blocks D-04.
3. Owner cutover GO (D-13) and merge/push GO.
4. Genuine discovery: not established (not a release blocker).

## 20. Next release decision

**No release change.** The candidate `79bbc053` (product `57457fc4`) is offline-verified and ready for the live
pilots the moment §3 is cleared; production stays `LLM_ONLY` with Hybrid opt-in. Next exact action: the Owner clears
`PAID_PROJECT_NOT_VERIFIED` by either option in §3; the delegated runner then measures K-1 → S-2 → R-1 on this
candidate and `LIVE_GEMINI_EVALUATION_REPORT.md` is written from those receipts.
