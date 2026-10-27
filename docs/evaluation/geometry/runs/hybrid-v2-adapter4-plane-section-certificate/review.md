# review.md — Independent Review, `hybrid-v2-adapter4-plane-section-certificate`

- **Marks:** `INDEPENDENT_CODE_REVIEW` · `AUTHORED_DEVELOPMENT_NOT_HOLDOUT` · `INDEPENDENT_HOLDOUT_NOT_EXECUTED` · `LIVE_NL_E2E_NOT_MEASURED` · `BROWSER_EVIDENCE_NOT_MEASURED`.
- **Reviewer:** a read-only subagent in an isolated context (conversation `c4924ed9-a99b-42af-8a33-f47c2865b248`). It did not author any of the reviewed code, tests, or evaluation artifacts. It audited the full `a3ee14a7..67069f3c` commit range (`16` changed/created files + surrounding context in `engine.py`, `adapter4_route.py`, `function_route.py`, `planner.py`, and `registry.py`), changed no file, and made `0` live provider calls. Both `NIT` items identified by the reviewer were subsequently resolved in `f54c3561` (frozen at `0be084d9`).

## 1. Deltas Reviewed

| Delta | Content | Verdict |
|---|---|---|
| `a3ee14a7..1070134e` | Pre-registration (`plan.md`, `baseline-audit.md`, `architecture-decision.md`), independent Euclidean section oracle (`tools/oracle_adapter4.py`, `inputs/oracle.json`), 36-case development & tamper corpus (`tools/corpus_adapter4.py`, `inputs/development.json`), evaluator (`tools/evaluate_adapter4.py`), and RED baseline receipt (`results/red-before.json`: `19/36` passed — `1/18` positive, `18/18` negative) | **INDEPENDENT_REVIEW_PASS** |
| `1070134e..05f3bd47` | Category B `plane-section-certificate/1` producer + self-check in `engine.py` (`_Dung.kiem_chung_chi_thiet_dien`, `KetQuaTuyen.section_certificates`), consumer validation in `adapter4_route.py` (`_validate_engine_derived_section`, `build_adapter4_response`), coincident plane-auxiliary label guard in `function_route.py` (`_an_dinh_thiet_dien_phu`), regression & tamper suite (`test_adapter4_plane_section_certificate.py` `39/39`, `test_prism_perpendicular_section_planning.py` `17/17`), and GREEN receipt (`results/green-after.json`: `36/36` passed — `18/18` positive, `18/18` negative/tamper) | **INDEPENDENT_REVIEW_PASS** |
| `05f3bd47..0be084d9` | Adapter `/2` trace compatibility preservation (`engine.py`), non-refusal literal registration (`test_hybrid_preview_contract.py`), `NIT-1` (`adapter4_route.py` `plane_relation` binding + `result is not None`) & `NIT-2` (`architecture-decision.md`), candidate freeze (`0be084d9`, product `f54c3561`, `118` files, `tree_hash = ae6360b1d20beb96b87bad4f335b74b3a61e7483d06214aa2192f17fe6f1c70a`), `candidate_divergence.json` | **INDEPENDENT_REVIEW_PASS** |

## 2. Verification of the 6 Review Dimensions

1. **Mathematical Correctness (`engine.py` & `adapter4_route.py`)**:
   - All coordinates, normals, offsets, edge interpolation parameters $t$, and cyclic polygon areas (`area_squared`) are represented and verified in exact `Fraction` arithmetic ($\mathbb{Q}^3$), with zero floating-point tolerances in the mathematical authority or consumer validation.
   - All 10 mathematical and structural invariants (§4.2) are enforced at both producer (`_Dung.kiem_chung_chi_thiet_dien`) and consumer (`_validate_engine_derived_section`) boundaries:
     1. Solid identity (`solid_object_id`, `vertex_ids`, `vertices`, `faces`) matches both `scene3d` and Engine solid.
     2. Cutting plane (`mp_td_<sid>`) exists in `scene3d`, matches `plane_points` (`depends`), includes `through_point`, matches `final_memory[plane_object_id]` (`normal`, `offset`) with $\vec{n} \neq \vec{0}$, and satisfies $\vec{n} \cdot Q_j = d$ for all $Q_j \in \text{plane\_points}$, and `plane_rule` / `plane_relation` match the verified `planner["auxiliary"]` record.
     3. Exact plane membership ($\vec{n} \cdot P_i = d$) for every section vertex $P_i$.
     4. Solid boundary membership (`SOLID_VERTEX` at $V_{\text{solid\_vertex\_index}}$ or `SOLID_EDGE_INTERSECTION` on a topological edge $(ia, ib)$ of `solid["faces"]`).
     5. Supporting edge & exact rational parameter $t \in [0, 1]$ satisfying $(1 - t) V_{ia} + t V_{ib} = P_i$ with $V_{ia} \neq V_{ib}$ and strict endpoints ($t \in \{0, 1\} \iff \text{SOLID\_VERTEX}$, $0 < t < 1 \iff \text{SOLID\_EDGE\_INTERSECTION}$).
     6. Cyclic coplanar polygon ordering (`len(vertices) >= 3`, distinct coordinates, consecutive vertices share a common face of `solid["faces"]`).
     7. Non-zero area (`_dien_tich_da_giac_3d(pts) == area_squared > 0`) and strict convexity (`_da_giac_loi_chat(pts, normal_vec)`).
     8. Exact agreement with `scene3d` `td_<sid>` (`boundary`, `vertices`, `plane_points`, `solid_object_id`, `plane_object_id` in `depends`) and `formation.steps` (`CONSTRUCT_SECTION` step covers `td_<sid>` and `mp_td_<sid>`).
     9. Exact agreement with `kq_<qid>` (`area_squared` matches `final_memory["kq_<qid>"]["value_squared"]`) whenever `section_area` is asked.
     10. No internal label leakage (`H`, `H1`, `H2`, `H3`, `sec:...:edge:...`, `section:td_...` absent from learner-facing `name`, `label`, `description`, `narration`, and `step_descriptions`).
