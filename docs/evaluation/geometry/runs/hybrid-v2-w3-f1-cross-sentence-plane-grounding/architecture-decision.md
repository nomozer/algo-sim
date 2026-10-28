# Architecture Decision — Grounded Cross-Sentence Plane Reference Resolution (`W3-F1`)

## 1. Design Goal

Enable **Grounded Cross-Sentence Plane Reference Resolution** so that a plane `(P)` defined in one sentence of `problem_text` and referenced in a subsequent sentence (single or compound question: `section_only`, `area_only`, or `section_and_area`, across Category A and Category B) is accepted **if and only if** the reference resolves uniquely and without contradiction to a verified plane definition in `problem_text`, while preserving two-source provenance (`Definition evidence` + `Question evidence`) and keeping all locked JSON schemas (`TypedFact` and `typed-fact-next/2`) 100% unchanged.

---

## 2. Seven-Stage Verification Pipeline (`registry.py`, `typed_fact_next_bridge.py`, `planner.py`)

### Stage 1 — Closed Plane-Definition Grammar (`registry.py`)
Extend the closed plane-definition patterns to cover standalone cross-sentence Vietnamese definitions without introducing open-ended wildcards:
- Define `_NOI_QUAN_HE_MAT = r"\s*,?\s*(?:(?:và(?:\s+đồng\s+thời)?|đồng\s+thời)\s+)?"` to connect `through_point` and the geometric relation (`song song` / `vuông góc`) in `_QUA_SONG_SONG`, `_QUA_VUONG_DUONG`, `_QUA_HAI_DUONG`, and `_DIEM_TRUOC`.
- Extend `_QUA_HAI_DUONG` (and add point-first `_DIEM_TRUOC_HAI_DUONG`) to accept `(?:(?:cả\s+)?(?:hai|các)\s+(?:đường thẳng|cạnh)(?:\s+bên)?\s+)?`.
- Extend `_CUM_DUNG_MAT_PHU` and `_NOI_TIEN_DE` to include the closed premise introducers `thiết\s+lập`, `xét`, and `kẻ`.

### Stage 2 — Two-Source Provenance Preservation (`typed_fact_next_bridge.py` & `registry.py`)
No synthetic or concatenated quotes are ever created:
- In `TypedFact`, `quotes: list[str]` already stores an ordered list of exact source substrings verified against `problem_text` via `_vi_tri(de, q)`.
- When `derived_sections[0].quote` quotes the definition sentence and `simulation_goals` / `math_goals` quotes the question sentence, `bridge_v2` and `planner.py` preserve both exact substrings `[def_quote, req_quote]` in `c.quotes`.
- When `derived_sections[0].quote` in `typed-fact-next/2` points to the **question sentence** (or when `c.quotes` in `mat_song_song_dung_nguon` contains only the question sentence referencing `({ten})`), `bridge_v2` and `mat_song_song_dung_nguon` resolve `({ten})` to its unique declarative definition sentence in `de` (`problem_text`) and preserve both exact source spans:
  1. **Definition evidence:** the exact plane-definition sentence/span in `de`.
  2. **Question evidence:** the exact question sentence/span in `de`.
  The resolved definition span is recorded in `buoc` so `_kiem_vung_tien_de` and `_kiem_du_kien_cau_hoi` verify and cover the definition sentence in `de` without requiring any schema change to `typed-fact-next/2` or `TypedFact`.

### Stage 3 — Uniqueness & Non-Contradiction of Plane Symbol Binding (`mat_song_song_dung_nguon`)
A cross-sentence plane reference `({ten})` is bound to a definition `m` in `de` **only if**:
1. The question quote in `c.quotes` explicitly names `({ten})` in a closed section-reference pattern (`_DAN_THIET_DIEN` + `({ten})` or `({ten}) cắt ... theo thiết diện`) whose solid matches `c.args.solid` (`_cum_goi_khoi`). Pronoun-only plane references (`"mặt phẳng đó"`, `"mặt phẳng này"`, `"mặt phẳng trên"`) never match `({ten})` and are refused (`SOURCE_OBJECT_MISMATCH`).
2. `m` in `de` matches `cac_mau` for the call's relation (`parallel_plane`, `perpendicular_line`, or `parallel_two_lines`), `m["diem"] == p`, and `khop(m)` holds.
3. `m` passes `vai_tro_ok(de, m.start(), m[0])` (raising `NEGATED_CLAUSE`, `CONDITIONAL_CLAUSE`, or `GOAL_CLAUSE_NOT_PREMISE` if the definition sentence is negated, conditional, or a proof goal) and `_het_dinh_nghia(de, cuoi, m, cut, doc_cat)`.
4. Across the entire `de`, there is **no** conflicting plane definition for `ten` across all plane-definition patterns, **no** second distinct definition sentence for `ten`, and **every** occurrence of `({ten})` in `de` lies inside a validated definition span, validated cut-clause restatement, validated derived-pyramid phrase, or validated section-reference span of `ten`.

