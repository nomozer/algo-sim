# report.md — `hybrid-v2-adapter4-plane-section-certificate`

**Task:** `HYBRID_V2_ADAPTER4_PLANE_ONLY_SECTION_CERTIFICATE` (`OWNER GO — HYBRID V2 ADAPTER4 PLANE-ONLY SECTION CERTIFICATE`, 2026-10-27).

**Marks:** `AUTHORED_DEVELOPMENT_NOT_HOLDOUT` · `INDEPENDENT_CODE_REVIEW` · `INDEPENDENT_HOLDOUT_NOT_EXECUTED` · `LIVE_NL_E2E_NOT_MEASURED` · `BROWSER_EVIDENCE_NOT_MEASURED`.

**Where:** branch `research/hybrid-v2-adapter4-plane-section-certificate` from verified `main` `a3ee14a707f35dddd70a52f551d23beb16476c41`, worktree `.superpowers/worktrees/adapter4-plane-section-certificate`.
No merge, no push, no worktree cleanup. `0` live provider calls (`ALLOW_LIVE_AI = 0`). `DEFAULT_MODE = LLM_ONLY`. Hybrid remains opt-in only. Registry `/17`, Planner `/16`, Engine `/14`, Adapter `/4`, and `CACHE_VERSION = 130` (`NO_BUMP`) unchanged.

## 1. Baseline and Architectural Gap (`ADAPTER_INTEGRATION_GAP`)

- **Baseline before wave:** `main` = `origin/main` = `a3ee14a707f35dddd70a52f551d23beb16476c41` (`registry /17`, `planner /16`, `engine /14`, `Adapter /4`, `CACHE_VERSION = 130`).
- **Root cause (`baseline-audit.md`):**
  1. For plane-only derived sections (`MAT_VUONG_DUONG`, `MAT_SONG_SONG`, `MAT_HAI_DUONG`) where the source problem defines the cutting plane by a point and geometric relation without naming edge-cut vertices (`cut_edges = []`), `run_typed_fact_next_v2_route` (`adapter4_route.py`) succeeded (`status = "SERVED"`) with `td_<sid>` (`type == "section"`) and `kq_<qid>` (`section_area`) computed and verified in exact `Fraction` arithmetic.
  2. However, `adapter4_route._build_section_certificates` constructed `route_d["sections"]` exclusively from `DINH_CAT_CANH` edge-cut certificates (`result.planner["auxiliary"]` with `rule == "section(plane by edge cuts)"`). When no `DINH_CAT_CANH` certificates existed, `route_d["sections"]` was `[]`.
  3. `build_adapter4_response` then called `_validate_sections(route_d["sections"], scene3d, result.final_memory)`, which saw `td_<sid>` in `scene3d["objects"]` with `len(sections) == 0 != 1`, and failed closed with `PREVIEW_RESULT_INVALID:section_count_mismatch`.
  4. Additionally, in `function_route._an_dinh_thiet_dien_phu`, when a plane-construction `translate_point` auxiliary (`H1`) happened to coincide with a section boundary vertex (`point:on:...`), `H1` was matched by coordinate equality and leaked into the learner-facing section name (`Thiết diện (MH1)` instead of `Thiết diện (M)`).

## 2. Category A vs. Category B Architecture (`architecture-decision.md`)

To preserve strict source grounding and deterministic verification without fabricating `DINH_CAT_CANH` certificates for unstated vertices:
- **Category A (`DINH_CAT_CANH` + `D6` closure):** Source-stated or planner-declared edge-cut vertices (`section_vertex_from_cut` / `dinh_cat_canh`). Validated by `_validate_category_a_section`.
- **Category B (`plane-section-certificate/1`):** Engine-derived plane-section certificate (`certificate_category = "ENGINE_DERIVED_SECTION"`, `certificate_version = "plane-section-certificate/1"`, `producer = "engine.kiem_chung_chi_thiet_dien"`, `rule = "engine_derived_plane_section"`).
  - Emitted by `_Dung.kiem_chung_chi_thiet_dien` (`engine.py`) onto `KetQuaTuyen.section_certificates` for every verified plane-section (`intersect_plane_solid` / `cat_khoi_boi_mat`).
  - Consumed by `adapter4_route._build_section_certificates` when `DINH_CAT_CANH` certificates are absent, and validated in exact `Fraction` arithmetic by `_validate_engine_derived_section`.
  - Unstated boundary vertices carry `stated: False`, `label: None`, and `provenance: "ENGINE_DERIVED_EDGE_CUT"`; only a source-named `through_point` coinciding with a solid vertex carries `stated: True`, `label: through_point`, and `provenance: "THROUGH_POINT_REUSE"`.
  - Mixing Category A and Category B on the same section is rejected fail-closed (`SECTION_CATEGORY_MIXED`).