2. **Contract & Provenance Separation (Category A vs. Category B)**:
   - Category A (`DINH_CAT_CANH` source-grounded cut vertices and `D6` closure) and Category B (`plane-section-certificate/1`, `certificate_category = "ENGINE_DERIVED_SECTION"`, `rule = "engine_derived_plane_section"`, `producer = "engine.kiem_chung_chi_thiet_dien"`) are strictly separated.
   - No `DINH_CAT_CANH` certificate is fabricated for unstated section vertices.
   - When `DINH_CAT_CANH` certificates exist (`co_dinh_cat_nguon = True`), `_validate_sections` enforces Category A validation (`_validate_category_a_section`) and rejects any Category B certificate on that section (`SECTION_CATEGORY_MIXED`).
   - Every unstated Engine-derived vertex has `stated: False`, `label: None`, and `provenance: "ENGINE_DERIVED_EDGE_CUT"`, while only the source-named `through_point` when coinciding with a solid vertex has `stated: True`, `label: through_point`, and `provenance: "THROUGH_POINT_REUSE"`.
3. **Fail-Closed Completeness**:
   - Every invalid or tampered state (missing certificate, empty `route_d["sections"]` with a `section` object in `scene3d`, off-plane vertex, invalid edge parameter $t \notin [0, 1]$, non-edge vertex pair, collinear/zero-area polygon, non-convex bow-tie ordering, `area_squared` mismatch vs. `kq_<qid>`, internal label leak, unverified `closure_certificate`, wrong producer/version, or category mixing) fails closed with `PREVIEW_RESULT_INVALID` (`envelope["ok"] == False`, `envelope["scene3d"] is None`).
4. **Learner-Facing Presentation (`function_route.py`)**:
   - `_an_dinh_thiet_dien_phu` collects `translate_point` results (`ket_qua_tinh_tien`) from `MAT_SONG_SONG` / `MAT_VUONG_DUONG` auxiliary plane decompositions and skips them when resolving coincident point names for unnamed section vertices (`point:on:...`), preventing internal construction labels (`H`, `H1`) from leaking into learner-facing section names (`Thiết diện (M)` instead of `Thiết diện (MH1)` when $H_1$ coincides with a section cut vertex).
5. **Architecture & Safety Rules**:
   - Zero hardcoded case IDs, vertex labels, or expected answers in product code.
   - `REGISTRY_VERSION = "geometry-functions/17"`, `PLANNER_VERSION = "geometry-fact-planner/16"`, `ENGINE_VERSION = "geometry-function-engine/14"`, `ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"`, `CACHE_VERSION = 130` (`NO_BUMP`), and `DEFAULT_MODE = LLM_ONLY` are unchanged.
   - `0` live provider calls (`ALLOW_LIVE_AI = 0`).
6. **Evidence & Oracle Independence**:
   - `tools/oracle_adapter4.py` computes 3D plane-polyhedron intersections from first principles using pure `Fraction` arithmetic without importing `app.simulation` or `app.ai`.

## 3. Findings by Severity

### BLOCKER
- None (`0`).

### MAJOR
- None (`0`).

### MINOR
- None (`0`).

### NIT (Resolved in `f54c3561`)
1. **`NIT-1` — Direct `result is None` call to `_validate_sections` & sub-field binding of `plane_relation` (`adapter4_route.py`) — RESOLVED in `f54c3561`**:
   - `_validate_engine_derived_section` now requires `result is not None` at the top (`if result is None: return "PREVIEW_RESULT_INVALID:section_missing_route_result"`) and explicitly verifies `rel.get("kind")` (`"parallel_plane"`, `"two_lines"`, `"perpendicular_line"`) and its target sub-fields (`parallel_to`, `lines`, `perpendicular_to`) against the verified `planner["auxiliary"]` record `dan`.
2. **`NIT-2` — Illustrative JSON key in `architecture-decision.md` — RESOLVED in `f54c3561`**:
   - Updated the illustrative JSON snippet in `architecture-decision.md` (`L40`) from `"line": ["A", "B"]` to `"perpendicular_to": ["A", "B"]` to match the exact runtime key emitted by `planner.py` (`L2024`).

## 4. Final Verdict

- **`ADAPTER_INTEGRATION_GAP` Status:** **CLOSED** for verified plane-only derived sections (`MAT_VUONG_DUONG`, `MAT_SONG_SONG`, `MAT_HAI_DUONG`) under Category B (`plane-section-certificate/1`). All `18/18` positive cases and `18/18` negative/tamper cases pass (`36/36` in `results/green-after.json`), and all `39/39` unit/tamper tests in `test_adapter4_plane_section_certificate.py` pass.
- **Final Verdict:** **`INDEPENDENT_REVIEW_PASS`** (`PASS`).