### Stage 4 — Cross-Solid Isolation (`_khoi_trong_quote` & Operand Solid Membership)
1. In `_khoi_trong_quote(c, khoi)`: reject if `ky_hieu` in `c.quotes` (or in the resolved plane-definition sentence in `de`) contains any declared solid symbol in `khoi` other than `c.args.solid`.
2. In `mat_song_song_dung_nguon`: verify that the through-point `p` and every reference label in `q` / `duong` / `hai_duong` belong to `c.args.solid` (its vertices or points constructed on `c.args.solid`), never to an unrelated second solid declared in `calls`.

### Stage 5 — Consistent `plane_name` (`ten_khai`) Enforcement Across All Three Relations
1. `typed_fact_next_bridge.py` (`_mat_fact`): include `"plane_name": sec.plane_name` for all three plane relations (`parallel`, `perpendicular`, `parallel_two_lines`).
2. `planner.py` (`_mat_qua_diem`, `_mat_vuong_duong`): include `f.plane_name` in `khoa` and `d` / `dd` whenever `f.plane_name is not None`.
3. `registry.py` (`_kiem_mat_song_song`, `_kiem_mat_vuong_duong`, `mat_song_song_dung_nguon`): pass `ten_khai=d.get("plane_name")` for all three rules (`MAT_SONG_SONG`, `MAT_VUONG_DUONG`, `MAT_HAI_DUONG`) and enforce `m["ten"] == ten_khai` whenever the plane is named (or `ten_khai != "α"` on an inline unnamed plane).

### Stage 6 — Request-Region Boundary Preservation Across Intermediate Sentences (`_kiem_du_kien_cau_hoi`)
In `_kiem_du_kien_cau_hoi` (line 2222 of `registry.py`), when a derived-plane `section` call (`c.id in phu`) has quotes `[q_def, q_req]`, a quote `q_def` whose sentence in `de` is a declarative plane definition with no `request_verb` and no `_HOI_SAU` does **not** pull `first_request` backward when another quote or sentence carries the request. Consequently, all intermediate premise sentences between `q_def` and `q_req` remain in `de[:first_request]` and are verified by `_kiem_vung_tien_de`.

### Stage 7 — Unasked Section Area Rejection (`planner.py` `_cau_hoi`)
In `_cau_hoi` (`planner.py`), when `n == "area"` and `f.plane_relation` is set with `role == "question"` and `not f.negated`, if `not hoi_td` (the quote does not ask for the section's area), raise `NOT_ASKED_IN_SOURCE` (when `"diện tích"` does not appear in `q`) or `SOURCE_OBJECT_MISMATCH` (when `"diện tích"` in `q` names a different object), rather than `UNSUPPORTED_CAPABILITY`.

---

## 3. Version & Cache Impact Assessment (Owner GO §11)

1. **`REGISTRY_VERSION`: bump `"geometry-functions/19"` -> `"geometry-functions/20"`**
   - Justified because Source Gate (`registry.py`) language & cross-sentence plane reference grounding semantics are updated.
2. **`PLANNER_VERSION`: bump `"geometry-fact-planner/17"` -> `"geometry-fact-planner/18"`**
   - Justified because `planner.py` (`_mat_qua_diem`, `_mat_vuong_duong`, `_cau_hoi`) propagates `plane_name` across all three plane relations and classifies unasked section-area goals under `NOT_ASKED_IN_SOURCE` / `SOURCE_OBJECT_MISMATCH`.
3. **Preview Fixture Identity Delta (`backend/scripts/export_hybrid_preview_fixtures.py`):**
   - Register `{"run": "hybrid-v2-w3-f1-cross-sentence-plane-grounding", "versions": {"registry_version": ("geometry-functions/19", "geometry-functions/20"), "planner_version": ("geometry-fact-planner/17", "geometry-fact-planner/18")}}` in `IDENTITY_DELTAS`.
4. **Locked Schemas (`TypedFact` and `typed-fact-next/2`):**
   - Unchanged (`LOCKED_TYPED_FACT_SCHEMA_SHA256` and `typed-fact-next/2` JSON schema remain byte-for-byte identical).
5. **`CACHE_VERSION = "130"` and `DEFAULT_MODE = "LLM_ONLY"`:**
   - Unchanged. The product cache (`SimulationCache`) is used only by `/api/analyze` (`RoutePolicy` with `hybrid_preview_enabled=False`); Route D explicitly forbids product cache access (`if route_policy.hybrid_preview_enabled: raise ValueError("Route D preview must never use the product cache")`), and non-default `geometry_compiler_mode` hashes `dinh_danh_be_mat` into `policy_version`. `semantic_environment_fingerprint()` is completely unchanged.
