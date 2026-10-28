# Report — Hybrid V2 W3-F1 Cross-Sentence Plane Grounding (`HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`)

## 1. Executive Summary & Identity

- **Task Code:** `HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`
- **Run Slug:** `hybrid-v2-w3-f1-cross-sentence-plane-grounding`
- **Branch:** `research/hybrid-v2-w3-f1-cross-sentence-plane-grounding`
- **Evidence Classification:** `PRODUCT_REPAIR_WITH_POST_FEEDBACK_DEVELOPMENT_REGRESSION` (NOT an independent blind holdout)
- **Authoritative Baseline (`main = origin/main = remote`):** `e137623c4f674135a8d7884b78614c132eb78085`
- **Parent Product Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8` (freeze `1170ca163529dd40b57f4058826db92a6433359546aa2ad712f38a538c10d`)
- **Preserved Historical Holdout Wave 3 Worktree:** `.superpowers/worktrees/independent-section-holdout-wave3` (`0943f0ee6bd2a2b297827e39fa7c07054d716ea9`, untouched)
- **Product Repair Commit:** `a609c4871a75426db52eb8b7a7be8ba3460fcf8c` (with initial W3-F1 implementation at `c15eebe44eea5518e060699f0f7dda0fac7b9eec` and test/artifact commit `c8222e7d2a57a5cf1cb08ec225b76b0fa8faffc6`)
- **Frozen Full T3 Candidate:** `b02b2c422e4049dc6ff0a94996f335424e7b02b9`
- **Measured Product System (`118` files):** `918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72` (`MATCH`)
- **Versions:**
  - `REGISTRY_VERSION`: `geometry-functions/19` $\rightarrow$ `geometry-functions/20`
  - `PLANNER_VERSION`: `geometry-fact-planner/17` $\rightarrow$ `geometry-fact-planner/18`
  - `ENGINE_VERSION`: `geometry-function-engine/14` (unchanged)
  - `ADAPTER_V4_VERSION`: `hybrid-simulation-adapter/4` (unchanged)
  - `PLANE_SECTION_CERTIFICATE_VERSION`: `plane-section-certificate/1` (unchanged)
  - `CACHE_VERSION`: `130` (unchanged)
  - `DEFAULT_MODE`: `LLM_ONLY` (`semantic_route_mode() == "off"`)
  - `ALLOW_LIVE_AI`: `0` (`0` live provider requests)

---

## 2. Root-Cause Diagnosis of `W3-F1: SECTION_AND_AREA_COMPOUND_QUESTION_GROUNDING`

In Independent Vietnamese Geometry Holdout Wave 3 (`0943f0ee6bd2a2b297827e39fa7c07054d716ea9`), all `24/24` positive cases with `question_type = "section_and_area"` (`18` Category B `P-B` + `6` Category A `P-A`) were refused with `SOURCE_OBJECT_MISMATCH`.

Audit of the `24` cases revealed four interacting mechanisms across the TypedFactNext v2 bridge, Planner, and Source Gate:

1. **Cross-Sentence Plane Definition Split:**
   - In compound `section_and_area` problems, the cutting plane `(P)` / `(Q)` / `(α)` / `(β)` / `(γ)` / `(Ω)` is defined in a standalone declarative sentence (e.g., *"Mặt phẳng (P) đi qua H đồng thời vuông góc với cạnh SF."* or *"Từ điểm I, thiết lập mặt phẳng (P) song song với cả hai đường thẳng EG và SH, cắt các cạnh SE, SF, SG lần lượt tại M, N, K."*) while the question is in a subsequent sentence (e.g., *"Hãy xác định thiết diện của hình chóp S.EFG khi cắt bởi mặt phẳng (P) và tính diện tích thiết diện đó."*).
   - When `math_goals[0]` (and/or `simulation_goals`) quotes only the question sentence, the `area_polygon` call only receives the question quote unless the unique plane-definition sentence is linked via Grounded Cross-Sentence Plane Reference Resolution.
2. **Compound Request Tail After Stated Cut Clause (`_het_dinh_nghia`):**
   - When `derived_sections[0].quote` spans both the plane definition sentence (with or without a Category A cut clause `cắt ... tại ...`) and the compound request sentence (`Hãy xác định thiết diện ... và tính diện tích thiết diện đó`), `_het_dinh_nghia` previously rejected the compound request tail after a stated cut clause or did not allow the trailing `và tính diện tích thiết diện đó` clause.
3. **Bounded Vietnamese Phrasing Gaps in Plane Definition & Section Reference Grammar:**
   - `_QUA_SONG_SONG`, `_QUA_VUONG_DUONG`, `_QUA_HAI_DUONG`, and `_DIEM_TRUOC` did not accept the relation connector `đồng thời` (`đi qua H đồng thời vuông góc với ...`), the two-line quantifier `cả hai` (`song song với cả hai đường thẳng ...`), point-first two-line definitions (`_DIEM_TRUOC_HAI_DUONG`, including `Từ điểm I, thiết lập mặt phẳng (P) ...`), or plane-first section references (`thiết diện tạo bởi mặt phẳng (P) với hình lăng trụ ...`).
4. **Declared Plane Name Identity Propagation:**
   - `_mat_fact` in `typed_fact_next_bridge.py` and `_mat_qua_diem` / `_mat_vuong_duong` in `planner.py` previously propagated `plane_name` only for `parallel_two_lines` (`MAT_HAI_DUONG`), leaving `MAT_SONG_SONG` and `MAT_VUONG_DUONG` without `plane_name` identity enforcement in `mat_song_song_dung_nguon`.

---

## 3. Product Repair Design & Scope Guard

Only `3` product files were modified (`0` changes to `radical.py`, `engine.py`, `adapter4_route.py`, or frontend):

1. **[`backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`](file:///d:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f1-cross-sentence-plane-grounding/backend/app/simulation/geometry_functions/typed_fact_next_bridge.py)**:
   - Propagates `plane_name` onto all derived plane facts (`parallel`, `perpendicular`, `parallel_two_lines`) in `_mat_fact`, rejecting invalid plane symbols that violate `^(?:[A-Z][0-9]*'?|[α-ω]'?)$` with `SOURCE_OBJECT_MISMATCH`.
   - Adds `_v2_plane_def_quotes(sec, problem_text)` so that when a `typed-fact-next/2` section references a named plane `(P)` whose definition is in a unique separate declarative sentence in `problem_text`, that sentence span is attached ahead of the section quotes without mutating quote order or guessing across multiple definitions.
2. **[`backend/app/simulation/geometry_functions/planner.py`](file:///d:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f1-cross-sentence-plane-grounding/backend/app/simulation/geometry_functions/planner.py)** (`PLANNER_VERSION = "geometry-fact-planner/18"`):
   - Propagates `plane_name` into `k.derived_planes` keys and `d["plane_name"]` / `dd["plane_name"]` in `_mat_qua_diem` and `_mat_vuong_duong`.
   - Updates `_cau_hoi` so unasked area goals (where `"diện tích"` is absent from the question quote) fail closed with `NOT_ASKED_IN_SOURCE` and mismatched area targets fail closed with `SOURCE_OBJECT_MISMATCH`.
3. **[`backend/app/simulation/geometry_functions/registry.py`](file:///d:/Documents/projects/algo-sim/.superpowers/worktrees/w3-f1-cross-sentence-plane-grounding/backend/app/simulation/geometry_functions/registry.py)** (`REGISTRY_VERSION = "geometry-functions/20"`):
   - Implements **Grounded Cross-Sentence Plane Reference Resolution** in `mat_song_song_dung_nguon`: when a section or area call quotes a question sentence referencing `(P)` (or `ten_khai`), it resolves `(P)` against `de` if and only if there is a **unique** plane definition sentence in `de` matching `(P)`, `p`, and `khop(m)`, passing `vai_tro_ok` (not negated, not conditional, not a goal clause) and `_het_dinh_nghia`, and with zero conflicting definitions across `_ALL_PLANE_DEF_MAU`.
   - Extends `_het_dinh_nghia`, `_td_mat_truoc_khoi`, `_cum_goi_khoi`, `_QUA_SONG_SONG`, `_QUA_VUONG_DUONG`, `_QUA_HAI_DUONG`, `_DIEM_TRUOC_HAI_DUONG`, and `_kiem_du_kien_cau_hoi` to support `đồng thời`, `cả hai`, `thiết diện tạo bởi mặt phẳng (P) với <khối>`, and compound `section_and_area` tails while preserving all fail-closed guards.

---

## 4. RED $\rightarrow$ GREEN Development Evaluation (`92` Cases)

Artifact: `results/red-before.json` (`1170ca16…`) $\rightarrow$ `results/green-after.json` (`918d3404…`)

| Development Slice | Total | RED (`1170ca16…`) | GREEN (`918d3404…`) | `SOURCE_OBJECT_MISMATCH` (RED $\rightarrow$ GREEN) | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|
| **Slice A1 — Historical `W3-F1` Pure (`historical_w3_f1_pure_9`)** | `9` (`6` `P-B`, `3` `P-A`) | `0/9` (`0.0%`) | **`9/9` (`100.0%`)** | `9` $\rightarrow$ **`0`** | `0` |
| **Slice A2 — Historical `W3-F1` with Out-of-Scope Secondary Defect (`W3-F2/F3/F4`)** | `15` (`12` `P-B`, `3` `P-A`) | `0/15` (`0.0%`) | `0/15` (all `15` fail closed on `W3-F2/F3/F4`: `7` `PREDICATE_NOT_IN_QUOTE`, `6` `SOURCE_PREMISE_UNREAD`, `2` `UNGROUNDED_VALUE`) | `15` $\rightarrow$ **`0`** | `0` |
| **Slice B — Isolated `W3-F1` (`w3_f1_isolated_24`, non-plane premise normalized)** | `24` (`18` `P-B`, `6` `P-A`) | `0/24` (`0.0%`) | **`24/24` (`100.0%`)** (`18/18` `P-B`, `6/6` `P-A`) | `24` $\rightarrow$ **`0`** | `0` |
| **Slice C — Newly Authored Cross-Sentence Positive (`authored_cross_sentence_positive_24`)** | `24` (`19` `P-B`, `5` `P-A`) | `0/24` (`0.0%`) | **`24/24` (`100.0%`)** (`19/19` `P-B`, `5/5` `P-A`) | `24` $\rightarrow$ **`0`** | `0` |
| **Slice D — Mandatory Adversarial / Tamper (`mandatory_negative_tamper_20`)** | `20` (`20` `N`) | `20/20` refused (`18/20` exact code) | **`20/20` refused (`20/20` category, `20/20` exact code)** | — | `0` |

- **Exact Oracle Agreement on Served Positive Cases:** `9/9` on `historical_w3_f1_pure_9`, `24/24` on `w3_f1_isolated_24`, `24/24` on `authored_cross_sentence_positive_24`.
- **Machine ID / Auxiliary Identity Leaks:** `0` (`machine_id_leak_cases = []`, `source_identity_leak_cases = []`).

---

## 5. Wave 3 Post-Feedback Development Regression (`144` Locked Cases)

> **Classification Notice:** This replay is strictly classified as `POST_FEEDBACK_DEVELOPMENT_REGRESSION` (`not_an_independent_blind_holdout = true`). The original Holdout Wave 3 evidence in `.superpowers/worktrees/independent-section-holdout-wave3` (`0943f0ee6bd2a2b297827e39fa7c07054d716ea9`) remains frozen and untouched.

Artifact: `results/wave3-post-feedback-regression.json`

| Metric | Historical Blind Holdout Wave 3 (`1170ca16…`) | Post-Feedback Regression After `W3-F1` (`918d3404…`) | Delta |
|---|---:|---:|---:|
| **Positive `SERVED_CORRECT` (`/72`)** | `20/72` (`27.78%`) | **`29/72` (`40.28%`)** | **`+9`** |
| — Category B (`P-B`, `/54`) | `12/54` (`22.22%`) | **`18/54` (`33.33%`)** | **`+6`** |
| — Category A (`P-A`, `/18`) | `8/18` (`44.44%`) | **`11/18` (`61.11%`)** | **`+3`** |
| — `section_only` (`/24`) | `10/24` (`41.67%`) | `10/24` (`41.67%`) | `0` |
| — `area_only` (`/24`) | `10/24` (`41.67%`) | `10/24` (`41.67%`) | `0` |
| — `section_and_area` (`/24`) | `0/24` (`0.00%`) | **`9/24` (`37.50%`)** | **`+9`** |
| **Remaining `W3-F1` `SOURCE_OBJECT_MISMATCH` (`/24`)** | `24/24` | **`0/24`** | **`-24`** |
| **Negative Refusal Rate (`/72`)** | `72/72` (`100.00%`) | **`72/72` (`100.00%`)** | `0` |
| **Negative Correct Refusal Category (`/72`)** | `60/72` (`83.33%`) | **`62/72` (`86.11%`)** | **`+2`** |
| **Overall `WRONG_SERVED` (`/144`)** | `0/144` (`0.00%`) | **`0/144` (`0.00%`)** | `0` |
| **Learner-Facing Identity Leaks (`/144`)** | `0/144` | **`0/144`** | `0` |

- **9 Pure `W3-F1` Cases Transitioning `FALSE_REFUSAL (SOURCE_OBJECT_MISMATCH)` $\rightarrow$ `SERVED_CORRECT`:**
  - Category B (`6` cases): `W3-B03`, `W3-B09`, `W3-B15`, `W3-B39`, `W3-B45`, `W3-B51`
  - Category A (`3` cases): `W3-A03`, `W3-A09`, `W3-A15`
- **15 `W3-F1` Cases Exposing Out-of-Scope Secondary Premise Defects (`W3-F2`, `W3-F3`, `W3-F4`) After `W3-F1` Unblocking:**
  - `W3-F2` (`PREDICATE_NOT_IN_QUOTE`, `7` cases): `W3-B18`, `W3-B21`, `W3-B24`, `W3-B30`, `W3-B33`, `W3-B36`, `W3-A12`
  - `W3-F3` (`SOURCE_PREMISE_UNREAD`, `6` cases): `W3-B06`, `W3-B12`, `W3-B42`, `W3-B48`, `W3-A06`, `W3-A18`
  - `W3-F4` (`UNGROUNDED_VALUE`, `2` cases): `W3-B27`, `W3-B54`
- **2 Negative Cases Improving from `REFUSED_REASON_DISAGREEMENT` $\rightarrow$ `REFUSED_CORRECT_REASON`:**
  - `W3-N58`, `W3-N60` (`SOURCE_PREMISE_UNREAD` $\rightarrow$ `SOURCE_OBJECT_MISMATCH`, matching `SOURCE_GROUNDING`).

---

## 6. Verification Tiers (T0, T1, T2, Full T3) & Freeze Integrity

1. **T0 (`verification/scope-and-evidence.json`, `verification/cache-and-fixtures.json`, `verification/impact-plan.json`):**
   - `frontend/scripts/impact.mjs --dry`: `PASS` (`exit_code = 0`)
   - `backend/scripts/check_publication_safety.py --range e137623c..b02b2c42`: `PASS` (`exit_code = 0`)
   - Product scope guard: only `planner.py`, `registry.py`, `typed_fact_next_bridge.py` modified (`0` forbidden layers changed)
   - `backend/scripts/lock_cache_identity.py --verify`: `MATCH` (`CACHE_VERSION = 130`)
   - `backend/scripts/export_hybrid_preview_fixtures.py --verify`: `41/41` verified, `0` problems
2. **T1 & T2 (`verification/tiers.json`, `verification/t1-t2.log`):**
   - `18` targeted geometry, adapter, bridge, contract, evaluation-candidate, and thesis-acceptance-matrix test suites: **`795 passed, 5 xfailed in 120.86s`** (`0` failed).
3. **Authoritative Full T3 (`verification/full-t3/receipt.json`, `verification/full-t3/full-t3.log`):**
   - Executed on a clean detached worktree at candidate `b02b2c422e4049dc6ff0a94996f335424e7b02b9` (product commit `a609c4871a75426db52eb8b7a7be8ba3460fcf8c`):
     - Backend full pytest: **`12592 passed, 1 skipped, 2 deselected, 15 xfailed, 1 warning in 536.13s`** (`0` failed)
     - Frontend full vitest: **`83 passed (83)` files, `1417 passed (1417)` tests** (`0` failed)
     - Production typecheck + build (`npm run build`): **`PASS` (`5.3s`)**
     - Thesis demo replay (`replay_demo_cases.py`): **`5/5 PASS`, `1/1` reduced chain (`0.8s`)**
     - Demo crash-surface audit (`audit_demo_crash_surface.py`): **`6/6 PASS`, `0` 500s (`0.5s`)**
     - Post-T3 `freeze_evaluation_candidate.py --verify`: **`MATCH` (`118` files, `918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72`)**
     - Verdict: **`FULL_PRODUCT_GATE_PASS`**