## 3. RED Baseline (`1070134e`) vs. GREEN After (`f54c3561` / `0be084d9`)

Evaluated by [`tools/evaluate_adapter4.py`](tools/evaluate_adapter4.py) on the 36-case development & tamper corpus ([`inputs/development.json`](inputs/development.json), 18 positive + 18 negative/tamper) against the independent first-principles Euclidean `Fraction` oracle ([`tools/oracle_adapter4.py`](tools/oracle_adapter4.py), [`inputs/oracle.json`](inputs/oracle.json)):

| Metric | RED Baseline (`a3ee14a7`, [`results/red-before.json`](results/red-before.json)) | GREEN After (`f54c3561`, [`results/green-after.json`](results/green-after.json)) |
|---|---|---|
| Total cases passed | `19/36` | **`36/36`** |
| Positive cases (`P01..P18`: `MAT_VUONG_DUONG`, `MAT_SONG_SONG`, `MAT_HAI_DUONG`, simulation-only, area-asked, Category A control `P18`) | `1/18` (`P18` only; `P01..P17` failed with `PREVIEW_RESULT_INVALID`) | **`18/18` (`100%` exact oracle agreement on `area_squared`, vertex count, coordinate set, plane membership, edge $t \in [0, 1]$, and learner label hygiene)** |
| Negative & Tamper cases (`N01..N18`: source gate refusals, underdetermined solids, degenerate/face planes, and 10 certificate tamper vectors `N09..N18`) | `18/18` | **`18/18` (`100%` refused with registered code, `envelope.ok == False`, `scene3d is None`)** |
| Wrong-served cases | `0` | **`0`** |
| Live provider calls | `0` | **`0`** |

## 4. Test Tiers, Candidate Freeze, and Authoritative Full T3

| Gate | Result |
|---|---|
| T0 `node frontend/scripts/impact.mjs --base a3ee14a7 --dry` | `IMPACT_GATE` (`18` changed files → `src/code-index-sync.test.ts` + `PYTEST`) |
| T1 targeted & geometry/semantic suites | `520 passed` (`test_adapter4_plane_section_certificate.py` `39/39`, `test_prism_perpendicular_section_planning.py` `17/17`, `test_adapter4_response.py`, `test_hybrid_contract_v2.py`, `test_section_display_identity.py`, `test_solid_kind_source_binding.py`, `test_hybrid_preview_contract.py`, `test_thesis_acceptance_matrix.py`) + `41 passed` (`test_hybrid_preview_fixtures.py`) |
| T2 `npx vitest run` (`frontend/`) | `83` test files, `1,417 passed` |
| Freeze (`0be084d9`) | Product `f54c3561b09153021bba0b35a5a9ab78a82546b3`, `118` files, `tree_hash = ae6360b1d20beb96b87bad4f335b74b3a61e7483d06214aa2192f17fe6f1c70a` |
| Divergence (`0be084d9`) | [`candidate_divergence.json`](candidate_divergence.json) (`corrects` `hybrid-v2-source-kind-consistency/candidate_divergence.json`, `CACHE_VERSION = 130` `NO_BUMP`) |
| **Full T3** (clean detached checkout `0be084d9` in `premerge-red`) | **`FULL_PRODUCT_GATE_PASS`**: `12,421 passed, 1 skipped, 2 deselected, 15 xfailed, 1 warning`; frontend `83 files / 1,417 passed`; build PASS; demo `5/5` + `1/1`; crash `6/6`; post-T3 freeze `MATCH` (`118 file, ae6360b1d20beb96…`, [`full-t3/receipt.json`](full-t3/receipt.json)) |

## 5. Independent Review (`review.md`)

Audited by independent read-only subagent `c4924ed9-a99b-42af-8a33-f47c2865b248` ([`review.md`](review.md)):
- **`BLOCKER`**: `0`.
- **`MAJOR`**: `0`.
- **`MINOR`**: `0`.
- **`NIT`**: `2` (both resolved in `f54c3561`: `NIT-1` `result is not None` check and `plane_relation` sub-field binding in `_validate_engine_derived_section`; `NIT-2` illustrative key in `architecture-decision.md`).
- **Verdict**: **`INDEPENDENT_REVIEW_PASS`**.

## 6. Honesty Boundaries & Status

- **Evaluation scope**: `AUTHORED_DEVELOPMENT_NOT_HOLDOUT` · `INDEPENDENT_HOLDOUT_NOT_EXECUTED` · `LIVE_NL_E2E_NOT_MEASURED` · `BROWSER_EVIDENCE_NOT_MEASURED`. `0` live provider calls.
- **Status**: `READY_FOR_OWNER_REVIEW` — see [`handoff.md`](handoff.md).
